import duckdb

con = duckdb.connect()

# Check NLP parquet for product/region
nlp_path = "data/nlp/nlp_results.parquet"
total = con.execute(f"SELECT count(*) FROM '{nlp_path}'").fetchone()[0]
prod = con.execute(f"SELECT count(*) FROM '{nlp_path}' WHERE product IS NOT NULL AND product != 'unknown'").fetchone()[0]
reg = con.execute(f"SELECT count(*) FROM '{nlp_path}' WHERE region IS NOT NULL AND region != 'unknown'").fetchone()[0]
print(f"Product coverage: {prod}/{total} = {prod/total*100:.1f}%")
print(f"Region coverage: {reg}/{total} = {reg/total*100:.1f}%")

print("---PRODUCT SAMPLES (5 rows)---")
rows = con.execute(f"SELECT product, LEFT(CAST(customer_text AS VARCHAR), 120) as text FROM (SELECT product, unnest(turns).text as customer_text FROM '{nlp_path}' WHERE product != 'unknown' LIMIT 5)").fetchall()
if not rows:
    # Try simpler query
    rows = con.execute(f"SELECT product FROM '{nlp_path}' WHERE product != 'unknown' LIMIT 5").fetchall()
    for r in rows:
        print(f"  product={r[0]}")
else:
    for r in rows:
        print(f"  product={r[0]} | {r[1]}")

print("---REGION SAMPLES (5 rows)---")
rows = con.execute(f"SELECT region FROM '{nlp_path}' WHERE region != 'unknown' LIMIT 5").fetchall()
for r in rows:
    print(f"  region={r[0]}")
