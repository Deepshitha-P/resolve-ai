"""
stage07_issue_clusters.py ΓÇö Change 1 & 2 surgical additions:
  ΓÇó After KMeans label assignment, members are re-grouped by (product, region,
    dominant_category) as the final cluster key.
  ΓÇó escalation_rate_component computed per PRT group from trajectory.escalation_flag.
  ΓÇó Updated pain score formula (5 weights):
      pain = 100 ├ù (0.30├ùvolume + 0.20├ùneg_sent + 0.20├ùsev + 0.15├ùgrowth + 0.15├ùesc_rate)
  ΓÇó cluster_name, summary, incident_id use {product}-{region}-{topic} format.
  ΓÇó product and region added to IssueCluster and incident_candidates.
"""
from collections import Counter
from typing import Dict, List, Optional
from datetime import datetime
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from pipeline.config_loader import load_config
from pipeline.logger import get_logger
from pipeline.schemas import IssueCluster, PainPointScore

logger = get_logger("Stage07_IssueClusters")


def cluster_issues(
    conversations: Optional[List[Dict]] = None,
    config: Optional[Dict] = None,
    n_clusters: int = 5,
    incident_size_threshold: int = 4,
) -> Dict:
    cfg = config or load_config()
    cluster_cfg = cfg.get("clustering", {})
    k_clusters  = cluster_cfg.get("n_clusters", n_clusters)
    max_sample  = cluster_cfg.get("max_sample_size", 10000)

    from pipeline.storage import StorageEngine
    import duckdb, os
    storage = StorageEngine(cfg)

    conv_file = storage.get_parquet_path("conversations.parquet", subfolder="conversations").replace("\\", "/")
    nlp_file  = storage.get_parquet_path("nlp_results.parquet",   subfolder="nlp").replace("\\", "/")

    if conversations is None and os.path.exists(conv_file) and os.path.exists(nlp_file):
        con = duckdb.connect()
        total_convs = con.execute(f"SELECT count(*) FROM '{conv_file}'").fetchone()[0]
        sample_rows = con.execute(f"""
            SELECT c.conversation_id, c.customer_turn_count, c.company_turn_count,
                   c.has_company_response, c.start_time,
                   n.intent, n.category, n.subcategory, n.sentiment_label,
                   n.severity.label as severity_label, n.escalation_signals,
                   COALESCE(n.product, 'unknown') as product,
                   COALESCE(n.region,  'unknown') as region,
                   TRY_CAST(n.trajectory.escalation_flag AS BOOLEAN) as traj_esc
            FROM '{conv_file}' c
            JOIN '{nlp_file}' n ON c.conversation_id = n.conversation_id
            LIMIT {max_sample}
        """).fetchall()
        sampled_convs = [
            {
                "conversation_id": r[0],
                "customer_turn_count": r[1],
                "company_turn_count": r[2],
                "has_company_response": r[3],
                "start_time": r[4],
                "product": r[11] or "unknown",
                "region":  r[12] or "unknown",
                "nlp": {
                    "intent": r[5], "category": r[6], "subcategory": r[7],
                    "sentiment_label": r[8], "severity": {"label": r[9]},
                    "escalation_signals": r[10] or [],
                    "product": r[11] or "unknown",
                    "region":  r[12] or "unknown",
                    "trajectory": {"escalation_flag": bool(r[13]) if r[13] is not None else False},
                },
                "turns": [{"text": r[5] or "issue"}],
            }
            for r in sample_rows
        ]
    else:
        conversations = conversations or []
        total_convs   = len(conversations)
        sampled_convs = conversations[:max_sample]

    is_sample_based = total_convs > max_sample
    logger.info(
        f"Clustering representative sample of {len(sampled_convs):,} "
        f"out of {total_convs:,} conversations into {k_clusters} topic clusters "
        f"then re-keying by (product├ùregion├ùtopic)..."
    )

    if not sampled_convs:
        return {"clusters": {}, "incident_candidates": []}

    # ΓöÇΓöÇ TF-IDF + KMeans (topic discovery ΓÇö unchanged) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    texts = []
    for c in sampled_convs:
        turns  = c.get("turns") or []
        t_text = turns[0]["text"] if turns else "empty"
        texts.append(t_text)

    vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
    X = vectorizer.fit_transform(texts)

    k = min(k_clusters, len(sampled_convs))
    model  = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=100, n_init=3)
    labels = model.fit_predict(X)

    terms            = vectorizer.get_feature_names_out()
    order_centroids  = model.cluster_centers_.argsort()[:, ::-1]
    total_sampled    = len(sampled_convs)

    # ΓöÇΓöÇ Re-group by (product, region, dominant_topic) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # First pass: collect per-label members and top terms
    label_members: Dict[int, List[Dict]] = {cid: [] for cid in range(k)}
    for i, c in enumerate(sampled_convs):
        label_members[labels[i]].append(c)

    # Build (product, region, topic) ΓåÆ merged member list
    prt_groups: Dict[str, List[Dict]] = {}
    prt_keywords:  Dict[str, List[str]] = {}

    for cid in range(k):
        members   = label_members[cid]
        top_terms = [terms[t] for t in order_centroids[cid, :5]] if terms.size > 0 else ["general"]
        if not members:
            continue
        cat_counter = Counter(m.get("nlp", {}).get("category", "other") for m in members)
        dominant_cat = cat_counter.most_common(1)[0][0]

        # Sub-group by (product, region, subtype) within this KMeans topic cluster
        prs_groups: Dict = {}
        for m in members:
            prod = m.get("product") or m.get("nlp", {}).get("product") or "unknown"
            reg  = m.get("region")  or m.get("nlp", {}).get("region")  or "unknown"
            sub  = m.get("subtype") or m.get("nlp", {}).get("subtype") or "general"
            prs_key = f"{prod}|{reg}|{sub}"
            prs_groups.setdefault(prs_key, []).append(m)

        for prs_key, prs_members in prs_groups.items():
            prod, reg, sub = prs_key.split("|", 2)
            prts_key = f"{prod}|{reg}|{dominant_cat}|{sub}"
            if prts_key not in prt_groups:
                prt_groups[prts_key] = []
                prt_keywords[prts_key] = top_terms
            prt_groups[prts_key].extend(prs_members)

    # ΓöÇΓöÇ Max cluster size for volume normalisation ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    max_cluster_size = max((len(m) for m in prt_groups.values()), default=1)

    incidents    = []
    clusters_dict = {}

    for flat_idx, (prt_key, members) in enumerate(prt_groups.items()):
        product, region, dominant_cat, subtype = prt_key.split("|", 3)
        top_terms = prt_keywords.get(prt_key, ["general"])

        intent_counter  = Counter(m.get("nlp", {}).get("intent", "other") for m in members)
        dominant_intent = intent_counter.most_common(1)[0][0] if members else "other"
        sentiment_dist  = Counter(m.get("nlp", {}).get("sentiment_label", "neutral") for m in members)
        severity_dist   = Counter(m.get("nlp", {}).get("severity", {}).get("label", "medium") for m in members)

        # ΓöÇΓöÇ Pain score (5-weight formula, Change 2) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        volume_comp    = round(len(members) / max(max_cluster_size, 1), 4)
        neg_count      = sentiment_dist.get("negative", 0)
        neg_sent_comp  = round(neg_count / max(len(members), 1), 4)
        high_critical  = severity_dist.get("high", 0) + severity_dist.get("critical", 0)
        sev_comp       = round(high_critical / max(len(members), 1), 4)

        # escalation_rate_component: fraction with trajectory escalation_flag
        esc_flags = [m.get("nlp", {}).get("trajectory", {}).get("escalation_flag", False) for m in members]
        esc_rate_comp = round(sum(esc_flags) / max(len(members), 1), 4)

        # Growth from timestamps
        timestamps = []
        for m in members:
            st = m.get("start_time")
            if st:
                try:
                    timestamps.append(datetime.fromisoformat(st.replace("Z", "+00:00")))
                except Exception:
                    pass

        if len(timestamps) >= 10:
            timestamps.sort()
            mid_idx     = len(timestamps) // 2
            first_half  = mid_idx
            second_half = len(timestamps) - mid_idx
            growth_comp     = round(min(max(second_half / max(first_half, 1) / 2.0, 0.0), 1.0), 4)
            growth_is_fallback = False
        else:
            growth_comp        = 0.5
            growth_is_fallback = True

        # New 5-weight formula: 0.30 vol + 0.20 neg_sent + 0.20 sev + 0.15 growth + 0.15 esc_rate
        pain_score = round(
            100.0 * (
                0.30 * volume_comp +
                0.20 * neg_sent_comp +
                0.20 * sev_comp +
                0.15 * growth_comp +
                0.15 * esc_rate_comp
            ),
            1,
        )

        pain_obj = PainPointScore(
            pain_score=pain_score,
            volume_component=volume_comp,
            negative_sentiment_component=neg_sent_comp,
            severity_component=sev_comp,
            growth_component=growth_comp,
            escalation_rate_component=esc_rate_comp,  # Change 2
        )

        area_counter = Counter(m.get("region") or m.get("area", "Global") for m in members)
        dominant_area, dominant_area_count = area_counter.most_common(1)[0] if members else ("Global", 0)

        is_incident = (
            len(members) >= incident_size_threshold
            and (dominant_area_count / max(len(members), 1)) >= 0.5
        )

        sample_prefix = f" (Sampled {len(members):,}/{total_sampled:,})" if is_sample_based else ""
        # Change 1: cluster_name uses product-region-topic format
        cluster_name = f"{product.title()}-{region.title()}-{dominant_cat.title()} Issues{sample_prefix}"
        summary = (
            f"Cluster of {len(members):,} complaints regarding '{dominant_cat}' "
            f"for product '{product}' in region '{region}' "
            f"(esc_rate={esc_rate_comp*100:.1f}%, pain={pain_score}/100)."
        )

        cluster_obj = IssueCluster(
            cluster_id=flat_idx,
            cluster_name=cluster_name,
            summary=summary,
            volume=len(members),
            percentage=round(len(members) / max(total_sampled, 1) * 100, 2),
            dominant_topic=dominant_cat,
            dominant_intent=dominant_intent,
            sentiment_distribution=dict(sentiment_dist),
            severity_distribution=dict(severity_dist),
            growth_rate=growth_comp,
            representative_case_ids=[m["conversation_id"] for m in members[:5]],
            keywords=top_terms,
            regions=[region],
            products=[product],
            period="overall",
            pain_point_impact=pain_obj,
        )

        cdict = cluster_obj.model_dump()
        cdict["product"]           = product          # Change 1
        cdict["region"]            = region           # Change 1
        cdict["topic"]             = dominant_cat     # Change 1
        cdict["subtype"]           = subtype          # Added
        cdict["prt_key"]           = prt_key
        cdict["is_sample_based"]   = is_sample_based
        cdict["sample_volume"]     = total_sampled
        cdict["total_conversations"] = total_convs
        cdict["growth_is_fallback"] = growth_is_fallback
        cdict["escalation_rate"]   = esc_rate_comp    # Change 2
        clusters_dict[flat_idx]    = cdict

        if is_incident or pain_score >= 65.0:
            incidents.append({
                "incident_id":            f"INC-{2000 + flat_idx}",
                "title":                  f"{product.title()} {dominant_cat} incident in {region.title()}",
                "cluster_id":             flat_idx,
                "affected_complaint_count": len(members),
                "product":                product,           # Change 1
                "region":                 region,            # Change 1
                "topic":                  dominant_cat,      # Change 1
                "subtype":                subtype,           # Added
                "area":                   region,            # backward compat
                "category":               dominant_cat,      # backward compat
                "pain_score":             pain_score,
                "escalation_rate":        esc_rate_comp,     # Change 2
                "keywords":               top_terms,
                "member_ids":             [m["conversation_id"] for m in members[:10]],
            })

    logger.info(
        f"[STAGE 7 ISSUE CLUSTERS] Generated {len(clusters_dict)} PRT clusters "
        f"({len(incidents)} potential incidents). Sample-based: {is_sample_based}."
    )
    return {"clusters": clusters_dict, "incident_candidates": incidents}


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    from stage03_conversations import build_conversations
    from stage04_nlp import enrich_with_nlp

    convs = enrich_with_nlp(build_conversations(clean_batch(generate_raw_complaints(50))))
    result = cluster_issues(convs)
    for cid, c in result["clusters"].items():
        print(c["prt_key"], "| pain:", c["pain_point_impact"]["pain_score"], "| esc:", c["escalation_rate"])
