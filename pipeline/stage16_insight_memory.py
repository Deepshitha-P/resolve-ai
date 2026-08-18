import json
import os
from typing import Any, Dict, List, Optional
from pipeline.config_loader import load_config
from pipeline.storage import StorageEngine


class InsightMemory:
    """
    Stage 16: Insight Memory.
    Persists generated grounded insights separately under data/knowledge/historical_insights/
    and outputs/insight_memory.json. Does NOT mix generated insights with raw customer cases.
    """
    def __init__(self, path: str = "outputs/insight_memory.json", config: Optional[Dict] = None):
        self.path = path
        self.config = config or load_config()
        self.storage = StorageEngine(self.config)
        self.records: List[Dict] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception:
                self.records = []

    def _signature(self, category: str, area: Optional[str] = None) -> str:
        return f"{category}::{area or 'any'}"

    def save(self, category: str, area: Optional[str], insight: Dict) -> Dict:
        doc_id = f"DOC-INSIGHT-{len(self.records)+1:04d}"
        record = {
            "document_id": doc_id,
            "doc_id": doc_id,
            "signature": self._signature(category, area),
            "category": category,
            "area": area,
            "insight": insight,
            "title": f"Grounded Insight for {category} ({area or 'global'})",
            "content": insight.get("insight_text") or str(insight.get("grounded_business_insight")),
            "type": "historical_insights",
            "document_type": "historical_insights",
            "metadata": {"category": category, "area": area, "layer": "historical_insights"},
        }
        self.records.append(record)

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2, default=str)

        # Persist out-of-core under data/knowledge/historical_insights/
        try:
            self.storage.write_parquet(self.records, "historical_insights.parquet", subfolder="knowledge/historical_insights")
        except Exception:
            pass

        return record

    def find_similar(self, category: str, area: Optional[str] = None) -> Optional[Dict]:
        sig = self._signature(category, area)
        matches = [r for r in self.records if r.get("signature") == sig]
        return matches[-1]["insight"] if matches else None
