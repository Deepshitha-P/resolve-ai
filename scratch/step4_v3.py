import json

convs = json.load(open("outputs/03_conversations.json", encoding="utf-8"))
total = len(convs)
prod_found = sum(1 for c in convs if c.get("nlp", {}).get("product", "unknown") != "unknown" or c.get("product", "unknown") != "unknown")
reg_found = sum(1 for c in convs if c.get("nlp", {}).get("region", "unknown") != "unknown" or c.get("region", "unknown") != "unknown")
print(f"Sample size: {total} (JSON saved only first 100)")
print(f"Product coverage: {prod_found}/{total} = {prod_found/total*100:.1f}%")
print(f"Region coverage: {reg_found}/{total} = {reg_found/total*100:.1f}%")

print("---PRODUCT SAMPLES (5 with tagged product + clean_text)---")
count = 0
for c in convs:
    p = c.get("nlp", {}).get("product") or c.get("product", "unknown")
    if p != "unknown" and count < 5:
        turns = c.get("turns", [])
        ct = ""
        for t in turns:
            if t.get("role") == "customer" or t.get("inbound", True):
                ct = (t.get("text", "") or "")[:120]
                break
        if not ct:
            ct = (turns[0].get("text", "") if turns else "")[:120]
        print(f"  {p} | {ct}")
        count += 1

print("---REGION SAMPLES (5 with tagged region + clean_text)---")
count = 0
for c in convs:
    r = c.get("nlp", {}).get("region") or c.get("region", "unknown")
    if r != "unknown" and count < 5:
        turns = c.get("turns", [])
        ct = ""
        for t in turns:
            if t.get("role") == "customer" or t.get("inbound", True):
                ct = (t.get("text", "") or "")[:120]
                break
        if not ct:
            ct = (turns[0].get("text", "") if turns else "")[:120]
        print(f"  {r} | {ct}")
        count += 1
