import os
from typing import Optional
import yaml

DEFAULT_CONFIG = {
    "dataset": {
        "raw_csv_path": "data/raw/twcs.csv",
        "source_type": "twcs_case",
        "default_sample_size": None,
    },
    "storage": {
        "base_dir": "data",
        "raw_dir": "data/raw",
        "parquet_dir": "data/parquet",
        "conversations_dir": "data/conversations",
        "nlp_dir": "data/nlp",
        "analytics_dir": "data/analytics",
        "knowledge_dir": "data/knowledge",
        "checkpoints_dir": "data/checkpoints",
        "chunk_size": 50000,
    },
    "nlp": {
        "default_provider": "local",
        "taxonomy": [
            "payment", "refund", "billing", "network", "service_outage",
            "account", "authentication", "delivery", "technical_support",
            "complaint_followup", "device_hardware", "travel_flight",
            "store_operations", "feature_request", "other"
        ],
    },
    "temporal": {
        "spike_z_threshold": 1.5,
        "min_spike_count": 5,
    },
    "clustering": {
        "n_clusters": 8,
        "max_sample_size": 10000,
    },
}

def load_config(config_path: Optional[str] = None) -> dict:
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "config.yaml")

    if not os.path.exists(config_path):
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            # Merge with default config
            merged = DEFAULT_CONFIG.copy()
            for k, v in cfg.items():
                if isinstance(v, dict) and k in merged:
                    merged[k].update(v)
                else:
                    merged[k] = v
            return merged
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}. Using defaults.")
        return DEFAULT_CONFIG
