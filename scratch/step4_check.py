import json

convs = json.load(open("outputs/03_conversations.json", encoding="utf-8"))
total = len(convs)
prod_found = sum(1 for c in convs if c.get("product", "unknown") != "unknown")
reg_found = sum(1 for c in convs if c.get("region", "unknown") != "unknown")
print(f"Product coverage: {prod_found}/{total} = {prod_found/total*100:.1f}%")
print(f"Region coverage: {reg_found}/{total} = {reg_found/total*100:.1f}%")

print("---PRODUCT SAMPLES---")
count = 0
for c in convs:
    if c.get("product", "unknown") != "unknown" and count < 5:
        ct = (c.get("turns", [{}])[0].get("text", "") or "")[:120]
        print(f"  product={c['product']} | {ct}")
        count += 1

print("---REGION SAMPLES---")
count = 0
for c in convs:
    if c.get("region", "unknown") != "unknown" and count < 5:
        ct = (c.get("turns", [{}])[0].get("text", "") or "")[:120]
        print(f"  region={c['region']} | {ct}")
        count += 1
