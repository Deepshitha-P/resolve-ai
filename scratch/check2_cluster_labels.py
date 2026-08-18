"""Check 2 — Cluster labeling: pull raw docs from DOC-CLUSTER-41, DOC-CLUSTER-141, DOC-CLUSTER-34"""
import pandas as pd, json, os

cluster_path = "data/knowledge/issue_clusters/issue_clusters.parquet"
if not os.path.exists(cluster_path):
    print("MISSING:", cluster_path)
    exit()

cl = pd.read_parquet(cluster_path)
print("=== CLUSTER PARQUET columns:", list(cl.columns))
print("=== Total clusters:", len(cl))
print()

targets = ["DOC-CLUSTER-41", "DOC-CLUSTER-141", "DOC-CLUSTER-34"]
for t in targets:
    row = cl[cl.apply(lambda r: t in str(r.get("doc_id","")) or t in str(r.get("document_id","")), axis=1)]
    if len(row) == 0:
        # try numeric id
        cid = int(t.split("-")[-1])
        row = cl[cl.get("cluster_id", pd.Series(dtype=int)) == cid] if "cluster_id" in cl.columns else pd.DataFrame()
    print(f"--- {t} ---")
    if len(row):
        r = row.iloc[0]
        for k in ["doc_id","document_id","cluster_id","label","title","text","excerpt","snippet","representative_text","size","member_count","product","category"]:
            if k in r.index:
                val = r[k]
                print(f"  {k}: {str(val)[:400]}")
    else:
        print("  NOT FOUND by ID — trying fuzzy label match")
    print()

# Also show full label distribution
if "label" in cl.columns:
    print("=== All cluster labels:")
    print(cl["label"].value_counts(dropna=False).to_string())
if "title" in cl.columns:
    print("\n=== All cluster titles (first 30):")
    for t in cl["title"].dropna().unique()[:30]:
        print(" ", t)
