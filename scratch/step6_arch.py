import os
import json

# Check all architecture components
checks = {}

# 1. Raw storage (CSV)
checks["raw_csv"] = os.path.exists("data/raw") and any(f.endswith(".csv") for f in os.listdir("data/raw")) if os.path.exists("data/raw") else False
checks["raw_csv_alt"] = os.path.exists("data/sample_1000.csv")

# 2. DB (DuckDB/Parquet)
checks["conversations_parquet"] = os.path.exists("data/conversations/conversations.parquet")
checks["nlp_parquet"] = os.path.exists("data/nlp/nlp_results.parquet")
checks["analytics_parquet"] = os.path.exists("data/analytics/analytics_summary.parquet")

# 3. Processing/FastAPI
checks["server_py"] = os.path.exists("server.py")
with open("server.py") as f:
    server_content = f.read()
checks["has_fastapi"] = "FastAPI" in server_content or "fastapi" in server_content
checks["has_flask"] = "Flask" in server_content or "flask" in server_content

# 4. Analytics overall feedback loop
checks["metrics_summary"] = os.path.exists("data/analytics_v2/metrics_summary.json")
if checks["metrics_summary"]:
    with open("data/analytics_v2/metrics_summary.json") as f:
        m = json.load(f)
    checks["feedback_loop"] = "insight_feedback" in m
    checks["feedback_queries"] = m.get("insight_feedback", {}).get("total_queries", 0)

# 5. Vector DB/RAG
checks["chroma_db"] = os.path.exists("data/chroma_db")

# 6. GenAI Agent (LLM provider)
checks["llm_provider"] = os.path.exists("pipeline/llm_provider.py")

# 7. Chatbot (frontend)
checks["frontend"] = os.path.exists("frontend/index.html")

# 8. Dashboard KPI independence
checks["stage18"] = os.path.exists("pipeline/stage18_analytics_v2.py") if os.path.exists("pipeline") else False

for k, v in checks.items():
    print(f"{k}: {v}")
