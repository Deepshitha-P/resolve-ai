import duckdb
import spacy
import yaml
import textwrap

con = duckdb.connect()

print("--- 1 & 3: PERCENTAGES ---")
rel = con.sql("""
    SELECT 
        company_handle_source, 
        count(*) as count 
    FROM 'data/conversations/conversations.parquet' 
    GROUP BY company_handle_source
""")
for r in rel.fetchall():
    print(f"{r[0]}: {r[1]}")

rel2 = con.sql("""
    SELECT 
        count(*) as total,
        sum(case when region != 'unknown' then 1 else 0 end) as region_found,
        sum(case when product != 'unknown' then 1 else 0 end) as product_found
    FROM 'data/nlp/nlp_results.parquet'
""")
r2 = rel2.fetchone()
print(f"Total: {r2[0]}, Region Found: {r2[1]}, Product Found: {r2[2]}")

print("\n--- 2: FALSE POSITIVE GUARD CHECK ---")
with open("config/company_product_map.yaml", "r") as f:
    cmap = yaml.safe_load(f) or {}
guard_words = set(k.lower() for k in cmap.keys()) | set(v.lower() for v in cmap.values())

nlp = spacy.load("en_core_web_sm")
rel_text = con.sql("SELECT turns[1].text FROM 'data/conversations/conversations.parquet'").fetchall()
caught = 0
caught_list = []
for row in rel_text:
    doc = nlp(row[0])
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            clean_ent = ent.text.strip().lower()
            if clean_ent and clean_ent in guard_words:
                caught += 1
                caught_list.append(clean_ent)
print(f"False Positives Caught: {caught}")
from collections import Counter
if caught_list:
    print(dict(Counter(caught_list)))

print("\n--- 4: SPOT CHECK 15 REGIONS ---")
rel3 = con.sql("""
    SELECT n.region, c.turns[1].text, n.product 
    FROM 'data/nlp/nlp_results.parquet' n
    JOIN 'data/conversations/conversations.parquet' c ON n.conversation_id = c.conversation_id
    WHERE n.region != 'unknown' AND n.region IS NOT NULL
    LIMIT 15
""")
for r in rel3.fetchall():
    print(f"[{r[0]}] -> {textwrap.shorten(r[1].replace(chr(10), ' '), width=100)}")

print("\n--- 5: SNAPSHOT PRODUCTS ---")
import json
with open('outputs/08_analytics_snapshots.json', 'r') as f:
    snaps = json.load(f)
products = set(s.get('product') for s in snaps if s.get('product'))
print(f"Products in Snapshots: {products}")
