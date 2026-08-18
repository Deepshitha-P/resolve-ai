"""Check 4 — Pain score and escalation rate: pull from aggregation layers directly"""
import pandas as pd, json, os

# Analytics v2 metrics
metrics_path = "data/analytics_v2/metrics_summary.json"
if os.path.exists(metrics_path):
    with open(metrics_path) as f:
        m = json.load(f)
    print("=== metrics_summary.json top-level keys:", list(m.keys()))
    # Pain score source
    for k in ["pain_score", "csat_proxy", "escalation_metrics", "product_analysis", "category_analysis", "cluster_analysis"]:
        if k in m:
            print(f"\n  [{k}]:", json.dumps(m[k], indent=2)[:1500])

# Parquet aggregations
for pname, ppath in [
    ("product_metrics", "data/analytics_v2/product_metrics.parquet"),
    ("category_metrics", "data/analytics_v2/category_metrics.parquet"),
    ("csat_trajectory",  "data/analytics_v2/csat_trajectory.parquet"),
]:
    if os.path.exists(ppath):
        df = pd.read_parquet(ppath)
        print(f"\n=== {pname} columns: {list(df.columns)}")
        print(df.to_string(max_rows=30))

# Check analytics summary parquet
ap = "data/analytics/analytics_summary.parquet"
if os.path.exists(ap):
    adf = pd.read_parquet(ap)
    print(f"\n=== analytics_summary.parquet columns: {list(adf.columns)}")
    for col in ["pain_score", "escalation_rate", "product", "cluster_id", "label"]:
        if col in adf.columns:
            print(f"\n  {col} distribution:")
            print(adf[col].value_counts(dropna=False).head(20).to_string())
    if "pain_score" in adf.columns and "escalation_rate" in adf.columns:
        print("\n  Rows with pain_score + escalation_rate (first 20):")
        print(adf[["pain_score","escalation_rate"] + [c for c in ["product","label","cluster_id"] if c in adf.columns]].head(20).to_string())

# Check issue_clusters for numeric scores
cluster_path = "data/knowledge/issue_clusters/issue_clusters.parquet"
if os.path.exists(cluster_path):
    cl = pd.read_parquet(cluster_path)
    score_cols = [c for c in cl.columns if any(k in c.lower() for k in ["pain","score","escalat","csat","rate","priority"])]
    print(f"\n=== issue_clusters score columns: {score_cols}")
    if score_cols:
        print(cl[score_cols + [c for c in ["doc_id","document_id","label","title"] if c in cl.columns]].to_string(max_rows=30))
