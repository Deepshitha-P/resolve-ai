import sys, os
sys.path.insert(0, os.getcwd())
import duckdb

con = duckdb.connect()
rows = con.execute(
    "SELECT category, count(*) as cnt, avg(sentiment) as avg_sent "
    "FROM 'data/nlp/nlp_results.parquet' "
    "GROUP BY category ORDER BY cnt DESC"
).fetchall()
total = sum(r[1] for r in rows)
print(f"Total rows: {total}")
for r in rows:
    pct = round(r[1]/total*100, 2)
    csat = round(((r[2]+1)/2)*100, 1) if r[2] is not None else None
    print(f"  {r[0]!r:30s}  vol={r[1]:>8,}  avg_sent={r[2]:.4f}  csat_proxy={csat}  pct={pct}%")
