import sys
sys.path.insert(0, ".")
sys.path.insert(0, "pipeline")

from main import run_batch_pipeline_cached, run_query_pipeline

ctx = run_batch_pipeline_cached(sample_size=5000, rebuild=False)
result = run_query_pipeline("What are the top billing complaints this week?", ctx)

print("\n========== STEP 5 RESPONSE ==========")
insight = result["grounded_business_insight"]
text = insight.get("insight_text", "No insight generated.")
print(text)
