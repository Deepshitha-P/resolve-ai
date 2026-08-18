import sys
from pipeline.stage13_query_router import route_query

q = "Show me raw tweets where the customer complained about broadband outage"
routed = route_query(q, [])
print("Query:", q)
print("Type:", routed["query_type"])
print("Layers:", routed["selected_layers"])

if routed["query_type"] == "deep_dive_raw_data":
    from pipeline.warehouse_engine import WarehouseEngine
    engine = WarehouseEngine()
    ev = engine.search_raw_data(q, limit=2)
    print("Warehouse returned:", len(ev), "records")
    for e in ev:
        print(f" - {e['doc_id']}: {e['excerpt'][:50]}...")
