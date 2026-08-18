"""
test_nlp.py — Resolve-AI Pipeline Tester
=========================================
Tests all 3 upgraded layers:
  1. TransformerNLPProvider  (sentiment + intent + emotion)
  2. FastEmbedder            (bge-base-en-v1.5, 768-dim)
  3. ChromaVectorDB          (upsert + semantic search)

Run with:
    python test_nlp.py
"""

import os, sys
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env", override=False)
except ImportError:
    pass

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — TransformerNLPProvider
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print(" TEST 1: TransformerNLPProvider (NLP Engine)")
print("="*65)

TEST_CASES = [
    {
        "text": "I was charged twice and no one is responding to my emails!",
        "expected_category":    "payment",
        "expected_subcategory": "duplicate_charge",
        "expected_sentiment":   "negative",
        "expected_emotion":     "anger",
    },
    {
        "text": "My internet has been down for 3 days and your team ignored me.",
        "expected_category":    "network",
        "expected_subcategory": "internet_down",
        "expected_sentiment":   "negative",
        "expected_emotion":     "frustration",
    },
    {
        "text": "Thank you so much, the issue is fully resolved!",
        "expected_category":    None,
        "expected_subcategory": None,
        "expected_sentiment":   "positive",
        "expected_emotion":     "satisfaction",
    },
    {
        "text": "Cannot login, OTP is not being received at all.",
        "expected_category":    "authentication",
        "expected_subcategory": "login_failed",
        "expected_sentiment":   "negative",
        "expected_emotion":     "frustration",
    },
]

try:
    from pipeline.nlp_engine import TransformerNLPProvider, LocalNLPProvider

    provider = TransformerNLPProvider()
    print(f"Provider available (transformer): {provider._available}")
    if not provider._available:
        print("  -> Falling back to LocalNLPProvider")
        provider = LocalNLPProvider()

    nlp_pass = 0
    for i, tc in enumerate(TEST_CASES, 1):
        r = provider.analyze_text(tc["text"])
        checks = []
        if tc["expected_category"]:
            checks.append(("category",   r.category == tc["expected_category"],   r.category,   tc["expected_category"]))
        if tc["expected_subcategory"]:
            checks.append(("subcategory", r.subcategory == tc["expected_subcategory"], r.subcategory, tc["expected_subcategory"]))
        checks.append(("sentiment", r.sentiment_label == tc["expected_sentiment"], r.sentiment_label, tc["expected_sentiment"]))
        checks.append(("emotion",   r.emotion == tc["expected_emotion"],           r.emotion,         tc["expected_emotion"]))

        all_ok = all(c[1] for c in checks)
        if all_ok:
            nlp_pass += 1

        print(f"\n  [{i}] {tc['text'][:60]}")
        print(f"      category : {r.category} / sub: {r.subcategory}")
        print(f"      sentiment: {r.sentiment_label} ({r.sentiment:.3f})  emotion: {r.emotion}")
        print(f"      urgency  : {r.urgency}  severity: {r.severity.label}  confidence: {r.confidence:.3f}")
        print(f"      source   : {r.label_source}  model: {r.model_version}")
        print(f"      {PASS if all_ok else FAIL}")

    results.append(("NLP Engine", nlp_pass, len(TEST_CASES)))

except Exception as e:
    print(f"  {FAIL} NLP test crashed: {e}")
    import traceback; traceback.print_exc()
    results.append(("NLP Engine", 0, len(TEST_CASES)))


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — FastEmbedder (bge-base-en-v1.5, 768-dim)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print(" TEST 2: FastEmbedder (BAAI/bge-base-en-v1.5, 768-dim)")
print("="*65)

try:
    from pipeline.stage10_embeddings import FastEmbedder
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    embed_model = os.environ.get("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
    embedder = FastEmbedder(model_name=embed_model)

    texts = [
        "customer payment failed twice",
        "internet service outage in london",
        "login otp not received",
    ]
    vectors  = embedder.encode(texts)
    vec_arr  = np.array(vectors)

    print(f"  Model       : {embed_model}")
    print(f"  Available   : {embedder.is_available}")
    print(f"  Output shape: {vec_arr.shape}  (expected: ({len(texts)}, 768))")

    dim_ok   = vec_arr.shape == (len(texts), 768)
    sims     = cosine_similarity(vec_arr)
    sims_ok  = all(0.0 <= sims[i][j] <= 1.0 for i in range(3) for j in range(3))

    print(f"  Dim=768 check: {'OK' if dim_ok else 'FAIL'}")
    print(f"  Similarity range [0,1]: {'OK' if sims_ok else 'FAIL'}")
    all_embed_ok = dim_ok and embedder.is_available and sims_ok
    print(f"  {PASS if all_embed_ok else FAIL}")
    results.append(("Embedder (768-dim)", int(all_embed_ok), 1))

except Exception as e:
    print(f"  {FAIL} Embedder test crashed: {e}")
    import traceback; traceback.print_exc()
    results.append(("Embedder (768-dim)", 0, 1))


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — ChromaVectorDB (upsert + semantic search)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print(" TEST 3: ChromaVectorDB (upsert + semantic search)")
print("="*65)

try:
    from pipeline.stage11_vector_db import ChromaVectorDB

    test_col = "test_resolve_verify"
    test_dir = "./data/chroma_db_test"

    vdb = ChromaVectorDB(collection_name=test_col, persist_dir=test_dir)
    print(f"  ChromaDB available: {vdb.is_available}")

    if vdb.is_available:
        vdb.delete_collection()
        vdb = ChromaVectorDB(collection_name=test_col, persist_dir=test_dir)

        docs = [
            {"doc_id": "d1", "title": "Payment failure cluster",
             "text": "Customers charged twice with no refund.", "type": "issue_cluster"},
            {"doc_id": "d2", "title": "Network outage cluster",
             "text": "Broadband internet down for days, no support response.", "type": "issue_cluster"},
            {"doc_id": "d3", "title": "Login issue cluster",
             "text": "OTP not received, cannot access account.", "type": "issue_cluster"},
        ]
        vdb.add(docs)
        count = vdb.count()
        print(f"  Docs indexed : {count}  (expected 3)")

        res_pay = vdb.search("customer charged twice duplicate payment", top_k=3)
        top_pay = res_pay[0]["doc"]["title"] if res_pay else "None"
        pay_ok  = "Payment" in top_pay
        print(f"  Query 'charged twice' -> '{top_pay}'  {'OK' if pay_ok else 'CHECK'}")

        res_net = vdb.search("broadband internet not working outage", top_k=3)
        top_net = res_net[0]["doc"]["title"] if res_net else "None"
        net_ok  = "Network" in top_net
        print(f"  Query 'internet outage' -> '{top_net}'  {'OK' if net_ok else 'CHECK'}")

        vdb.delete_collection()
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

        vdb_ok = (count == 3) and bool(res_pay) and bool(res_net)
        print(f"  {PASS if vdb_ok else FAIL}")
        results.append(("ChromaVectorDB", int(vdb_ok), 1))
    else:
        print(f"  {FAIL} ChromaDB unavailable — pip install chromadb")
        results.append(("ChromaVectorDB", 0, 1))

except Exception as e:
    print(f"  {FAIL} ChromaDB test crashed: {e}")
    import traceback; traceback.print_exc()
    results.append(("ChromaVectorDB", 0, 1))


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print(" SUMMARY")
print("="*65)
total_pass = total_tests = 0
for name, passed, total in results:
    status = PASS if passed == total else FAIL
    print(f"  {status}  {name:<25} {passed}/{total} passed")
    total_pass  += passed
    total_tests += total

print(f"\n  Overall: {total_pass}/{total_tests} checks passed")
print("  All systems GO!" if total_pass == total_tests else "  Some checks need review (see above).")
print("="*65 + "\n")
