"""
Pipeline trace script for verification checks 1-5.
"""
import json
import os
from collections import Counter
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# CHECK 1: Raw data product field distribution
# ============================================================
print("=" * 60)
print("CHECK 1: RAW DATA PRODUCT FIELD DISTRIBUTION")
print("=" * 60)

with open(os.path.join(ROOT, "outputs/01_raw_data.json"), "r") as f:
    raw = json.load(f)

print(f"Total raw records in outputs/01_raw_data.json: {len(raw)}")
products_raw = [r.get("product", "__MISSING__") for r in raw]
print("Product field distribution:")
for k, v in Counter(products_raw).most_common(30):
    print(f"  {repr(k)}: {v}")

channels = [r.get("channel", "__MISSING__") for r in raw]
print("Channel distribution:")
for k, v in Counter(channels).most_common():
    print(f"  {repr(k)}: {v}")

brands = set()
for r in raw:
    cid = r.get("customer_id", "")
    if cid and cid.startswith("BRAND-"):
        brands.add(cid.replace("BRAND-", ""))
print(f"Unique brand IDs in dataset: {sorted(brands)}")

print("\nSample 5 raw_text values:")
for i, r in enumerate(raw[:5]):
    print(f"  [{i}] customer_id={r.get('customer_id')} | {r.get('raw_text', '')[:80]}")

# ============================================================
# CHECK 1b: Product gazetteer vs telecom domain
# ============================================================
print()
print("=" * 60)
print("CHECK 1b: PRODUCT KEYWORDS GAZETTEER (stage04_nlp.py)")
print("=" * 60)
with open(os.path.join(ROOT, "pipeline/stage04_nlp.py"), "r", encoding="utf-8", errors="replace") as f:
    stage04_src = f.read()

telecom_terms = ["network outage", "billing dispute", "5G", "4G", "roaming", "prepaid", "postpaid",
                 "chennai", "t.nagar", "airtel", "jio", "vodafone", "bsnl", "recharge",
                 "software", "ecommerce", "retail"]
print("Telecom/domain terms in stage04_nlp.py:")
for term in telecom_terms:
    found = term.lower() in stage04_src.lower()
    print(f"  {repr(term)}: {'FOUND' if found else 'NOT FOUND'}")

# ============================================================
# CHECK 2: Cluster labeling
# ============================================================
print()
print("=" * 60)
print("CHECK 2: CLUSTER LABELING")
print("=" * 60)

with open(os.path.join(ROOT, "outputs/07_issue_clusters.json"), "r") as f:
    cluster_data = json.load(f)

clusters = cluster_data.get("clusters", {})
print(f"Total clusters: {len(clusters)}")

cluster_products = [c.get("product", "MISSING") for c in clusters.values()]
print("Product distribution in clusters:")
for k, v in Counter(cluster_products).most_common(30):
    print(f"  {repr(k)}: {v}")

target_clusters = [41, 141, 34]
print()
for target_id in target_clusters:
    found_key = None
    for k, c in clusters.items():
        if c.get("cluster_id") == target_id:
            found_key = k
            break
    if found_key:
        c = clusters[found_key]
        print(f"=== CLUSTER cluster_id={target_id} (key={found_key}) ===")
        print(f"  cluster_name:      {c.get('cluster_name')}")
        print(f"  product:           {c.get('product')}")
        print(f"  region:            {c.get('region')}")
        print(f"  dominant_topic:    {c.get('dominant_topic')}")
        print(f"  volume:            {c.get('volume')}")
        print(f"  pain_score:        {c.get('pain_point_impact', {}).get('pain_score')}")
        print(f"  escalation_rate:   {c.get('escalation_rate')}")
        print(f"  representative:    {c.get('representative_case_ids')}")
        print(f"  keywords:          {c.get('keywords')}")
        print(f"  summary:           {c.get('summary')}")
    else:
        print(f"=== CLUSTER cluster_id={target_id}: NOT FOUND ===")

print()
print("Top 5 clusters by volume:")
sorted_clusters = sorted(clusters.values(), key=lambda c: c.get("volume", 0), reverse=True)
for c in sorted_clusters[:5]:
    print(f"  id={c.get('cluster_id')} | name={c.get('cluster_name')} | vol={c.get('volume')} | pain={c.get('pain_point_impact', {}).get('pain_score')}")

print()
print("Top 5 clusters by pain_score:")
sorted_by_pain = sorted(clusters.values(), key=lambda c: c.get("pain_point_impact", {}).get("pain_score", 0), reverse=True)
for c in sorted_by_pain[:5]:
    print(f"  id={c.get('cluster_id')} | name={c.get('cluster_name')} | pain={c.get('pain_point_impact', {}).get('pain_score')} | esc={c.get('escalation_rate')}")

# ============================================================
# CHECK 3: Embedding model
# ============================================================
print()
print("=" * 60)
print("CHECK 3: EMBEDDING MODEL")
print("=" * 60)

env_path = os.path.join(ROOT, ".env")
embed_lines = []
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if "EMBED" in line.upper() or "embed" in line.lower():
                embed_lines.append(line.strip())
print(f"Embed-related lines in .env: {embed_lines}")

with open(os.path.join(ROOT, "pipeline/stage10_embeddings.py"), "r", encoding="utf-8", errors="replace") as f:
    s10 = f.read()

m = re.search(r'EMBED_MODEL\s*=.*', s10)
if m:
    print(f"EMBED_MODEL default in stage10_embeddings.py: {m.group()}")

st_mention = "sentence-transformer" in s10.lower() or "sentence_transformers" in s10.lower()
fastembed_mention = "fastembed" in s10.lower()
print(f"  'sentence-transformer' mentioned: {st_mention}")
print(f"  'fastembed' mentioned: {fastembed_mention}")

# ============================================================
# CHECK 3b: Evidence chain scores
# ============================================================
print()
print("CHECK 3b: RETRIEVAL EVIDENCE SCORES")
grounded_path = os.path.join(ROOT, "outputs/17_grounded_insight_result.json")
if os.path.exists(grounded_path):
    with open(grounded_path, "r") as f:
        g = json.load(f)
    evidence = g.get("evidence_chain", [])
    print(f"Evidence chain length: {len(evidence)}")
    scores = []
    for ev in evidence:
        score = ev.get("relevance_score")
        if score is not None:
            scores.append(float(score))
        print(f"  doc_id={ev.get('doc_id')} | relevance={score} | conf={ev.get('metadata', {}).get('confidence')} | text={ev.get('text', '')[:60]}")
    if scores:
        print(f"Score range: min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
    print(f"Overall confidence_score: {g.get('confidence_score')}")

# ============================================================
# CHECK 4: Pain score formula vs stated numbers
# ============================================================
print()
print("=" * 60)
print("CHECK 4: PAIN SCORE FORMULA + NUMBER GROUNDEDNESS")
print("=" * 60)

# Extract formula from stage07
with open(os.path.join(ROOT, "pipeline/stage07_issue_clusters.py"), "r", encoding="utf-8", errors="replace") as f:
    s07 = f.read()

formula_match = re.search(r"pain_score\s*=\s*round\(.*?\)", s07, re.DOTALL)
if formula_match:
    print(f"Pain score formula in stage07:\n{formula_match.group()}")

# Dashboard states these clusters:
# DOC-CLUSTER-41: software, pain=22.9, esc=13.3%
# DOC-CLUSTER-141: ecommerce, pain=22.3, esc=16.7%
# DOC-CLUSTER-34: retail, pain=13.4, esc=0%

print()
print("Dashboard claimed numbers vs actual cluster DB:")
claimed = {
    "DOC-CLUSTER-41":  {"product": "software",   "pain": 22.9, "esc_pct": 13.3},
    "DOC-CLUSTER-141": {"product": "ecommerce",  "pain": 22.3, "esc_pct": 16.7},
    "DOC-CLUSTER-34":  {"product": "retail",     "pain": 13.4, "esc_pct": 0.0},
}
for cluster_label, claim in claimed.items():
    print(f"  {cluster_label}: dashboard says product={claim['product']}, pain={claim['pain']}, esc={claim['esc_pct']}%")
    # Try to find matching cluster in actual data
    matching = [c for c in clusters.values() if claim["product"] in c.get("product", "").lower()]
    if matching:
        for m in matching:
            actual_pain = m.get("pain_point_impact", {}).get("pain_score")
            actual_esc = round(m.get("escalation_rate", 0) * 100, 1)
            print(f"    ACTUAL cluster (id={m.get('cluster_id')}): pain={actual_pain}, esc={actual_esc}%, name={m.get('cluster_name')}")
    else:
        print(f"    NO cluster with product={repr(claim['product'])} found in 07_issue_clusters.json!")

# ============================================================
# CHECK 5: Total cluster count and complaint volume
# ============================================================
print()
print("=" * 60)
print("CHECK 5: CLUSTER COUNT + COMPLAINT VOLUME")
print("=" * 60)
print(f"Total clusters in 07_issue_clusters.json: {len(clusters)}")
incidents = cluster_data.get("incident_candidates", [])
print(f"Total incident_candidates (potential incidents): {len(incidents)}")

conv_path = os.path.join(ROOT, "outputs/03_conversations.json")
if os.path.exists(conv_path):
    with open(conv_path, "r") as f:
        convs = json.load(f)
    print(f"Total conversations in 03_conversations.json: {len(convs)}")

first_c = list(clusters.values())[0]
print(f"total_conversations field (from first cluster): {first_c.get('total_conversations')}")
print(f"sample_volume field (from first cluster): {first_c.get('sample_volume')}")
print(f"is_sample_based (from first cluster): {first_c.get('is_sample_based')}")

volumes = [c.get("volume", 0) for c in clusters.values()]
total_vol = sum(volumes)
print(f"Sum of all cluster volumes: {total_vol}")
print(f"Min cluster volume: {min(volumes)}, Max: {max(volumes)}, Mean: {total_vol/len(volumes):.1f}")
print(f"Clusters with volume >= 10: {sum(1 for v in volumes if v >= 10)}")
print(f"Clusters with volume == 1: {sum(1 for v in volumes if v == 1)}")

# Show volume distribution
print("Volume distribution buckets:")
for bucket, label in [(1, "=1"), (2, "=2"), (3, "=3"), (5, "<5"), (10, "<10"), (20, "<20"), (999, "20+")]:
    count = sum(1 for v in volumes if v <= bucket)
print("Full distribution (sorted desc):")
print(sorted(volumes, reverse=True)[:20])
