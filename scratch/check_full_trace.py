"""
Pull actual complaint texts from parquet for the 3 clusters.
Also check product field in parquet layers.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import duckdb

ROOT = r'c:\Users\indhu\Downloads\Resolve-AI (2)\Resolve-AI\Resolve-AI'

conv_parquet = os.path.join(ROOT, 'data/conversations/conversations.parquet')
nlp_parquet  = os.path.join(ROOT, 'data/nlp/nlp_results.parquet')
raw_parquet  = os.path.join(ROOT, 'data/parquet/raw_cases.parquet')

con = duckdb.connect()

# ---- Check raw_cases.parquet schema ----
print("=== RAW CASES PARQUET SCHEMA ===")
schema = con.execute(f"DESCRIBE SELECT * FROM '{raw_parquet}' LIMIT 1").fetchall()
print([r[0] for r in schema])

# ---- Check NLP parquet schema (has product field) ----
print("\n=== NLP PARQUET SCHEMA ===")
nlp_schema = con.execute(f"DESCRIBE SELECT * FROM '{nlp_parquet}' LIMIT 1").fetchall()
print([r[0] for r in nlp_schema])

# ---- Product distribution in NLP parquet ----
print("\n=== PRODUCT DISTRIBUTION IN NLP PARQUET ===")
prod_dist = con.execute(f"""
    SELECT COALESCE(product, '__NULL__') as prod, count(*) as cnt 
    FROM '{nlp_parquet}' 
    GROUP BY prod 
    ORDER BY cnt DESC 
    LIMIT 30
""").fetchall()
print(f"Total rows: {con.execute(f'SELECT count(*) FROM \'{nlp_parquet}\'').fetchone()[0]}")
for row in prod_dist:
    print(f"  {repr(row[0])}: {row[1]}")

# ---- Pull complaint texts for cluster 34 (software) reps ----
cluster34_reps = ['CONV-284', 'CONV-242', 'CONV-247', 'CONV-278', 'CONV-285']
cluster141_reps = ['CONV-1245', 'CONV-1247', 'CONV-1249', 'CONV-1542', 'CONV-1549']
cluster41_reps  = ['CONV-785', 'CONV-786', 'CONV-1324', 'CONV-1325', 'CONV-788']

def pull_texts(ids, label):
    print(f"\n=== CLUSTER {label} REPRESENTATIVE COMPLAINT TEXTS ===")
    id_list = "'" + "','".join(ids) + "'"
    rows = con.execute(f"""
        SELECT c.conversation_id, n.intent, n.category, n.product, n.region,
               c.company_handle
        FROM '{conv_parquet}' c
        JOIN '{nlp_parquet}' n ON c.conversation_id = n.conversation_id
        WHERE c.conversation_id IN ({id_list})
    """).fetchall()
    
    for r in rows:
        conv_id, intent, cat, product, region, brand = r
        # Get raw text from raw parquet
        raw_rows = con.execute(f"""
            SELECT clean_text FROM '{raw_parquet}'
            WHERE conversation_id = '{conv_id}'
            AND inbound = true
            LIMIT 3
        """).fetchall()
        texts = [rr[0] for rr in raw_rows]
        print(f"  {conv_id}: intent={intent} cat={cat} product={product} region={region} brand={brand}")
        for t in texts[:2]:
            print(f"    >> {str(t)[:120]}")
    
    # Any IDs not found?
    found = {r[0] for r in rows}
    missing = set(ids) - found
    if missing:
        print(f"  NOT FOUND in parquet: {missing}")

pull_texts(cluster34_reps, "34 [software, pain=22.9, esc=13.3%]")
pull_texts(cluster141_reps, "141 [ecommerce, pain=22.3, esc=16.7%]")
pull_texts(cluster41_reps, "41 [retail, pain=13.4, esc=0%]")

# ---- Full retrieval score distribution from all insight memory ----
print("\n=== FULL RETRIEVAL SCORE ANALYSIS ===")
import json

insight_path = os.path.join(ROOT, 'outputs/insight_memory.json')
with open(insight_path, 'r', encoding='utf-8') as f:
    insight_mem = json.load(f)

all_scores = []
entries = insight_mem if isinstance(insight_mem, list) else list(insight_mem.values())
for entry in entries:
    ev_chain = entry.get('evidence_chain', []) if isinstance(entry, dict) else []
    for ev in ev_chain:
        score = ev.get('relevance_score') or ev.get('score')
        if score:
            try: all_scores.append(float(score))
            except: pass

if all_scores:
    all_scores.sort()
    print(f"Total evidence scores across all queries: {len(all_scores)}")
    print(f"Score distribution:")
    buckets = [(0.0, 0.3), (0.3, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
    for lo, hi in buckets:
        count = sum(1 for s in all_scores if lo <= s < hi)
        print(f"  [{lo:.1f}-{hi:.1f}): {count}")
    print(f"  Min: {min(all_scores):.4f}, Max: {max(all_scores):.4f}, Mean: {sum(all_scores)/len(all_scores):.4f}")
else:
    # The insight_memory is not evidence-chain format, check structure
    print(f"insight_memory entries type: {type(entries[0])}")
    if isinstance(entries[0], dict):
        print(f"Keys: {list(entries[0].keys())}")
    
    # Check 17_grounded
    grounded_path = os.path.join(ROOT, 'outputs/17_grounded_insight_result.json')
    with open(grounded_path, 'r', encoding='utf-8') as f:
        g = json.load(f)
    evidence = g.get('evidence_chain', [])
    scores = [float(ev.get('relevance_score', 0)) for ev in evidence]
    print(f"\nScores from 17_grounded_insight_result: {scores}")
    conf_score = g.get('confidence_score')
    print(f"Overall confidence_score: {conf_score}")
    print(f"WARNING: Only {len(evidence)} candidates shown in output - full score distribution NOT persisted")

# ---- Check analytics for pain score origin ----
print("\n=== PAIN SCORE FORMULA (from stage07_issue_clusters.py) ===")
print("pain = 100 * (0.30 * volume_component + 0.20 * neg_sentiment_component + 0.20 * severity_component + 0.15 * growth_component + 0.15 * escalation_rate_component)")
print()
print("Verify Cluster 34 (software) pain=22.9:")
# volume_comp = len(members)/max_cluster_size
# From cluster data:
cluster_data_path = os.path.join(ROOT, 'outputs/07_issue_clusters.json')
with open(cluster_data_path, 'r', encoding='utf-8') as f:
    cluster_data = json.load(f)
clusters = cluster_data['clusters']

for cid_str in ['34', '141', '41']:
    c = clusters[cid_str]
    pi = c['pain_point_impact']
    stated_pain = pi['pain_score']
    vol = pi['volume_component']
    neg = pi['negative_sentiment_component']
    sev = pi['severity_component']
    grow = pi['growth_component']
    esc = pi['escalation_rate_component']
    recomputed = round(100.0 * (0.30*vol + 0.20*neg + 0.20*sev + 0.15*grow + 0.15*esc), 1)
    esc_pct = round(c['escalation_rate'] * 100, 1)
    print(f"Cluster {cid_str} ({c['product']}): stated_pain={stated_pain}, recomputed={recomputed}, esc={esc_pct}%, vol={c['volume']}")
    print(f"  Components: vol={vol} neg_sent={neg} sev={sev} growth={grow} esc_rate={esc}")
    match_pain = abs(stated_pain - recomputed) < 0.15
    print(f"  Pain score match: {match_pain}")
