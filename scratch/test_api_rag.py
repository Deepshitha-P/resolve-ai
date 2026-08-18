import urllib.request, json

def post_rag(query):
    req = urllib.request.Request(
        "http://localhost:8000/api/rag/query",
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())

queries = [
    "why are account complaints increasing?",
    "what is our refund policy for service delays?",
]
for q in queries:
    print(f"\n=== POST: {q!r} ===")
    d = post_rag(q)
    ans = d.get("answer", {})
    print(f"  query_type : {d.get('query_type')}")
    print(f"  priority   : {ans.get('priority')}")
    print(f"  recommendations:")
    for i, a in enumerate(ans.get("recommendations", []), 1):
        print(f"    {i}. {a}")
