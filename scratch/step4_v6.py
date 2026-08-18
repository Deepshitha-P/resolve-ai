import duckdb
con = duckdb.connect()

# Join NLP with knowledge conversations to get content text
print("---5 PRODUCT SAMPLES (product | clean_text)---")
rows = con.execute("""
    SELECT n.product, LEFT(k.content, 120)
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/knowledge/conversations/conversations.parquet' k
      ON 'conv_thread_' || REPLACE(n.case_id, 'CONV-', '') = k.document_id
    WHERE n.product != 'unknown'
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0]} | {r[1]}")

print("\n---5 REGION SAMPLES (region | clean_text)---")
rows = con.execute("""
    SELECT n.region, LEFT(k.content, 120)
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/knowledge/conversations/conversations.parquet' k
      ON 'conv_thread_' || REPLACE(n.case_id, 'CONV-', '') = k.document_id
    WHERE n.region != 'unknown'
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0]} | {r[1]}")
