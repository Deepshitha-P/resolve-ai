import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pipeline.schemas import NLPResult, NLPSeverity
from pipeline.logger import get_logger

logger = get_logger("NLPEngine")

TAXONOMY_KEYWORDS = {
    "payment": ["payment", "pay", "charged", "card", "transaction", "amount", "debit", "credit"],
    "refund": ["refund", "money back", "reimburse", "return funds"],
    "billing": ["bill", "invoice", "overcharged", "fee", "cost", "charge"],
    "network": ["network", "internet", "broadband", "wifi", "signal", "disconnection", "connection", "data"],
    "service_outage": ["outage", "down", "offline", "no service", "crash", "blackout"],
    "account": ["account", "profile", "user", "lock", "suspended", "disabled", "fraudulent"],
    "authentication": ["login", "password", "otp", "2fa", "sign in", "access"],
    "delivery": [
        "delivery", "delivered", "shipping", "package", "order", "sim card", "courier",
        "address", "wrong address", "arrived", "item not received", "ups", "fedex"
    ],
    "technical_support": [
        "error", "bug", "issue", "help", "broken", "fail", "failed", "glitch",
        "update", "software", "export", "working", "doesn't work", "does not work", "breaks"
    ],
    "complaint_followup": ["again", "still", "no response", "ignored", "sent several", "following up"],
    "device_hardware": ["battery", "screen", "device", "hardware", "phone", "button", "charge", "charging"],
    "travel_flight": ["flight", "flights", "airline", "train", "booking", "itinerary", "ticket", "seat", "travelling"],
    "store_operations": ["store", "staff", "stock", "out of stock", "in store", "rep", "clerk", "queue", "bakery"],
    "feature_request": ["feature", "export", "supported", "suggestion", "filter", "option"],
}

SUBCATEGORY_TAXONOMY = {
    "payment": {
        "payment_failed": ["failed", "declined", "unsuccessful", "error paying", "could not pay", "payment failed"],
        "duplicate_charge": ["charged twice", "double charge", "charged 2x", "duplicate charge"],
        "charged_but_order_failed": ["money deducted", "charged but", "debited but", "taken but no order"],
        "payment_pending": ["pending", "processing payment", "stuck payment"],
    },
    "refund": {
        "refund_pending": ["refund processing", "refund pending", "status of refund"],
        "refund_not_received": ["refund not received", "haven't received refund", "no refund", "where is refund", "still no refund"],
        "refund_request": ["want refund", "request refund", "cancel and refund", "give money back", "need refund"],
    },
    "billing": {
        "incorrect_bill": ["wrong bill", "incorrect bill", "bill error"],
        "unexpected_charge": ["unexpected charge", "unknown fee", "hidden charge", "extra fee"],
        "overcharge": ["overcharged", "charged more", "higher than usual", "excessive charge"],
    },
    "network": {
        "internet_down": ["down", "no internet", "broadband down", "no connection", "disconnected", "offline"],
        "slow_connection": ["slow", "speed", "buffering", "lag", "throttled", "low speed"],
        "intermittent_connection": ["keeps dropping", "intermittent", "disconnecting", "unstable", "on and off"],
    },
    "service_outage": {
        "widespread_outage": ["outage", "blackout", "area outage", "major outage", "service outage"],
        "app_outage": ["app down", "server down", "system down", "site down"],
    },
    "delivery": {
        "late_delivery": ["late", "delayed", "delay", "taking long", "overdue"],
        "missing_delivery": ["not delivered", "missing package", "lost delivery", "never arrived"],
        "tracking_issue": ["tracking", "no update", "status", "courier tracking"],
        "address_issue": ["wrong address", "delivery address", "dispatch address"],
    },
    "technical_support": {
        "app_issue": ["app crash", "app freezing", "app error", "mobile app", "application"],
        "software_bug": ["bug", "glitch", "error code", "broken feature"],
        "update_issue": ["update failed", "cannot update", "new update"],
        "feature_not_working": ["not working", "fails to load", "doesn't work", "cannot click"],
    },
    "complaint_followup": {
        "no_response": ["no response", "no reply", "ignored", "no one responded"],
        "unresolved_complaint": ["still unresolved", "not fixed yet", "issue remains", "still facing"],
        "repeat_complaint": ["again", "second time", "third time", "repeated issue"],
        "escalation_request": ["escalate", "manager", "supervisor", "higher authority"],
    },
    "account": {
        "account_locked": ["locked", "suspended", "disabled", "cannot access account"],
        "account_details": ["profile", "update details", "account settings"],
    },
    "authentication": {
        "login_failed": ["cannot login", "login error", "sign in failed"],
        "otp_issue": ["otp", "2fa", "verification code", "auth code"],
    },
    "device_hardware": {
        "battery_issue": ["battery", "charging", "drain", "power"],
        "hardware_fault": ["screen", "broken hardware", "button", "faulty device"],
    },
    "travel_flight": {
        "flight_cancellation": ["cancelled flight", "flight cancel", "rescheduled"],
        "booking_issue": ["ticket", "seat", "itinerary", "booking error"],
    },
    "store_operations": {
        "staff_service": ["staff", "clerk", "rep", "rude service"],
        "stock_issue": ["out of stock", "in store", "queue", "bakery"],
    },
    "feature_request": {
        "new_feature": ["feature request", "add option", "suggestion", "would be nice"],
    },
    "other": {
        "general_query": ["info", "inquiry", "help"],
    }
}

PROBLEM_TYPE_MAP = {
    "network": "service_failure",
    "service_outage": "service_failure",
    "payment": "payment_failure",
    "delivery": "delivery_failure",
    "account": "access_problem",
    "authentication": "access_problem",
    "billing": "billing_problem",
    "refund": "billing_problem",
    "technical_support": "technical_failure",
    "device_hardware": "technical_failure",
    "complaint_followup": "complaint",
    "feature_request": "feature_request",
    "travel_flight": "information_request",
    "store_operations": "information_request",
    "other": "unknown",
}

EMOTION_KEYWORDS = {
    "anger": ["furious", "terrible", "worst", "unacceptable", "hate", "scam", "disgrace", "ridiculous"],
    "frustration": ["frustrated", "annoying", "useless", "lying", "liars", "fed up", "waste"],
    "satisfaction": ["thanks", "thank you", "great", "awesome", "fixed", "resolved", "helpful"],
}

URGENCY_PATTERNS = [
    (re.compile(r"asap|immediately|urgently|emergency", re.IGNORECASE), "critical"),
    (re.compile(r"today|worst|3 days|48 hours|no response", re.IGNORECASE), "high"),
    (re.compile(r"please|help|waiting", re.IGNORECASE), "medium"),
]

TEMPORAL_PATTERNS = [
    re.compile(r"(\d+)\s*days?", re.IGNORECASE),
    re.compile(r"(\d+)\s*hours?", re.IGNORECASE),
    re.compile(r"(\d+)\s*weeks?", re.IGNORECASE),
    re.compile(r"(\d+)\s*months?", re.IGNORECASE),
    re.compile(r"since\s+yesterday", re.IGNORECASE),
    re.compile(r"for\s+a\s+week", re.IGNORECASE),
    re.compile(r"still\s+waiting", re.IGNORECASE),
    re.compile(r"within\s+\d+\s*hours?", re.IGNORECASE),
    re.compile(r"48\s*hours?", re.IGNORECASE),
    re.compile(r"3\s*days?", re.IGNORECASE),
]

ESCALATION_PATTERNS = {
    "repeat_contact": re.compile(r"sent\s+several|again|multiple\s+times|third\s+time|second\s+time|3rd\s+call|3\s+times|called\s+twice", re.IGNORECASE),
    "multiple_complaints": re.compile(r"several\s+complaints|posted\s+before|tweeted\s+yesterday|again\s+today", re.IGNORECASE),
    "manager_request": re.compile(r"manager|supervisor|head\s+of|escalate", re.IGNORECASE),
    "explicit_escalation": re.compile(r"escalat|legal|consumer\s+court|lawyer|ombudsman|sue", re.IGNORECASE),
    "no_response_language": re.compile(r"no\s+one\s+is\s+responding|no\s+reply|ignored|unanswered|no\s+response", re.IGNORECASE),
    "still_unresolved_language": re.compile(r"still\s+not\s+working|still\s+down|still\s+waiting|not\s+resolved|unresolved", re.IGNORECASE),
}

RESOLUTION_PATTERNS = {
    "customer_claimed_unresolved": re.compile(r"still\s+not\s+working|still\s+broken|not\s+resolved|not\s+fixed|issue\s+remains|unresolved", re.IGNORECASE),
    "customer_claimed_resolved": re.compile(r"working\s+now|fixed\s+now|issue\s+resolved|thanks\s+for\s+fixing|all\s+good\s+now|resolved", re.IGNORECASE),
    "waiting_for_response": re.compile(r"waiting\s+for\s+reply|awaiting\s+response|please\s+respond|anyone\s+there|no\s+reply", re.IGNORECASE),
    "waiting_for_resolution": re.compile(r"waiting\s+for\s+fix|when\s+will\s+it\s+be\s+fixed|expecting\s+resolution", re.IGNORECASE),
}


class NLPProvider(ABC):
    @abstractmethod
    def analyze_text(self, text: str, case_id: Optional[str] = None, conversation_id: Optional[str] = None) -> NLPResult:
        pass


class LocalNLPProvider(NLPProvider):
    """
    Local NLP Engine (v1.2-local) with dynamic evidence-based confidence scoring,
    extended TWCS taxonomy, subcategories, problem_type classification,
    evidence-based entity extraction, resolution-language signals, and evidence spans.
    """
    def __init__(self, taxonomy: Optional[List[str]] = None):
        self.taxonomy = taxonomy or list(TAXONOMY_KEYWORDS.keys())

    def analyze_text(self, text: str, case_id: Optional[str] = None, conversation_id: Optional[str] = None) -> NLPResult:
        clean = text.lower()
        evidence_spans: Dict[str, Any] = {}

        # 1. Category Scoring
        cat_scores = {}
        cat_evidence = {}
        for cat, kws in TAXONOMY_KEYWORDS.items():
            matches = [kw for kw in kws if kw in clean]
            cat_scores[cat] = len(matches)
            if matches:
                cat_evidence[cat] = matches[0]

        max_score = max(cat_scores.values()) if cat_scores else 0

        if max_score > 0:
            best_cat = max(cat_scores, key=cat_scores.get)
            evidence_spans["category_keyword"] = cat_evidence.get(best_cat)
        else:
            best_cat = "other"

        # 2. Subcategory Scoring
        best_subcat = None
        subcat_dict = SUBCATEGORY_TAXONOMY.get(best_cat, {})
        subcat_scores = {}
        subcat_evidence = {}
        for subcat, kws in subcat_dict.items():
            matches = []
            for kw in kws:
                if " " in kw:
                    parts = kw.split()
                    if kw in clean or (len(parts) == 2 and re.search(r"\b" + re.escape(parts[0]) + r"\b.*\b" + re.escape(parts[1]) + r"\b", clean)):
                        matches.append(kw)
                elif kw in clean:
                    matches.append(kw)
            subcat_scores[subcat] = len(matches)
            if matches:
                subcat_evidence[subcat] = matches[0]

        max_sub_score = max(subcat_scores.values()) if subcat_scores else 0
        if max_sub_score > 0:
            best_subcat = max(subcat_scores, key=subcat_scores.get)
            evidence_spans["subcategory_keyword"] = subcat_evidence.get(best_subcat)
            intent = best_subcat

        else:
            best_subcat = None  # Insufficient evidence -> MUST BE NULL
            intent = best_cat

        # 3. Problem Type Mapping
        problem_type = PROBLEM_TYPE_MAP.get(best_cat, "unknown")

        # 4. Sentiment
        neg_words = [kw for kw in ["worst", "bad", "down", "fail", "failed", "error", "no", "never", "scam", "useless", "lies", "lying"] if kw in clean]
        pos_words = [kw for kw in ["good", "great", "thanks", "helpful", "resolved", "fixed", "nice"] if kw in clean]
        total_tokens = max(len(clean.split()), 1)

        if len(pos_words) > len(neg_words):
            sentiment = min(round((len(pos_words) - len(neg_words)) / total_tokens * 3, 2), 1.0)
            sentiment_label = "positive"
        elif len(neg_words) > len(pos_words):
            sentiment = max(round(-(len(neg_words) - len(pos_words)) / total_tokens * 3, 2), -1.0)
            sentiment_label = "negative"
        else:
            sentiment = 0.0
            sentiment_label = "neutral"

        # 5. Emotion
        emotion = "neutral"
        for em, kws in EMOTION_KEYWORDS.items():
            matches = [kw for kw in kws if kw in clean]
            if matches:
                emotion = em
                evidence_spans["emotion_keyword"] = matches[0]
                break

        # 6. Urgency
        urgency = "low"
        for pattern, urg_val in URGENCY_PATTERNS:
            m = pattern.search(clean)
            if m:
                urgency = urg_val
                evidence_spans["urgency_span"] = m.group(0)
                break

        # 7. Escalation Signals
        escalation_signals = []
        for esc_name, pat in ESCALATION_PATTERNS.items():
            m = pat.search(clean)
            if m:
                escalation_signals.append(esc_name)
                evidence_spans[f"escalation_{esc_name}"] = m.group(0)

        # 8. Resolution Signals
        resolution_signals = []
        for res_name, pat in RESOLUTION_PATTERNS.items():
            m = pat.search(clean)
            if m:
                resolution_signals.append(res_name)
                evidence_spans[f"resolution_{res_name}"] = m.group(0)

        # 9. Temporal Signals
        temporal_signals = []
        for pat in TEMPORAL_PATTERNS:
            m = pat.search(clean)
            if m:
                sig_str = m.group(0)
                if sig_str not in temporal_signals:
                    temporal_signals.append(sig_str)
                    evidence_spans["temporal_span"] = sig_str

        # 10. Evidence-Based Entity Extraction (Never invent entities)
        entities: Dict[str, Any] = {}
        
        # product_service
        ps_match = re.search(r"\b(broadband|wifi|internet|sim card|sim|app|application|phone|flight|ticket|router|line)\b", clean)
        if ps_match:
            entities["product_service"] = ps_match.group(0)

        # payment_method
        pm_match = re.search(r"\b(credit card|debit card|upi|paypal|bank transfer|card|apple pay)\b", clean)
        if pm_match:
            entities["payment_method"] = pm_match.group(0)

        # amount & currency
        amt_match = re.search(r"(?:\$|rs\.?|┬ú|Γé¼)\s*\d+(?:\.\d{2})?|\b\d+\s*(?:dollars|rupees|pounds|euros)\b", text, re.IGNORECASE)
        if amt_match:
            entities["amount"] = amt_match.group(0)
            if "$" in amt_match.group(0) or "dollar" in amt_match.group(0).lower():
                entities["currency"] = "USD"
            elif "rs" in amt_match.group(0).lower() or "rupee" in amt_match.group(0).lower():
                entities["currency"] = "INR"
            elif "┬ú" in amt_match.group(0) or "pound" in amt_match.group(0).lower():
                entities["currency"] = "GBP"
            elif "Γé¼" in amt_match.group(0) or "euro" in amt_match.group(0).lower():
                entities["currency"] = "EUR"

        # order_reference_id
        ref_match = re.search(r"\b(?:TW-|CMP-|CONV-)\d{4,10}\b|#(?:[a-zA-Z0-9_-]{4,12})", text)
        if ref_match:
            entities["order_reference_id"] = ref_match.group(0)

        # duration
        if temporal_signals:
            entities["duration"] = temporal_signals[0]

        # date_time
        dt_match = re.search(r"\b(today|yesterday|since\s+\w+|for\s+a\s+week)\b", clean)
        if dt_match:
            entities["date_time"] = dt_match.group(0)

        # location
        loc_match = re.search(r"\b(anna nagar|chennai|london|store|in\s+store)\b", clean)
        if loc_match:
            entities["location"] = loc_match.group(0)

        # support_channel
        entities["support_channel"] = "twitter"

        # 11. Dynamic Evidence-Based Confidence Scoring
        if best_cat == "other" and not best_subcat:
            confidence = 0.55
        elif best_subcat and max_sub_score >= 1:
            confidence = 0.95
        elif max_score >= 2 or (max_score >= 1 and (escalation_signals or temporal_signals)):
            confidence = 0.90
        elif max_score == 1:
            confidence = 0.78
        else:
            confidence = 0.60

        # 12. Severity & Reasons
        severity_reasons = []
        severity_score = 1

        if best_cat in ("payment", "refund", "billing"):
            severity_reasons.append("financial_impact")
            severity_score += 3
        if best_cat in ("network", "service_outage", "device_hardware"):
            severity_reasons.append("service_outage")
            severity_score += 4
        if "repeat_contact" in escalation_signals or "still_unresolved_language" in escalation_signals:
            severity_reasons.append("repeat_failure")
            severity_score += 2
        if "no_response_language" in escalation_signals:
            severity_reasons.append("long_wait")
            severity_score += 1
        if "explicit_escalation" in escalation_signals:
            severity_reasons.append("business_impact")
            severity_score += 2

        severity_score = min(max(severity_score, 1), 10)
        if severity_score >= 8:
            severity_label = "critical"
        elif severity_score >= 6:
            severity_label = "high"
        elif severity_score >= 3:
            severity_label = "medium"
        else:
            severity_label = "low"

        severity = NLPSeverity(
            label=severity_label,
            score=severity_score,
            reasons=severity_reasons or ["general_query"]
        )

        canonical_entity_keys = [
            "amount", "currency", "date_time", "duration", "location",
            "order_reference_id", "payment_method", "product_service", "support_channel"
        ]
        canonical_evidence_span_keys = [
            "category_keyword", "emotion_keyword", "escalation_explicit_escalation",
            "escalation_manager_request", "escalation_multiple_complaints",
            "escalation_no_response_language", "escalation_repeat_contact",
            "escalation_still_unresolved_language", "resolution_customer_claimed_resolved",
            "resolution_customer_claimed_unresolved", "resolution_waiting_for_resolution",
            "resolution_waiting_for_response", "subcategory_keyword", "temporal_span",
            "urgency_span"
        ]

        formatted_entities = {k: entities.get(k) for k in canonical_entity_keys}
        formatted_evidence_spans = {k: evidence_spans.get(k) for k in canonical_evidence_span_keys}

        return NLPResult(
            case_id=case_id,
            conversation_id=conversation_id,
            intent=intent,
            category=best_cat,
            subcategory=best_subcat,
            problem_type=problem_type,
            sentiment=sentiment,
            sentiment_label=sentiment_label,
            emotion=emotion,
            urgency=urgency,
            severity=severity,
            escalation_signals=escalation_signals,
            resolution_signals=resolution_signals,
            temporal_signals=temporal_signals,
            entities=formatted_entities,
            evidence_spans=formatted_evidence_spans,
            priority_signals=[f"urgency:{urgency}", f"severity:{severity_label}"],
            human_review_required=severity_label in ("high", "critical"),
            confidence=confidence,
            label_source="local_nlp_provider",
            model_version="v1.2-local"
        )



class ExternalNLPProviderAdapter(NLPProvider):
    """
    Validates external NLP JSON payload and converts it into canonical NLPResult,
    with robust fallbacks for malformed or missing fields.
    """
    def __init__(self, fallback_provider: Optional[NLPProvider] = None):
        self.fallback_provider = fallback_provider or LocalNLPProvider()

    def analyze_json(self, data: Optional[Dict[str, Any]], raw_text: str = "") -> NLPResult:
        case_id = None
        conversation_id = None
        if not isinstance(data, dict):
            logger.warning("Malformed external NLP JSON (not a dict). Falling back to LocalNLPProvider.")
            return self.fallback_provider.analyze_text(raw_text)

        try:
            case_id = data.get("case_id")
            conversation_id = data.get("conversation_id")

            intent_data = data.get("intent", {})
            intent_label = intent_data.get("label", "other") if isinstance(intent_data, dict) else str(intent_data)

            topic_data = data.get("topic", {})
            topic_label = topic_data.get("label", intent_label) if isinstance(topic_data, dict) else str(topic_data)

            sentiment_data = data.get("sentiment", {})
            if isinstance(sentiment_data, dict):
                sent_label = sentiment_data.get("label", "neutral")
                sent_conf = float(sentiment_data.get("confidence", 0.5))
                sent_val = -0.8 if sent_label == "negative" else (0.8 if sent_label == "positive" else 0.0)
            else:
                sent_label = "neutral"
                sent_val = 0.0

            sev_data = data.get("severity", {})
            if isinstance(sev_data, dict):
                sev_label = sev_data.get("label", "medium")
                sev_score = int(sev_data.get("score", 5))
                sev_reasons = list(sev_data.get("reasons", ["external_analysis"]))
            else:
                sev_label = "medium"
                sev_score = 5
                sev_reasons = ["external_analysis"]

            severity = NLPSeverity(
                label=sev_label,
                score=sev_score,
                reasons=sev_reasons
            )

            return NLPResult(
                case_id=case_id,
                conversation_id=conversation_id,
                intent=intent_label,
                category=topic_label,
                subcategory=data.get("subcategory"),
                problem_type=data.get("problem_type", PROBLEM_TYPE_MAP.get(topic_label, "unknown")),
                sentiment=sent_val,
                sentiment_label=sent_label,
                emotion=data.get("emotion", "neutral"),
                urgency=data.get("urgency", "medium"),
                severity=severity,
                escalation_signals=data.get("escalation_signals", []),
                resolution_signals=data.get("resolution_signals", []),
                temporal_signals=data.get("temporal_signals", []),
                entities=data.get("entities", {}),
                evidence_spans=data.get("evidence_spans", {}),
                priority_signals=data.get("priority_signals", []),
                human_review_required=bool(data.get("human_review_required", False)),
                confidence=float(data.get("confidence", 0.9)),
                label_source="external_nlp_provider",
                model_version="v1.2-external"
            )
        except Exception as e:
            logger.warning(f"Malformed external NLP JSON: {e}. Falling back to LocalNLPProvider.")
            return self.fallback_provider.analyze_text(raw_text, case_id, conversation_id)

    def analyze_text(self, text: str, case_id: Optional[str] = None, conversation_id: Optional[str] = None) -> NLPResult:
        return self.fallback_provider.analyze_text(text, case_id, conversation_id)


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# TransformerNLPProvider  ΓÇö HuggingFace-powered, semantically accurate NLP
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class TransformerNLPProvider(NLPProvider):
    """
    Production-quality NLP engine powered by three HuggingFace transformer models:

    1. Sentiment  : cardiffnlp/twitter-roberta-base-sentiment-latest
                    Fine-tuned on 124M tweets ΓåÆ ideal for support/social-media text.
                    3 classes: negative / neutral / positive ΓåÆ maps to [-1, 0, 1].

    2. Intent /   : facebook/bart-large-mnli  (zero-shot NLI classifier)
       Category     Classifies into any label set without retraining.
                    Uses the same TAXONOMY_KEYWORDS keys as candidate labels.

    3. Emotion    : j-hartmann/emotion-english-distilroberta-base
                    7-class Ekman emotion (anger, disgust, fear, joy, neutral,
                    sadness, surprise).  Replaces the 3-word keyword list.

    Urgency, escalation, resolution, temporal and entity signals are still
    handled by the fast regex rules in LocalNLPProvider ΓÇö they are already
    highly accurate and need no ML upgrade.

    Falls back to LocalNLPProvider transparently if models are unavailable
    (e.g. no internet on first run or HuggingFace cache missing).

    Usage:
        provider = TransformerNLPProvider()
        result   = provider.analyze_text("I was charged twice and nobody replied!")
    """

    # Candidate labels for zero-shot intent/category classification
    _INTENT_LABELS: List[str] = list(TAXONOMY_KEYWORDS.keys())

    # Map BART zero-shot label ΓåÆ sentiment-style emotion string
    _BART_EMOTION_MAP: Dict[str, str] = {
        "anger":    "anger",
        "disgust":  "anger",
        "fear":     "frustration",
        "joy":      "satisfaction",
        "neutral":  "neutral",
        "sadness":  "frustration",
        "surprise": "neutral",
    }

    def __init__(
        self,
        sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english",
        zeroshot_model:  str = "cross-encoder/nli-MiniLM2-L6-H768",
        emotion_model:   str = "bhadresh-savani/distilbert-base-uncased-emotion",
        taxonomy: Optional[List[str]] = None,
        device: Optional[str] = None,  # None ΓåÆ auto-detect (cuda > mps > cpu)
    ):
        self.sentiment_model_name = sentiment_model
        self.zeroshot_model_name  = zeroshot_model
        self.emotion_model_name   = emotion_model
        self.taxonomy = taxonomy or self._INTENT_LABELS

        self._device = device or self._detect_device()
        self._fallback = LocalNLPProvider(taxonomy=taxonomy)

        # Lazy-loaded pipelines (None until first use)
        self._sentiment_pipe = None
        self._zeroshot_pipe  = None
        self._emotion_pipe   = None
        self._available      = False

        self._init_pipelines()

    # ΓöÇΓöÇ Device detection ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    @staticmethod
    def _detect_device() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    # ΓöÇΓöÇ Pipeline initialisation ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def _init_pipelines(self) -> None:
        """
        Attempt to load all three HuggingFace pipelines.
        Logs a warning and falls back to LocalNLPProvider on any failure.
        """
        try:
            from transformers import pipeline as hf_pipeline
        except ImportError:
            logger.warning(
                "[TransformerNLP] 'transformers' not installed. "
                "Run: pip install transformers torch  ΓÇö falling back to LocalNLPProvider."
            )
            return

        try:
            logger.info(
                f"[TransformerNLP] Loading sentiment model: {self.sentiment_model_name} on {self._device}"
            )
            self._sentiment_pipe = hf_pipeline(
                "sentiment-analysis",
                model=self.sentiment_model_name,
                device=0 if self._device == "cuda" else -1,
                truncation=True,
                max_length=512,
            )
            logger.info("[TransformerNLP] [OK] Sentiment model loaded.")
        except Exception as e:
            logger.warning(f"[TransformerNLP] Sentiment model load failed: {e}")

        try:
            logger.info(
                f"[TransformerNLP] Loading zero-shot model: {self.zeroshot_model_name} on {self._device}"
            )
            self._zeroshot_pipe = hf_pipeline(
                "zero-shot-classification",
                model=self.zeroshot_model_name,
                device=0 if self._device == "cuda" else -1,
            )
            logger.info("[TransformerNLP] [OK] Zero-shot classifier loaded.")
        except Exception as e:
            logger.warning(f"[TransformerNLP] Zero-shot model load failed: {e}")

        try:
            logger.info(
                f"[TransformerNLP] Loading emotion model: {self.emotion_model_name} on {self._device}"
            )
            self._emotion_pipe = hf_pipeline(
                "text-classification",
                model=self.emotion_model_name,
                device=0 if self._device == "cuda" else -1,
                truncation=True,
                max_length=512,
                top_k=1,
            )
            logger.info("[TransformerNLP] [OK] Emotion model loaded.")
        except Exception as e:
            logger.warning(f"[TransformerNLP] Emotion model load failed: {e}")

        if self._sentiment_pipe or self._zeroshot_pipe:
            self._available = True
            logger.info("[TransformerNLP] Provider is ACTIVE (transformer-based NLP).")
        else:
            logger.warning("[TransformerNLP] No models loaded ΓÇö will use LocalNLPProvider fallback.")

    # ΓöÇΓöÇ Core analysis ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def analyze_text(
        self,
        text: str,
        case_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> NLPResult:
        """
        Full NLP analysis using transformer models.

        Sentiment, intent/category, and emotion come from HuggingFace models.
        Urgency, escalation, temporal, entity signals come from the fast
        LocalNLPProvider regex layer (already accurate ΓÇö no ML upgrade needed).
        """
        if not self._available or not text or not text.strip():
            return self._fallback.analyze_text(text, case_id, conversation_id)

        # ΓöÇΓöÇ Step 1: Get rule-based signals from LocalNLPProvider as base ΓöÇΓöÇΓöÇΓöÇΓöÇ
        # This gives us urgency, escalation, temporal, entities, severity, etc.
        base: NLPResult = self._fallback.analyze_text(text, case_id, conversation_id)

        # ΓöÇΓöÇ Step 2: Transformer sentiment ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        sentiment, sentiment_label = base.sentiment, base.sentiment_label
        if self._sentiment_pipe:
            try:
                sent_result = self._sentiment_pipe(text[:512])[0]
                raw_label   = sent_result["label"].lower()  # e.g. "negative", "positive", "neutral"
                raw_score   = float(sent_result["score"])   # confidence [0, 1]

                if "negative" in raw_label:
                    sentiment       = round(-(raw_score), 3)
                    sentiment_label = "negative"
                elif "positive" in raw_label:
                    sentiment       = round(raw_score, 3)
                    sentiment_label = "positive"
                else:
                    sentiment       = 0.0
                    sentiment_label = "neutral"
            except Exception as e:
                logger.debug(f"[TransformerNLP] Sentiment inference error: {e}")

        # ΓöÇΓöÇ Step 3: Zero-shot intent / category classification ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        best_cat    = base.category
        best_subcat = base.subcategory
        intent      = base.intent
        confidence  = base.confidence

        if self._zeroshot_pipe:
            try:
                truncated = text[:1024]  # BART handles up to ~1024 tokens
                zs_result = self._zeroshot_pipe(
                    truncated,
                    candidate_labels=self.taxonomy,
                    multi_label=False,
                )
                top_label = zs_result["labels"][0]
                top_score = float(zs_result["scores"][0])

                # Only accept if model is reasonably confident
                if top_score >= 0.25:
                    best_cat   = top_label
                    intent     = top_label
                    confidence = round(top_score, 4)

                    # Re-derive subcategory from updated category
                    subcat_dict = SUBCATEGORY_TAXONOMY.get(best_cat, {})
                    clean       = text.lower()
                    sub_scores  = {}
                    for subcat, kws in subcat_dict.items():
                        matches = [kw for kw in kws if kw in clean]
                        if matches:
                            sub_scores[subcat] = len(matches)
                    if sub_scores:
                        best_subcat = max(sub_scores, key=sub_scores.get)
                        intent      = best_subcat
                    else:
                        best_subcat = None
            except Exception as e:
                logger.debug(f"[TransformerNLP] Zero-shot inference error: {e}")

        # ΓöÇΓöÇ Step 4: Transformer emotion ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        emotion = base.emotion
        if self._emotion_pipe:
            try:
                em_result = self._emotion_pipe(text[:512])
                # pipeline returns list of list when top_k=1
                em_label  = (em_result[0][0] if isinstance(em_result[0], list) else em_result[0])["label"].lower()
                emotion   = self._BART_EMOTION_MAP.get(em_label, "neutral")
            except Exception as e:
                logger.debug(f"[TransformerNLP] Emotion inference error: {e}")

        # ΓöÇΓöÇ Step 5: Re-derive problem_type from updated category ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        problem_type = PROBLEM_TYPE_MAP.get(best_cat, base.problem_type)

        # ΓöÇΓöÇ Step 6: Rebuild severity with updated category ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        severity_reasons = []
        severity_score   = 1

        if best_cat in ("payment", "refund", "billing"):
            severity_reasons.append("financial_impact")
            severity_score += 3
        if best_cat in ("network", "service_outage", "device_hardware"):
            severity_reasons.append("service_outage")
            severity_score += 4
        if "repeat_contact" in base.escalation_signals or "still_unresolved_language" in base.escalation_signals:
            severity_reasons.append("repeat_failure")
            severity_score += 2
        if "no_response_language" in base.escalation_signals:
            severity_reasons.append("long_wait")
            severity_score += 1
        if "explicit_escalation" in base.escalation_signals:
            severity_reasons.append("business_impact")
            severity_score += 2

        severity_score = min(max(severity_score, 1), 10)
        if severity_score >= 8:
            severity_label = "critical"
        elif severity_score >= 6:
            severity_label = "high"
        elif severity_score >= 3:
            severity_label = "medium"
        else:
            severity_label = "low"

        severity = NLPSeverity(
            label=severity_label,
            score=severity_score,
            reasons=severity_reasons or ["general_query"],
        )

        return NLPResult(
            case_id=case_id,
            conversation_id=conversation_id,
            intent=intent,
            category=best_cat,
            subcategory=best_subcat,
            problem_type=problem_type,
            sentiment=sentiment,
            sentiment_label=sentiment_label,
            emotion=emotion,
            urgency=base.urgency,
            severity=severity,
            escalation_signals=base.escalation_signals,
            resolution_signals=base.resolution_signals,
            temporal_signals=base.temporal_signals,
            entities=base.entities,
            evidence_spans=base.evidence_spans,
            priority_signals=[f"urgency:{base.urgency}", f"severity:{severity_label}"],
            human_review_required=severity_label in ("high", "critical"),
            confidence=confidence,
            label_source="transformer_nlp_provider",
            model_version="v2.0-transformer",
        )
