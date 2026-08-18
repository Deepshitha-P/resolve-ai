"""Check 1 — Raw dataset product field distribution"""
import pandas as pd, json, os

# Raw source
raw_path = "data/raw/twcs_cleaned.csv"
if os.path.exists(raw_path):
    df = pd.read_csv(raw_path, nrows=5000)
    print("=== RAW CSV columns:", list(df.columns))
    for col in ["product", "product_service", "category", "company", "author_id", "inbound"]:
        if col in df.columns:
            print(f"\n  {col} top-20 values:")
            print(df[col].value_counts(dropna=False).head(20).to_string())

# Parquet conversations
parquet_path = "data/knowledge/conversations/conversations.parquet"
if os.path.exists(parquet_path):
    pq = pd.read_parquet(parquet_path)
    print("\n\n=== CONVERSATIONS PARQUET columns:", list(pq.columns))
    for col in ["product", "product_service", "category", "company"]:
        if col in pq.columns:
            print(f"\n  {col} top-20:")
            print(pq[col].value_counts(dropna=False).head(20).to_string())

# customer_cases
cc_path = "data/knowledge/customer_cases/customer_cases.parquet"
if os.path.exists(cc_path):
    cc = pd.read_parquet(cc_path)
    print("\n\n=== CUSTOMER_CASES PARQUET columns:", list(cc.columns))
    for col in ["product", "product_service", "category"]:
        if col in cc.columns:
            print(f"\n  {col} top-20:")
            print(cc[col].value_counts(dropna=False).head(20).to_string())

# NLP results
nlp_path = "data/nlp/nlp_results.parquet"
if os.path.exists(nlp_path):
    nlp = pd.read_parquet(nlp_path)
    print("\n\n=== NLP_RESULTS PARQUET columns:", list(nlp.columns))
    for col in ["product", "product_service", "category", "intent"]:
        if col in nlp.columns:
            print(f"\n  {col} top-20:")
            print(nlp[col].value_counts(dropna=False).head(20).to_string())
