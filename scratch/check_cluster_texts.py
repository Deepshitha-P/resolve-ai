"""
Pulls representative complaint texts for clusters 34, 141, 41.
Also checks full retrieval score distribution and analytics.
"""
import json, os

ROOT = r'c:\Users\indhu\Downloads\Resolve-AI (2)\Resolve-AI\Resolve-AI'

# ---- Load conversations ----
with open(os.path.join(ROOT, 'outputs/03_conversations.json'), 'r', encoding='utf-8') as f:
    convs = json.load(f)

conv_by_id = {c.get('conversation_id'): c for c in convs if c.get('conversation_id')}

# ---- Representative cases per cluster ----
cluster_reps = {
    "34  [software, pain=22.9, esc=13.3%]": ['CONV-284', 'CONV-242', 'CONV-247', 'CONV-278', 'CONV-285'],
    "141 [ecommerce, pain=22.3, esc=16.7%]": ['CONV-1245', 'CONV-1247', 'CONV-1249', 'CONV-1542', 'CONV-1549'],
    "41  [retail, pain=13.4, esc=0%]": ['CONV-785', 'CONV-786', 'CONV-1324', 'CONV-1325', 'CONV-788'],
}

for cluster_label, reps in cluster_reps.items():
    print(f"=== CLUSTER {cluster_label} ===")
    for conv_id in reps:
        c = conv_by_id.get(conv_id)
        if not c:
            print(f"  {conv_id}: NOT FOUND")
            continue
        turns = c.get('turns', [])
        texts = [t.get('text', '') for t in turns[:3] if t.get('text')]
        nlp = c.get('nlp', {})
        intent = nlp.get('intent', 'N/A')
        category = nlp.get('category', 'N/A')
        product = nlp.get('product', 'N/A')
        region = nlp.get('region', 'N/A')
        traj = nlp.get('trajectory', {})
        esc_flag = traj.get('escalation_flag', 'N/A') if isinstance(traj, dict) else 'N/A'
        print(f"  {conv_id}: intent={intent} cat={category} product={product} region={region} esc_flag={esc_flag}")
        for i, t in enumerate(texts[:2]):
            print(f"    turn[{i}]: {t[:120]}")
    print()

# ---- Full retrieval score distribution ----
print("=" * 60)
print("RETRIEVAL SCORE DISTRIBUTION (from insight_memory.json)")
print("=" * 60)

insight_path = os.path.join(ROOT, 'outputs/insight_memory.json')
if os.path.exists(insight_path):
    with open(insight_path, 'r', encoding='utf-8') as f:
        insight_mem = json.load(f)
    
    # Collect all relevance scores across all queries
    all_scores = []
    entries = insight_mem if isinstance(insight_mem, list) else []
    if isinstance(insight_mem, dict):
        entries = list(insight_mem.values())
    
    print(f"Number of insight_memory entries: {len(entries)}")
    for entry in entries[:3]:
        if isinstance(entry, dict):
            ev_chain = entry.get('evidence_chain', [])
            for ev in ev_chain:
                score = ev.get('relevance_score') or ev.get('score')
                if score:
                    try:
                        all_scores.append(float(score))
                    except Exception:
                        pass
    
    if all_scores:
        all_scores.sort()
        print(f"All evidence scores: {all_scores}")
        print(f"Min: {min(all_scores):.4f}, Max: {max(all_scores):.4f}, Mean: {sum(all_scores)/len(all_scores):.4f}")
    
    # Show first entry structure
    if entries:
        first = entries[0]
        if isinstance(first, dict):
            print(f"\nFirst entry keys: {list(first.keys())[:10]}")
else:
    print("insight_memory.json not found")

# Also check the 17_grounded_insight
grounded_path = os.path.join(ROOT, 'outputs/17_grounded_insight_result.json')
if os.path.exists(grounded_path):
    with open(grounded_path, 'r', encoding='utf-8') as f:
        g = json.load(f)
    
    evidence = g.get('evidence_chain', [])
    print(f"\nEvidence chain in 17_grounded_insight_result.json: {len(evidence)} items")
    for ev in evidence:
        doc_id = ev.get('doc_id', 'N/A')
        score = ev.get('relevance_score', 'N/A')
        conf = ev.get('metadata', {}).get('confidence', 'N/A')
        text = ev.get('text', '')[:80]
        print(f"  {doc_id}: relevance={score} trust={conf} text={text}")

# ---- Analytics snapshots ----
print()
print("=" * 60)
print("ANALYTICS_V2 / AGGREGATION OUTPUT (check5: cluster volume)")
print("=" * 60)
analytics_v2_dir = os.path.join(ROOT, 'data/analytics_v2')
if os.path.exists(analytics_v2_dir):
    files = os.listdir(analytics_v2_dir)
    print(f"analytics_v2 files: {files}")
    for fname in files[:3]:
        fpath = os.path.join(analytics_v2_dir, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()[:2000]
        print(f"\n--- {fname} (first 2000 chars) ---")
        print(content)
else:
    print("data/analytics_v2 dir not found")

# stage18 analytics
analytics_path = os.path.join(ROOT, 'outputs/05_analytics.json')
if os.path.exists(analytics_path):
    with open(analytics_path, 'r', encoding='utf-8') as f:
        analytics = json.load(f)
    print(f"\nanalytics (05) keys: {list(analytics.keys())[:10]}")
    # Check categories
    cat_dist = analytics.get('category_distribution', {})
    if cat_dist:
        print(f"Category distribution: {cat_dist}")
    top_cats = analytics.get('top_categories', [])
    if top_cats:
        print(f"Top categories: {top_cats}")
