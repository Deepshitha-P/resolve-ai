import json
with open("data/analytics_v2/metrics_summary.json", "r") as f:
    d = json.load(f)

ca = d.get("category_analysis", {})
print("=== category_analysis ===")
print(f"  coverage_percentage: {ca.get('coverage_percentage')}")
print(f"  category_mention_cases: {ca.get('category_mention_cases')}")
print(f"  unknown_percentage: {ca.get('unknown_percentage')}")
print(f"  unique_normalized_categories: {ca.get('unique_normalized_categories')}")
print("\n  top_categories (all, by volume):")
for r in sorted(ca.get("top_categories", []), key=lambda x: x["total_cases"], reverse=True):
    print(f"    {r['category_name']:30s} vol={r['total_cases']:>8,}  csat_proxy={r['csat_proxy']}")

print("\n=== product_analysis coverage for comparison ===")
pa = d.get("product_analysis", {})
print(f"  product coverage_percentage: {pa.get('coverage_percentage')}")
print(f"  region coverage_percentage: {d.get('region_analysis', {}).get('coverage_percentage')}")
