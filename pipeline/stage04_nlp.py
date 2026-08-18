"""
stage04_nlp.py ΓÇö Change 1 & 2 surgical additions:
  ΓÇó _extract_product_and_region(): lightweight keyword/gazetteer extraction
    EXTRACTION_QUALITY_FLAG: Twitter data gives ~12% product / ~2.5% region coverage.
    Replace this function with a real NER model for production-quality clustering.
  ΓÇó _compute_trajectory(): per-thread CSAT trajectory from sequential turn-level sentiment
  ΓÇó Both are attached to c["nlp"] in _process_conv() before Parquet write.
"""
import os
import statistics
from typing import Dict, List, Optional

from pipeline.config_loader import load_config
from pipeline.nlp_engine import NLPProvider
from pipeline.logger import get_logger
from pipeline.nlp_engine import LocalNLPProvider, ExternalNLPProviderAdapter, TransformerNLPProvider
from pipeline.schemas import NLPResult, NLPSeverity, SentimentTrajectory
from pipeline.storage import StorageEngine

logger = get_logger("Stage04_NLP")

# ΓöÇΓöÇ Configurable escalation drop threshold (Change 2) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
_ESC_THRESHOLD = float(os.environ.get("TRAJECTORY_ESCALATION_THRESHOLD", "0.2"))

# ΓöÇΓöÇ Product gazetteer (Change 1) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# EXTRACTION_QUALITY_FLAG: these keywords map raw text tokens to canonical product
# names. Coverage on Twitter data is low (~12%). Extend or replace with NER.
_PRODUCT_KEYWORDS: Dict[str, List[str]] = {
    "broadband":  ["broadband", "fibre", "fiber", "dsl"],
    "wifi":       ["wifi", "wi-fi", "wireless"],
    "internet":   ["internet", "net connection", "connection"],
    "sim":        ["sim card", "sim", "esim"],
    "app":        ["app", "application", "mobile app"],
    "phone":      ["phone", "handset", "mobile", "smartphone"],
    "flight":     ["flight", "airline", "air ticket"],
    "ticket":     ["ticket", "booking", "reservation"],
    "router":     ["router", "modem", "hub"],
    "line":       ["line", "landline", "telephone line"],
    "tv":         ["tv", "television", "cable", "satellite"],
    "streaming":  ["streaming", "video", "netflix", "disney"],
    "account":    ["account", "profile", "login"],
    "payment":    ["payment", "card", "charge", "fee", "bill", "invoice", "direct debit", "subscription", "plan"],
    "device":     ["device", "hardware", "screen", "battery"],
}

# ΓöÇΓöÇ Region gazetteer (Change 1) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# EXTRACTION_QUALITY_FLAG: ~2.5% region coverage on Twitter. Extend as needed.
_REGION_KEYWORDS: Dict[str, List[str]] = {
    "london":     ["london", "uk", "england", "britain"],
    "manchester": ["manchester"],
    "birmingham": ["birmingham"],
    "glasgow":    ["glasgow", "scotland"],
    "chennai":    ["chennai", "madras", "anna nagar"],
    "mumbai":     ["mumbai", "bombay"],
    "delhi":      ["delhi", "new delhi"],
    "bangalore":  ["bangalore", "bengaluru"],
    "hyderabad":  ["hyderabad"],
    "new_york":   ["new york", "nyc"],
    "california": ["california", "ca", "los angeles", "san francisco"],
    "texas":      ["texas", "tx", "houston", "dallas"],
    "store":      ["in store", "at store", "store location", "branch"],
}

# Subtype taxonomy is now loaded dynamically from config.yaml


def _extract_subtype(text: str, subtype_taxonomy: dict = None):
    clean = text.lower()
    import re
    subtype = "general"
    if subtype_taxonomy:
        for sub_name, keywords in subtype_taxonomy.items():
            pattern = re.compile(r'(?:' + '|'.join(kw for kw in keywords) + r')', re.IGNORECASE)
            if pattern.search(clean):
                subtype = sub_name
                break
    return subtype

_SPACY_MODEL = None

def _extract_region_spacy_batch(texts: List[str], guard_words: set) -> List[str]:
    global _SPACY_MODEL
    if _SPACY_MODEL is None:
        try:
            import spacy
            spacy.prefer_gpu()
            try:
                _SPACY_MODEL = spacy.load("en_core_web_trf")
            except Exception as trf_err:
                logger.warning(f"spaCy TRF not available: {trf_err}. Trying en_core_web_sm fallback...")
                _SPACY_MODEL = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"spaCy model loading failed: {e}")
            _SPACY_MODEL = False
            
    if not _SPACY_MODEL:
        return ["unspecified"] * len(texts)
        
    results = []
    for doc in _SPACY_MODEL.pipe(texts, batch_size=8):
        found = "unspecified"
        for ent in doc.ents:
            if ent.label_ == "GPE":
                clean_ent = ent.text.strip().lower()
                if clean_ent and clean_ent not in guard_words:
                    found = ent.text.strip()
                    break
        results.append(found)
    return results


def _compute_trajectory(turns: List[Dict], nlp_provider: LocalNLPProvider) -> Dict:
    """
    Compute CSAT sentiment trajectory from ordered customer turns.
    Returns a SentimentTrajectory-compatible dict.

    Fields produced:
      turn_sentiments  ΓÇö sentiment score per customer turn (in order)
      start_sentiment  ΓÇö first customer turn sentiment
      end_sentiment    ΓÇö last customer turn sentiment
      delta            ΓÇö end ΓêÆ start
      escalation_flag  ΓÇö True if any consecutive drop > _ESC_THRESHOLD
      recovery_flag    ΓÇö True if sentiment improved after a negative dip
      volatility       ΓÇö population stddev of turn_sentiments
      csat_proxy_score ΓÇö linear rescale of end_sentiment from [-1,1] to [1,5]
    """
    cust_turns = [
        t for t in turns
        if t.get("role") == "customer" or t.get("inbound", True)
    ]

    if not cust_turns:
        traj = SentimentTrajectory()
        return traj.model_dump()

    turn_sentiments: List[float] = []
    for turn in cust_turns:
        text = turn.get("text") or turn.get("raw") or ""
        if text:
            res = nlp_provider.analyze_text(text)
            turn_sentiments.append(res.sentiment)
        else:
            turn_sentiments.append(0.0)

    start_sentiment = turn_sentiments[0]
    end_sentiment = turn_sentiments[-1]
    delta = round(end_sentiment - start_sentiment, 4)

    # escalation_flag: any consecutive drop greater than threshold
    escalation_flag = False
    had_dip = False
    recovery_flag = False
    prev = start_sentiment
    for i, s in enumerate(turn_sentiments[1:], 1):
        drop = prev - s
        if drop > _ESC_THRESHOLD:
            escalation_flag = True
            had_dip = True
        if had_dip and s > prev:
            recovery_flag = True
        prev = s

    volatility = round(statistics.pstdev(turn_sentiments) if len(turn_sentiments) > 1 else 0.0, 4)

    # csat_proxy_score: linear rescale end_sentiment [-1,1] ΓåÆ [1,5]
    csat_proxy_score = round(1.0 + (end_sentiment + 1.0) * 2.0, 3)
    csat_proxy_score = max(1.0, min(5.0, csat_proxy_score))

    traj = SentimentTrajectory(
        turn_sentiments=turn_sentiments,
        start_sentiment=round(start_sentiment, 4),
        end_sentiment=round(end_sentiment, 4),
        delta=delta,
        escalation_flag=escalation_flag,
        recovery_flag=recovery_flag,
        volatility=volatility,
        csat_proxy_score=csat_proxy_score,
    )
    return traj.model_dump()


def enrich_with_nlp(
    conversations: Optional[List[Dict]] = None,
    config: Optional[Dict] = None,
    external_json_payloads: Optional[List[Dict]] = None,
) -> List[Dict]:
    cfg = config or load_config()
    storage = StorageEngine(cfg)
    nlp_cfg = cfg.get("nlp", {})
    # NLP_PROVIDER env var takes precedence, then config, then default to 'transformer'
    provider_type = os.environ.get("NLP_PROVIDER") or nlp_cfg.get("default_provider", "transformer")
    taxonomy = nlp_cfg.get("taxonomy")
    subtype_taxonomy = nlp_cfg.get("subtype_taxonomy", {})

    logger.info(
        f"Enriching conversations using NLPProvider '{provider_type}' "
        f"in streaming batches (+ product/region extraction, trajectory, "
        f"esc_threshold={_ESC_THRESHOLD})..."
    )

    local_provider = LocalNLPProvider(taxonomy=taxonomy)

    # ΓöÇΓöÇ Select the active NLP provider ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    if provider_type == "transformer":
        active_provider = TransformerNLPProvider(taxonomy=taxonomy)
        # If transformer init failed (no models), fall back to local
        if not active_provider._available:
            logger.warning(
                "[Stage04] TransformerNLPProvider unavailable ΓÇö falling back to LocalNLPProvider."
            )
            active_provider = local_provider
    else:
        active_provider = local_provider

    external_adapter = ExternalNLPProviderAdapter(fallback_provider=local_provider)

    ext_map = {}
    if external_json_payloads:
        for ext in external_json_payloads:
            cid = ext.get("case_id") or ext.get("conversation_id")
            if cid:
                ext_map[cid] = ext

    import yaml
    company_product_map = {}
    map_path = "config/company_product_map.yaml"
    if os.path.exists(map_path):
        with open(map_path, "r") as f:
            company_product_map = yaml.safe_load(f) or {}
            
    guard_words = set()
    for k, v in company_product_map.items():
        guard_words.add(str(k).lower())
        guard_words.add(str(v).lower())

    total_enriched = 0
    total_product_found = 0
    total_region_found = 0
    enriched_sample_return: List[Dict] = []

    def _conv_batch_generator():
        if conversations:
            for i in range(0, len(conversations), 50000):
                yield conversations[i : i + 50000]
        else:
            for batch in storage.read_parquet_batches(
                "conversations.parquet", subfolder="conversations", batch_size=50000
            ):
                yield batch

    from concurrent.futures import ThreadPoolExecutor

    def _process_conv_no_region(c):
        conv_id = c.get("conversation_id")
        turns = c.get("turns") or []
        cust_turns = [t for t in turns if t.get("role") == "customer" or t.get("inbound", True)]
        cust_text = (
            cust_turns[0]["text"]
            if cust_turns
            else (turns[0]["text"] if turns else "No content")
        )

        # ΓöÇΓöÇ Core NLP ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        if conv_id in ext_map:
            nlp_res = external_adapter.analyze_json(ext_map[conv_id], raw_text=cust_text)
        else:
            nlp_res = active_provider.analyze_text(cust_text, case_id=conv_id, conversation_id=conv_id)

        nlp_dict = nlp_res.model_dump()

        full_text = " ".join(t.get("text") or "" for t in turns)
        
        company_handle = c.get("company_handle")
        product = company_product_map.get(company_handle, company_handle or "unspecified")
        
        subtype = _extract_subtype(full_text or cust_text, subtype_taxonomy)
        
        nlp_dict["product"] = product
        nlp_dict["subtype"] = subtype
        c["product"] = product
        c["subtype"] = subtype
        
        nlp_dict["_full_text"] = full_text or cust_text
        nlp_dict["trajectory"] = _compute_trajectory(turns, local_provider)

        c["nlp"] = nlp_dict
        return nlp_dict

    def _nlp_chunk_generator():
        nonlocal total_enriched, total_product_found, total_region_found
        with ThreadPoolExecutor(max_workers=8) as executor:
            for batch in _conv_batch_generator():
                chunk_nlp_results = list(executor.map(_process_conv_no_region, batch, chunksize=1000))
                
                texts = [res.pop("_full_text") for res in chunk_nlp_results]
                regions = _extract_region_spacy_batch(texts, guard_words)
                
                for i, res in enumerate(chunk_nlp_results):
                    region = regions[i]
                    res["region"] = region
                    batch[i]["region"] = region
                    batch[i]["nlp"]["region"] = region
                    
                    if res.get("product") not in ("unknown", "unspecified"):
                        total_product_found += 1
                    if region not in ("unknown", "unspecified"):
                        total_region_found += 1
                        
                total_enriched += len(chunk_nlp_results)

                if conversations and len(enriched_sample_return) < 50000:
                    enriched_sample_return.extend(batch)

                yield chunk_nlp_results

    storage.write_parquet_chunks(_nlp_chunk_generator(), "nlp_results.parquet", subfolder="nlp")
    storage.checkpoint_mgr.save_checkpoint("stage04_nlp", {"count": total_enriched})

    prod_pct = round(total_product_found / max(total_enriched, 1) * 100, 2)
    reg_pct = round(total_region_found / max(total_enriched, 1) * 100, 2)

    logger.info(
        f"[STAGE 4 NLP] Successfully enriched all {total_enriched:,} conversations. "
        f"Product coverage: {prod_pct}% | Region coverage: {reg_pct}%"
    )
    return enriched_sample_return if conversations else None


# ΓöÇΓöÇ Backward compatibility helpers ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Module-level singleton avoids re-constructing the NLP provider on every call.
# Uses TransformerNLPProvider by default; falls back to LocalNLPProvider.
_NLP_SINGLETON: Optional[NLPProvider] = None


def _get_nlp() -> NLPProvider:
    """Return the process-wide NLP provider singleton (lazy init)."""
    global _NLP_SINGLETON
    if _NLP_SINGLETON is None:
        provider_type = os.environ.get("NLP_PROVIDER", "transformer")
        if provider_type == "transformer":
            p = TransformerNLPProvider()
            _NLP_SINGLETON = p if p._available else LocalNLPProvider()
        else:
            _NLP_SINGLETON = LocalNLPProvider()
    return _NLP_SINGLETON


def classify_intent(text: str) -> str:
    return _get_nlp().analyze_text(text).intent


def score_sentiment(text: str) -> float:
    return _get_nlp().analyze_text(text).sentiment


def extract_duration_days(text: str) -> Optional[int]:
    res = _get_nlp().analyze_text(text)
    for sig in res.temporal_signals:
        if "day" in sig.lower():
            nums = [int(s) for s in sig.split() if s.isdigit()]
            if nums:
                return nums[0]
    return None


def score_severity(intent: str, sentiment: float, duration_days: Optional[int]) -> str:
    res = _get_nlp().analyze_text(f"{intent} issue lasting {duration_days or 1} days")
    return res.severity.label


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    from stage03_conversations import build_conversations

    convs = enrich_with_nlp(build_conversations(clean_batch(generate_raw_complaints(5))))
    for c in convs:
        nlp = c["nlp"]
        traj = nlp.get("trajectory") or {}
        print(
            c["conversation_id"],
            "->",
            nlp["category"],
            "| product:", nlp["product"],
            "| region:", nlp["region"],
            "| delta:", traj.get("delta"),
            "| esc:", traj.get("escalation_flag"),
            "| csat:", traj.get("csat_proxy_score"),
        )
