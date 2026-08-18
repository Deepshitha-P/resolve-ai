"""
llm_provider.py

Single-LLM Provider Architecture for RootIQ RAG.

One LLM handles both chunking guidance and insight generation.
Reads from a single set of LLM_* env vars in .env.

Supported providers (via LLM_PROVIDER):
  openrouter  ΓÇö OpenRouter.ai (best free models: deepseek, gemini-flash, kimi)
  anthropic   ΓÇö Claude family
  openai      ΓÇö GPT family
  gemini      ΓÇö Google Gemini
  local       ΓÇö Offline template fallback (no API key required)

Best free model (set in .env):
  LLM_MODEL=deepseek/deepseek-chat:free   (DeepSeek V3 via OpenRouter ΓÇö free tier)
"""

from abc import ABC, abstractmethod
import os
import json
import urllib.request
import urllib.error
from typing import Optional

# ΓöÇΓöÇ Load .env at import time ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass

from pipeline.logger import get_logger

logger = get_logger("LLMProvider")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Abstract Base
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class LLMProvider(ABC):
    """Abstract Base Class for LLM Inference Providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Local / Offline Fallback
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class LocalLLMProvider(LLMProvider):
    """
    Offline fallback ΓÇö returns the prompt unchanged as a grounded template.
    No API key required. Always available.
    """
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        logger.info("LocalLLMProvider: using offline grounded template (offline mode / fallback).")
        return ""


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Cloud LLM (OpenRouter / Anthropic / OpenAI / Gemini)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class CloudLLMProvider(LLMProvider):
    """
    Cloud LLM provider. Supports OpenRouter, Anthropic, OpenAI, and Gemini.
    Falls back to LocalLLMProvider on errors or missing API key.

    OpenRouter is recommended ΓÇö gives access to DeepSeek V3, Kimi K2,
    Gemini Flash, and many other models on a free tier with one API key.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: int = 8,   # hard cap: keep RAG queries under 10s total
        fallback_provider: Optional[LLMProvider] = None,
    ):
        self.provider = (provider or os.environ.get("LLM_PROVIDER") or "openrouter").lower()
        self.model = model or os.environ.get("LLM_MODEL") or "deepseek/deepseek-chat:free"
        self.api_key = (
            api_key
            or os.environ.get("LLM_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        self.api_base = api_base or os.environ.get("LLM_API_BASE")
        self.timeout = timeout
        self.fallback_provider = fallback_provider or LocalLLMProvider()

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key or self.api_key.startswith("your-"):
            logger.warning(
                "CloudLLMProvider: No API key set. "
                "Add LLM_API_KEY=your-key to .env. Falling back to offline template."
            )
            return self.fallback_provider.generate(prompt, system_prompt)

        import time
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if "openrouter" in self.provider:
                    return self._call_openrouter(prompt, system_prompt)
                elif "anthropic" in self.provider or "claude" in self.model:
                    return self._call_anthropic(prompt, system_prompt)
                elif "gemini" in self.provider:
                    return self._call_gemini(prompt, system_prompt)
                else:
                    # openai or generic OpenAI-compatible
                    return self._call_openai_compatible(prompt, system_prompt)
    
            except urllib.error.HTTPError as e:
                if e.code in (429, 503):
                    if attempt < max_retries - 1:
                        sleep_time = 5 * (attempt + 1)
                        logger.warning(f"CloudLLMProvider HTTPError ({e.code}). Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue
                logger.warning(f"CloudLLMProvider HTTPError ({e.code}): {e.reason}. Using offline fallback.")
                return self.fallback_provider.generate(prompt, system_prompt)
            except urllib.error.URLError as e:
                logger.warning(f"CloudLLMProvider URLError: {e.reason}. Using offline fallback.")
                return self.fallback_provider.generate(prompt, system_prompt)
            except Exception as e:
                logger.warning(f"CloudLLMProvider error ({type(e).__name__}): {e}. Using offline fallback.")
                return self.fallback_provider.generate(prompt, system_prompt)

    # ΓöÇΓöÇ Provider call methods ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def _call_openrouter(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """OpenRouter ΓÇö OpenAI-compatible, supports DeepSeek/Kimi/Gemini/etc. free models."""
        url = self.api_base or "https://openrouter.ai/api/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "max_tokens": 2048}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/rootiq-rag",
                "X-Title": "RootIQ RAG",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = self.api_base or "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return "".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")

    def _call_openai_compatible(
        self, prompt: str, system_prompt: Optional[str] = None, url: Optional[str] = None
    ) -> str:
        url = url or self.api_base or "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "max_tokens": 2048}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _call_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        full_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {"contents": [{"parts": [{"text": full_text}]}]}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Factory Functions ΓÇö single LLM for all roles
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def get_llm_provider(
    provider_type: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMProvider:
    """
    Returns the configured LLM provider (single model for all pipeline roles).
    Reads LLM_PROVIDER / LLM_MODEL / LLM_API_KEY from .env.

    When USE_REAL_LLM=false (default) always returns LocalLLMProvider so that
    no network call is attempted even when an API key is present.

    Default: OpenRouter + deepseek/deepseek-chat:free (best free model).
    Falls back to LocalLLMProvider if no API key is set.
    """
    # Respect USE_REAL_LLM flag -- skip cloud entirely in offline mode
    use_real = os.environ.get("USE_REAL_LLM", "false").lower() in ("true", "1", "yes")
    if not use_real:
        logger.info("LLM: USE_REAL_LLM=false -- using LocalLLMProvider (offline template).")
        return LocalLLMProvider()

    p_type = (provider_type or os.environ.get("LLM_PROVIDER") or "openrouter").lower()
    m = model or os.environ.get("LLM_MODEL") or "deepseek/deepseek-chat:free"
    k = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")

    if not k or k.startswith("your-"):
        logger.info(f"LLM: No API key -- using LocalLLMProvider (offline template).")
        return LocalLLMProvider()

    logger.info(f"LLM: provider={p_type}, model={m}")
    return CloudLLMProvider(provider=p_type, model=m, api_key=k, timeout=15)


# Both roles now use the same single provider ΓÇö no dual-key split
get_chunking_llm_provider = get_llm_provider
get_generation_llm_provider = get_llm_provider
