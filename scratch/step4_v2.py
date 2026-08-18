import duckdb
con = duckdb.connect()
nlp_count = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet'").fetchone()[0]
conv_count = con.execute("SELECT count(*) FROM 'data/conversations/conversations.parquet'").fetchone()[0]
print(f"nlp parquet rows: {nlp_count}")
print(f"conv parquet rows: {conv_count}")

# Product/region from conversations parquet (where stage04 writes back)
prod = con.execute("SELECT count(*) FROM 'data/conversations/conversations.parquet' WHERE product IS NOT NULL AND product != 'unknown'").fetchone()[0]
reg = con.execute("SELECT count(*) FROM 'data/conversations/conversations.parquet' WHERE region IS NOT NULL AND region != 'unknown'").fetchone()[0]
print(f"Product coverage (conv): {prod}/{conv_count} = {prod/conv_count*100:.1f}%")
print(f"Region coverage (conv): {reg}/{conv_count} = {reg/conv_count*100:.1f}%")

# Samples with clean_text
print("---PRODUCT SAMPLES---")
rows = con.execute("""
    SELECT product, LEFT(clean_text, 120) as ct 
    FROM 'data/conversations/conversations.parquet' 
    WHERE product IS NOT NULL AND product != 'unknown' 
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  product={r[0]} | {r[1]}")

print("---REGION SAMPLES---")
rows = con.execute("""
    SELECT region, LEFT(clean_text, 120) as ct 
    FROM 'data/conversations/conversations.parquet' 
    WHERE region IS NOT NULL AND region != 'unknown' 
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  region={r[0]} | {r[1]}")
