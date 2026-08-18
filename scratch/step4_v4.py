import duckdb
con = duckdb.connect()
nlp_count = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet'").fetchone()[0]
print(f"NLP parquet rows: {nlp_count}")

# Check columns
cols = con.execute("DESCRIBE SELECT * FROM 'data/nlp/nlp_results.parquet'").fetchall()
print("NLP columns:", [c[0] for c in cols])

prod = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet' WHERE product IS NOT NULL AND product != 'unknown'").fetchone()[0]
reg = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet' WHERE region IS NOT NULL AND region != 'unknown'").fetchone()[0]
print(f"Product coverage: {prod}/{nlp_count} = {prod/nlp_count*100:.1f}%")
print(f"Region coverage: {reg}/{nlp_count} = {reg/nlp_count*100:.1f}%")

print("---PRODUCT SAMPLES (5)---")
rows = con.execute("SELECT product, LEFT(entities, 120) FROM 'data/nlp/nlp_results.parquet' WHERE product != 'unknown' LIMIT 5").fetchall()
for r in rows:
    print(f"  product={r[0]} | entities={r[1]}")

print("---REGION SAMPLES (5)---")
rows = con.execute("SELECT region, LEFT(entities, 120) FROM 'data/nlp/nlp_results.parquet' WHERE region != 'unknown' LIMIT 5").fetchall()
for r in rows:
    print(f"  region={r[0]} | entities={r[1]}")
