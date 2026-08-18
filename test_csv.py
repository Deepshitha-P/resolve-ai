import duckdb
con = duckdb.connect()
print("Rows:", con.sql("SELECT count(*) FROM 'data/raw/twcs_cleaned.csv'").fetchone()[0])
rel = con.sql("SELECT author_id, count(*) as c FROM 'data/raw/twcs_cleaned.csv' WHERE inbound = false GROUP BY author_id ORDER BY c DESC LIMIT 30")
for r in rel.fetchall():
    print(f"{r[0]}: {r[1]}")
