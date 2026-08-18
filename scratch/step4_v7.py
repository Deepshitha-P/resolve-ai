import duckdb
con = duckdb.connect()
rows = con.execute("SELECT document_id, LEFT(content, 80) FROM 'data/knowledge/conversations/conversations.parquet' LIMIT 3").fetchall()
for r in rows:
    print(r)

# Also check NLP case_id format
rows2 = con.execute("SELECT case_id FROM 'data/nlp/nlp_results.parquet' LIMIT 3").fetchall()
print("NLP case_ids:", [r[0] for r in rows2])

# Get conversations parquet columns
cols = con.execute("DESCRIBE SELECT * FROM 'data/conversations/conversations.parquet'").fetchall()
print("Conv parquet columns:", [c[0] for c in cols])

# Try direct: get clean_text from conversations parquet with product from nlp  
rows3 = con.execute("""
    SELECT n.product, LEFT(c.clean_text, 120) as ct
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/conversations/conversations.parquet' c 
      ON n.conversation_id = c.conversation_id
    WHERE n.product != 'unknown'
    LIMIT 5
""").fetchall()
print("\n---PRODUCT SAMPLES---")
for r in rows3:
    print(f"  {r[0]} | {r[1]}")

rows4 = con.execute("""
    SELECT n.region, LEFT(c.clean_text, 120) as ct
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/conversations/conversations.parquet' c 
      ON n.conversation_id = c.conversation_id
    WHERE n.region != 'unknown'
    LIMIT 5
""").fetchall()
print("\n---REGION SAMPLES---")
for r in rows4:
    print(f"  {r[0]} | {r[1]}")
