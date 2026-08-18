"""Check 5 — Total cluster count and complaint volume"""
import pandas as pd, json, os

# Total clusters
cluster_path = "data/knowledge/issue_clusters/issue_clusters.parquet"
if os.path.exists(cluster_path):
    cl = pd.read_parquet(cluster_path)
    print(f"Total clusters in issue_clusters.parquet: {len(cl)}")
    size_cols = [c for c in cl.columns if any(k in c.lower() for k in ["size","count","volume","member","cases"])]
    print(f"  Size/count columns: {size_cols}")
    if size_cols:
        sc = size_cols[0]
        print(f"  Top 10 clusters by {sc}:")
        print(cl.nlargest(10, sc)[[c for c in ["doc_id","document_id","label","title",sc] if c in cl.columns]].to_string())
    print(f"\n  All column names: {list(cl.columns)}")

# Total conversations
for p in ["data/conversations/conversations.parquet", "data/knowledge/conversations/conversations.parquet"]:
    if os.path.exists(p):
        df = pd.read_parquet(p)
        print(f"\nTotal conversations in {p}: {len(df):,}")

# Raw CSV
raw = "data/raw/twcs_cleaned.csv"
if os.path.exists(raw):
    rc = sum(1 for _ in open(raw, encoding='utf-8', errors='ignore')) - 1
    print(f"\nTotal rows in twcs_cleaned.csv: {rc:,}")

# NLP results
nlp = "data/nlp/nlp_results.parquet"
if os.path.exists(nlp):
    ndf = pd.read_parquet(nlp)
    print(f"\nTotal rows in nlp_results.parquet: {len(ndf):,}")
    if "cluster_id" in ndf.columns:
        print(f"  Distinct cluster_ids: {ndf['cluster_id'].nunique()}")
    if "product" in ndf.columns:
        print(f"  Product distribution:\n{ndf['product'].value_counts(dropna=False).head(20).to_string()}")
