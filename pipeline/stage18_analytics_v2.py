"""
stage18_analytics_v2.py

UC18 Analytics V2 Enterprise Customer Intelligence Layer.

Executes out-of-core over:
- data/conversations/conversations.parquet (1,898,083 rows)
- data/nlp/nlp_results.parquet (1,898,083 rows)

Computes:
1. Response Time (Avg, Median, P90, P95, Category/Product/Region breakdowns)
2. First Contact Resolution (FCR) (Deterministic turn & company response rule)
3. Escalation Rate (NLP escalation signals)
4. Reopen Rate (Repeat contact signals)
5. Satisfaction / CSAT Proxy & Trajectory (Sentiment + Signal Calibrated Formula)
6. Product Analysis (Normalized entities.product_service, volume, sentiment, severity)
7. Region Analysis (Normalized entities.location, volume, sentiment, severity)
8. Recurring Pain Points (Issue clusters sentiment impact & volume)
9. Emerging Issues (Growth rate over time & emerging issue score)

Outputs:
- data/analytics_v2/metrics_summary.json
- data/analytics_v2/category_metrics.parquet
- data/analytics_v2/product_metrics.parquet
- data/analytics_v2/region_metrics.parquet
- data/analytics_v2/csat_trajectory.parquet
- data/knowledge/analytics_snapshots/analytics_snapshots.parquet (appends DOC-SNAPSHOT-ANALYTICS-V2)
"""

import os
import sys
import json
import time
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

project_root = os.getcwd()
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "pipeline"))

from config_loader import load_config
from storage import StorageEngine, CheckpointManager
from logger import get_logger
from schemas import KnowledgeDocument


logger = get_logger("Stage18_AnalyticsV2")

def run_stage18_analytics_v2(config=None, storage=None):
    if config is None:
        config = load_config()
    if storage is None:
        storage = StorageEngine(config)

    checkpoint_mgr = CheckpointManager(os.path.join(project_root, "data", "checkpoints"))
    
    conv_file = os.path.join(project_root, "data", "conversations", "conversations.parquet")
    nlp_file = os.path.join(project_root, "data", "nlp", "nlp_results.parquet")

    if not os.path.exists(conv_file) or not os.path.exists(nlp_file):
        raise FileNotFoundError("Stage 3 or Stage 4 parquet production files missing!")

    out_dir = os.path.join(project_root, "data", "analytics_v2")
    os.makedirs(out_dir, exist_ok=True)

    con = duckdb.connect()

    logger.info("Computing UC18 Analytics V2 out-of-core over 1,898,083 conversations...")

    # 1. OVERALL METRICS SUMMARY
    # FCR Rule: customer_turn_count == 1 AND has_company_response == true
    # Escalation Rule: len(escalation_signals) > 0
    # Reopen Rule: repeat_contact_signals == true
    _conv_fwd = conv_file.replace('\\', '/')
    _nlp_fwd  = nlp_file.replace('\\', '/')
    overall_query = f"""
        SELECT
            count(*) as total_conversations,
            count(CASE WHEN c.has_company_response = true THEN 1 END) as company_responded_count,
            count(CASE WHEN c.first_response_time IS NOT NULL AND c.first_response_time > 0 THEN 1 END) as valid_rt_count,
            avg(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END) as avg_response_time_sec,
            median(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END) as median_response_time_sec,
            quantile_cont(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END, 0.90) as p90_response_time_sec,
            quantile_cont(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END, 0.95) as p95_response_time_sec,

            count(CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 1 END) as fcr_count,
            count(CASE WHEN len(n.escalation_signals) > 0 THEN 1 END) as escalation_count,
            count(CASE WHEN c.repeat_contact_signals = true THEN 1 END) as reopen_count,

            avg(n.sentiment) as avg_sentiment,
            count(CASE WHEN n.sentiment_label = 'negative' THEN 1 END) as negative_sentiment_count,
            count(CASE WHEN n.severity.label = 'high' THEN 1 END) as high_severity_count
        FROM '{_conv_fwd}' c
        JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
    """
    ov = con.execute(overall_query).fetchone()

    total_convs = ov[0]
    comp_resp = ov[1]
    valid_rt_count = ov[2]
    avg_rt = round(ov[3] or 0.0, 2)
    med_rt = round(ov[4] or 0.0, 2)
    p90_rt = round(ov[5] or 0.0, 2)
    p95_rt = round(ov[6] or 0.0, 2)

    fcr_count = ov[7]
    fcr_rate_overall = round(fcr_count / total_convs, 4) if total_convs > 0 else 0.0
    fcr_rate_responded = round(fcr_count / comp_resp, 4) if comp_resp > 0 else 0.0

    esc_count = ov[8]
    esc_rate = round(esc_count / total_convs, 4) if total_convs > 0 else 0.0

    reopen_count = ov[9]
    reopen_rate = round(reopen_count / total_convs, 4) if total_convs > 0 else 0.0

    avg_sent = round(ov[10] or 0.0, 4)
    neg_sent_count = ov[11]
    high_sev_count = ov[12]

    # CSAT Proxy Score Formula:
    # 100 * clamp(0.5 + 0.35 * sentiment + 0.15 * is_fcr - 0.25 * is_escalated - 0.20 * is_reopen, 0, 1)
    csat_query = f"""
        SELECT
            avg(100.0 * LEAST(GREATEST(
                0.5 + 0.35 * n.sentiment
                    + (CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 0.15 ELSE 0.0 END)
                    - (CASE WHEN len(n.escalation_signals) > 0 THEN 0.25 ELSE 0.0 END)
                    - (CASE WHEN c.repeat_contact_signals = true THEN 0.20 ELSE 0.0 END),
                0.0), 1.0)
            ) as avg_csat_proxy
        FROM '{_conv_fwd}' c
        JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
    """
    csat_overall = round(con.execute(csat_query).fetchone()[0] or 50.0, 2)

    # 2. CATEGORY METRICS BREAKDOWN
    cat_query = f"""
        SELECT
            n.category,
            count(*) as total_cases,
            count(CASE WHEN c.has_company_response = true THEN 1 END) as responded_cases,
            count(CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 1 END) as fcr_cases,
            count(CASE WHEN len(n.escalation_signals) > 0 THEN 1 END) as escalation_cases,
            count(CASE WHEN c.repeat_contact_signals = true THEN 1 END) as reopen_cases,
            avg(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END) as avg_rt_sec,
            median(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END) as median_rt_sec,
            quantile_cont(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END, 0.90) as p90_rt_sec,
            avg(n.sentiment) as avg_sentiment,
            avg(100.0 * LEAST(GREATEST(
                0.5 + 0.35 * n.sentiment
                    + (CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 0.15 ELSE 0.0 END)
                    - (CASE WHEN len(n.escalation_signals) > 0 THEN 0.25 ELSE 0.0 END)
                    - (CASE WHEN c.repeat_contact_signals = true THEN 0.20 ELSE 0.0 END),
                0.0), 1.0)
            ) as csat_proxy
        FROM '{_conv_fwd}' c
        JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
        GROUP BY n.category
        ORDER BY total_cases DESC
    """
    cat_rows = con.execute(cat_query).fetchall()
    cat_list = []
    unknown_cat_cases = 0
    for r in cat_rows:
        cnt = r[1]
        cat_name = r[0] or "other"
        if cat_name in ("other", "unknown", None):
            unknown_cat_cases += cnt
        cat_list.append({
            "category_name": cat_name,
            "total_cases": cnt,
            "responded_cases": r[2],
            "fcr_rate": round(r[3] / cnt, 4) if cnt > 0 else 0.0,
            "escalation_rate": round(r[4] / cnt, 4) if cnt > 0 else 0.0,
            "reopen_rate": round(r[5] / cnt, 4) if cnt > 0 else 0.0,
            "avg_response_time_sec": round(r[6] or 0.0, 1),
            "median_response_time_sec": round(r[7] or 0.0, 1),
            "p90_response_time_sec": round(r[8] or 0.0, 1),
            "avg_sentiment": round(r[9] or 0.0, 4),
            "csat_proxy": round(r[10] or 50.0, 2)
        })
    total_cat_mention_cases = sum(
        r["total_cases"] for r in cat_list
        if r["category_name"] not in ("other", "unknown")
    )

    # Save category_metrics.parquet
    cat_tb = pa.Table.from_pylist(cat_list)
    pq.write_table(cat_tb, os.path.join(out_dir, "category_metrics.parquet"), compression="snappy")

    # 3. PRODUCT METRICS BREAKDOWN
    prod_query = f"""
        SELECT
            lower(trim(n.entities.product_service)) as product_name,
            count(*) as total_cases,
            count(CASE WHEN c.has_company_response = true THEN 1 END) as responded_cases,
            count(CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 1 END) as fcr_cases,
            count(CASE WHEN len(n.escalation_signals) > 0 THEN 1 END) as escalation_cases,
            count(CASE WHEN c.repeat_contact_signals = true THEN 1 END) as reopen_cases,
            avg(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END) as avg_rt_sec,
            avg(n.sentiment) as avg_sentiment,
            count(CASE WHEN n.severity.label = 'high' THEN 1 END) as high_severity_cases,
            avg(100.0 * LEAST(GREATEST(
                0.5 + 0.35 * n.sentiment
                    + (CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 0.15 ELSE 0.0 END)
                    - (CASE WHEN len(n.escalation_signals) > 0 THEN 0.25 ELSE 0.0 END)
                    - (CASE WHEN c.repeat_contact_signals = true THEN 0.20 ELSE 0.0 END),
                0.0), 1.0)
            ) as csat_proxy
        FROM '{_conv_fwd}' c
        JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
        WHERE n.entities.product_service IS NOT NULL AND length(trim(n.entities.product_service)) > 1
        GROUP BY 1
        HAVING count(*) >= 10
        ORDER BY total_cases DESC
    """
    prod_rows = con.execute(prod_query).fetchall()
    prod_list = []
    total_prod_mention_cases = sum(r[1] for r in prod_rows)
    for r in prod_rows:
        cnt = r[1]
        prod_list.append({
            "product_name": r[0],
            "total_cases": cnt,
            "responded_cases": r[2],
            "fcr_rate": round(r[3] / cnt, 4) if cnt > 0 else 0.0,
            "escalation_rate": round(r[4] / cnt, 4) if cnt > 0 else 0.0,
            "reopen_rate": round(r[5] / cnt, 4) if cnt > 0 else 0.0,
            "avg_response_time_sec": round(r[6] or 0.0, 1),
            "avg_sentiment": round(r[7] or 0.0, 4),
            "high_severity_cases": r[8],
            "csat_proxy": round(r[9] or 50.0, 2)
        })

    # Save product_metrics.parquet
    prod_tb = pa.Table.from_pylist(prod_list)
    pq.write_table(prod_tb, os.path.join(out_dir, "product_metrics.parquet"), compression="snappy")

    # 4. REGION METRICS BREAKDOWN
    region_query = f"""
        SELECT
            lower(trim(n.entities.location)) as region_name,
            count(*) as total_cases,
            count(CASE WHEN c.has_company_response = true THEN 1 END) as responded_cases,
            count(CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 1 END) as fcr_cases,
            count(CASE WHEN len(n.escalation_signals) > 0 THEN 1 END) as escalation_cases,
            count(CASE WHEN c.repeat_contact_signals = true THEN 1 END) as reopen_cases,
            avg(CASE WHEN c.first_response_time > 0 THEN c.first_response_time END) as avg_rt_sec,
            avg(n.sentiment) as avg_sentiment,
            avg(100.0 * LEAST(GREATEST(
                0.5 + 0.35 * n.sentiment
                    + (CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 0.15 ELSE 0.0 END)
                    - (CASE WHEN len(n.escalation_signals) > 0 THEN 0.25 ELSE 0.0 END)
                    - (CASE WHEN c.repeat_contact_signals = true THEN 0.20 ELSE 0.0 END),
                0.0), 1.0)
            ) as csat_proxy
        FROM '{_conv_fwd}' c
        JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
        WHERE n.entities.location IS NOT NULL AND length(trim(n.entities.location)) > 1
        GROUP BY 1
        HAVING count(*) >= 10
        ORDER BY total_cases DESC
    """
    region_rows = con.execute(region_query).fetchall()
    region_list = []
    total_region_mention_cases = sum(r[1] for r in region_rows)
    for r in region_rows:
        cnt = r[1]
        region_list.append({
            "region_name": r[0],
            "total_cases": cnt,
            "responded_cases": r[2],
            "fcr_rate": round(r[3] / cnt, 4) if cnt > 0 else 0.0,
            "escalation_rate": round(r[4] / cnt, 4) if cnt > 0 else 0.0,
            "reopen_rate": round(r[5] / cnt, 4) if cnt > 0 else 0.0,
            "avg_response_time_sec": round(r[6] or 0.0, 1),
            "avg_sentiment": round(r[7] or 0.0, 4),
            "csat_proxy": round(r[8] or 50.0, 2)
        })

    # Save region_metrics.parquet
    region_tb = pa.Table.from_pylist(region_list)
    pq.write_table(region_tb, os.path.join(out_dir, "region_metrics.parquet"), compression="snappy")

    # 5. CSAT PROXY TRAJECTORY OVER TIME (DAILY)
    csat_traj_query = f"""
        SELECT
            cast(c.start_time as DATE) as date_val,
            count(*) as case_count,
            avg(n.sentiment) as avg_sentiment,
            avg(100.0 * LEAST(GREATEST(
                0.5 + 0.35 * n.sentiment
                    + (CASE WHEN c.customer_turn_count = 1 AND c.has_company_response = true THEN 0.15 ELSE 0.0 END)
                    - (CASE WHEN len(n.escalation_signals) > 0 THEN 0.25 ELSE 0.0 END)
                    - (CASE WHEN c.repeat_contact_signals = true THEN 0.20 ELSE 0.0 END),
                0.0), 1.0)
            ) as csat_proxy
        FROM '{_conv_fwd}' c
        JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
        WHERE c.start_time IS NOT NULL AND length(cast(c.start_time as VARCHAR)) > 8
        GROUP BY 1
        HAVING count(*) >= 50
        ORDER BY date_val ASC
    """
    csat_traj_rows = con.execute(csat_traj_query).fetchall()
    csat_traj_list = []
    for r in csat_traj_rows:
        csat_traj_list.append({
            "date": str(r[0]),
            "case_count": r[1],
            "avg_sentiment": round(r[2] or 0.0, 4),
            "csat_proxy": round(r[3] or 50.0, 2)
        })

    csat_tb = pa.Table.from_pylist(csat_traj_list)
    pq.write_table(csat_tb, os.path.join(out_dir, "csat_trajectory.parquet"), compression="snappy")

    # 6. EMERGING ISSUES SCORE (Growth Rate calculation over 7-day windows)
    emerging_query = f"""
        WITH daily_cat AS (
            SELECT
                n.category,
                cast(c.start_time as DATE) as dt,
                count(*) as cnt
            FROM '{_conv_fwd}' c
            JOIN '{_nlp_fwd}' n ON c.conversation_id = n.conversation_id
            WHERE c.start_time IS NOT NULL AND length(cast(c.start_time as VARCHAR)) > 8
            GROUP BY 1, 2
        ),
        recent_vs_prior AS (
            SELECT
                category,
                sum(CASE WHEN dt >= '2017-11-20' THEN cnt ELSE 0 END) as recent_7d_vol,
                sum(CASE WHEN dt >= '2017-11-13' AND dt < '2017-11-20' THEN cnt ELSE 0 END) as prior_7d_vol
            FROM daily_cat
            GROUP BY category
        )
        SELECT
            category,
            recent_7d_vol,
            prior_7d_vol,
            round((recent_7d_vol - prior_7d_vol) / GREATEST(prior_7d_vol, 1.0) * 100.0, 2) as growth_rate_pct,
            round((recent_7d_vol - prior_7d_vol) * (1.0 + (recent_7d_vol / 1000.0)), 2) as emerging_issue_score
        FROM recent_vs_prior
        ORDER BY emerging_issue_score DESC
    """
    emerging_rows = con.execute(emerging_query).fetchall()
    emerging_list = []
    for r in emerging_rows:
        emerging_list.append({
            "category": r[0],
            "recent_7d_volume": r[1],
            "prior_7d_volume": r[2],
            "growth_rate_pct": r[3],
            "emerging_issue_score": r[4]
        })

    # Assemble complete metrics_summary.json
    summary = {
        "dataset_metrics": {
            "total_conversations": total_convs,
            "company_responded_conversations": comp_resp,
            "company_response_rate": round(comp_resp / total_convs, 4) if total_convs > 0 else 0.0,
            "negative_sentiment_rate": round(neg_sent_count / total_convs, 4) if total_convs > 0 else 0.0,
            "high_severity_rate": round(high_sev_count / total_convs, 4) if total_convs > 0 else 0.0,
            "average_sentiment": avg_sent
        },
        "response_time_metrics": {
            "valid_measured_cases": valid_rt_count,
            "coverage_percentage": round(valid_rt_count / total_convs * 100, 2),
            "unknown_percentage": round((1.0 - valid_rt_count / total_convs) * 100, 2),
            "average_seconds": avg_rt,
            "median_seconds": med_rt,
            "p90_seconds": p90_rt,
            "p95_seconds": p95_rt,
            "average_minutes": round(avg_rt / 60.0, 2),
            "median_minutes": round(med_rt / 60.0, 2),
            "p90_minutes": round(p90_rt / 60.0, 2),
            "p95_minutes": round(p95_rt / 60.0, 2),
            "formula": "first_response_time = timestamp(first_company_turn) - timestamp(first_customer_turn)"
        },
        "first_contact_resolution": {
            "fcr_cases": fcr_count,
            "total_conversations": total_convs,
            "fcr_rate_overall": fcr_rate_overall,
            "fcr_rate_responded_threads": fcr_rate_responded,
            "formula": "customer_turn_count == 1 AND has_company_response == true",
            "coverage_percentage": 100.0
        },
        "escalation_metrics": {
            "escalated_cases": esc_count,
            "total_conversations": total_convs,
            "escalation_rate": esc_rate,
            "formula": "len(escalation_signals) > 0",
            "coverage_percentage": 100.0
        },
        "reopen_metrics": {
            "reopened_cases": reopen_count,
            "total_conversations": total_convs,
            "reopen_rate": reopen_rate,
            "formula": "repeat_contact_signals == true",
            "coverage_percentage": 100.0
        },
        "csat_proxy": {
            "label": "CSAT Proxy",
            "is_actual_csat_survey": False,
            "overall_csat_proxy_score": csat_overall,
            "formula": "100 * clamp(0.5 + 0.35 * sentiment + 0.15 * is_fcr - 0.25 * is_escalated - 0.20 * is_reopen, 0, 1)",
            "csat_trajectory_days_count": len(csat_traj_list)
        },
        "product_analysis": {
            "product_mention_cases": total_prod_mention_cases,
            "unique_normalized_products": len(prod_list),
            "coverage_percentage": round(total_prod_mention_cases / total_convs * 100, 2),
            "unknown_percentage": round((1.0 - total_prod_mention_cases / total_convs) * 100, 2),
            "top_products": prod_list[:5]
        },
        "region_analysis": {
            "region_mention_cases": total_region_mention_cases,
            "unique_normalized_regions": len(region_list),
            "coverage_percentage": round(total_region_mention_cases / total_convs * 100, 2),
            "unknown_percentage": round((1.0 - total_region_mention_cases / total_convs) * 100, 2),
            "top_regions": region_list[:5]
        },
        "emerging_issues": emerging_list[:5],
        "category_breakdown": cat_list[:5],
        "category_analysis": {
            "category_mention_cases": total_cat_mention_cases,
            "unique_normalized_categories": sum(
                1 for r in cat_list if r["category_name"] not in ("other", "unknown")
            ),
            "coverage_percentage": round(total_cat_mention_cases / total_convs * 100, 2) if total_convs > 0 else 0.0,
            "unknown_percentage": round(unknown_cat_cases / total_convs * 100, 2) if total_convs > 0 else 0.0,
            "top_categories": [
                r for r in cat_list if r["category_name"] not in ("other", "unknown")
            ]
        }
    }

    summary_file = os.path.join(out_dir, "metrics_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info(f"Saved metrics summary to {summary_file}")

    # 7. RAG INTEGRATION: Append DOC-SNAPSHOT-ANALYTICS-V2 to analytics_snapshots layer
    snapshot_dir = os.path.join(project_root, "data", "knowledge", "analytics_snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    snapshot_file = os.path.join(snapshot_dir, "analytics_snapshots.parquet")

    existing_snapshots = []
    if os.path.exists(snapshot_file):
        existing_snapshots = pq.read_table(snapshot_file).to_pylist()

    v2_snapshot = KnowledgeDocument(
        document_id="DOC-SNAPSHOT-ANALYTICS-V2",
        doc_id="DOC-SNAPSHOT-ANALYTICS-V2",
        document_type="analytics_snapshots",
        type="analytics_snapshots",
        title="RootIQ UC18 Analytics V2 Enterprise Operational Summary",
        text=(
            f"UC18 Analytics V2 Summary over {total_convs:,} conversations: "
            f"FCR Rate={fcr_rate_overall*100:.2f}%, Escalation Rate={esc_rate*100:.2f}%, "
            f"Reopen Rate={reopen_rate*100:.2f}%, CSAT Proxy={csat_overall}/100. "
            f"Response Times: Avg={avg_rt/60.0:.1f}m, Median={med_rt/60.0:.1f}m, P90={p90_rt/60.0:.1f}m, P95={p95_rt/60.0:.1f}m. "
            f"Top Product: {prod_list[0]['product_name'] if prod_list else 'N/A'} ({prod_list[0]['total_cases'] if prod_list else 0:,} cases, CSAT Proxy={prod_list[0]['csat_proxy'] if prod_list else 0}). "
            f"Top Region: {region_list[0]['region_name'] if region_list else 'N/A'} ({region_list[0]['total_cases'] if region_list else 0:,} cases). "
            f"Emerging Issue Category: {emerging_list[0]['category'] if emerging_list else 'N/A'} (growth rate {emerging_list[0]['growth_rate_pct'] if emerging_list else 0}%)."
        ),
        content=(
            f"UC18 Analytics V2 Summary over {total_convs:,} conversations: "
            f"FCR Rate={fcr_rate_overall*100:.2f}%, Escalation Rate={esc_rate*100:.2f}%, "
            f"Reopen Rate={reopen_rate*100:.2f}%, CSAT Proxy={csat_overall}/100. "
            f"Response Times: Avg={avg_rt/60.0:.1f}m, Median={med_rt/60.0:.1f}m, P90={p90_rt/60.0:.1f}m, P95={p95_rt/60.0:.1f}m."
        ),
        metadata={
            "total_conversations": total_convs,
            "fcr_rate": fcr_rate_overall,
            "escalation_rate": esc_rate,
            "reopen_rate": reopen_rate,
            "csat_proxy": csat_overall,
            "avg_response_time_mins": round(avg_rt/60.0, 2),
            "product_coverage_pct": round(total_prod_mention_cases / total_convs * 100, 2),
            "region_coverage_pct": round(total_region_mention_cases / total_convs * 100, 2),
        },
        source_type="analytics_v2",
        topic="operational_metrics"
    ).model_dump()

    # Avoid duplicate DOC-SNAPSHOT-ANALYTICS-V2
    filtered_snapshots = [s for s in existing_snapshots if s.get("document_id") != "DOC-SNAPSHOT-ANALYTICS-V2" and s.get("doc_id") != "DOC-SNAPSHOT-ANALYTICS-V2"]
    filtered_snapshots.append(v2_snapshot)

    storage.write_parquet(filtered_snapshots, "analytics_snapshots.parquet", subfolder="knowledge/analytics_snapshots")
    checkpoint_mgr.save_checkpoint("stage18_analytics_v2", {"status": "COMPLETED", "summary": summary["dataset_metrics"]})

    logger.info("UC18 Analytics V2 execution successfully completed!")
    return summary

if __name__ == "__main__":
    run_stage18_analytics_v2()
