import duckdb
con = duckdb.connect()

# Coverage on full NLP parquet
total = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet'").fetchone()[0]
prod = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet' WHERE product IS NOT NULL AND product != 'unknown'").fetchone()[0]
reg = con.execute("SELECT count(*) FROM 'data/nlp/nlp_results.parquet' WHERE region IS NOT NULL AND region != 'unknown'").fetchone()[0]
print(f"Product coverage: {prod}/{total} = {prod/total*100:.1f}%")
print(f"Region coverage: {reg}/{total} = {reg/total*100:.1f}%")

# Get samples - join with conversations to get clean_text
# Actually, NLP parquet has entities.product_service - let's use that with product field
print("\n---5 PRODUCT SAMPLES (product | first 120 chars of entities.product_service)---")
rows = con.execute("""
    SELECT product, entities.product_service, LEFT(CAST(case_id AS VARCHAR), 30)
    FROM 'data/nlp/nlp_results.parquet' 
    WHERE product != 'unknown' 
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  product={r[0]} | entity_product_service={r[1]} | case_id={r[2]}")

print("\n---5 REGION SAMPLES (region | case_id)---")
rows = con.execute("""
    SELECT region, LEFT(CAST(case_id AS VARCHAR), 30), entities.location
    FROM 'data/nlp/nlp_results.parquet' 
    WHERE region != 'unknown' 
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  region={r[0]} | case_id={r[1]} | entity_location={r[2]}")
