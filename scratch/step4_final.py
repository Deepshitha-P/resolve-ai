import duckdb
con = duckdb.connect()

# Knowledge parquet has document_id like 'DOC-CONV-CONV-1', NLP has case_id like 'CONV-1'
# Join: k.document_id = 'DOC-CONV-' || n.case_id

print("---5 PRODUCT SAMPLES (product | clean_text)---")
rows = con.execute("""
    SELECT n.product, LEFT(k.content, 130)
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/knowledge/conversations/conversations.parquet' k
      ON k.document_id = 'DOC-CONV-' || n.case_id
    WHERE n.product != 'unknown'
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0]} | {r[1]}")

print("\n---5 REGION SAMPLES (region | clean_text)---")
rows = con.execute("""
    SELECT n.region, LEFT(k.content, 130)
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/knowledge/conversations/conversations.parquet' k
      ON k.document_id = 'DOC-CONV-' || n.case_id
    WHERE n.region != 'unknown'
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0]} | {r[1]}")
