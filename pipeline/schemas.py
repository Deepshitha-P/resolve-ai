from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseRecord(BaseModel):
    case_id: str
    conversation_id: Optional[str] = None
    customer_id: str
    channel: str = "twitter"
    area: Optional[str] = None
    timestamp: str
    raw_text: str
    clean_text: Optional[str] = None
    inbound: bool = True
    response_tweet_id: Optional[str] = None
    in_response_to_tweet_id: Optional[str] = None
    source_type: str = "twcs_case"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    turn_id: Optional[str] = None
    role: str  # "customer" or "company"
    author_id: str
    text: str
    raw: str
    timestamp: str
    in_response_to_tweet_id: Optional[str] = None


class Conversation(BaseModel):
    conversation_id: str
    customer_id: str
    channel: str = "twitter"
    area: Optional[str] = None
    turns: List[ConversationTurn] = Field(default_factory=list)
    customer_turn_count: int = 1
    company_turn_count: int = 0
    start_time: str
    end_time: str
    first_response_time: Optional[float] = None  # seconds
    conversation_duration: Optional[float] = None  # seconds
    repeat_contact_signals: bool = False
    has_company_response: bool = False
    company_handle: Optional[str] = None
    company_handle_source: Optional[str] = None  # "confirmed" or "inferred"
    source_type: str = "twcs_case"
    nlp: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NLPSeverity(BaseModel):
    label: str  # "low", "medium", "high", "critical"
    score: int  # 1 to 10
    reasons: List[str] = Field(default_factory=list)


class SentimentTrajectory(BaseModel):
    """Per-conversation CSAT trajectory derived from sequential turn-level sentiment."""
    turn_sentiments: List[float] = Field(default_factory=list)  # sentiment per customer turn
    start_sentiment: float = 0.0   # sentiment of first customer turn
    end_sentiment: float = 0.0     # sentiment of last customer turn
    delta: float = 0.0             # end_sentiment ΓêÆ start_sentiment
    escalation_flag: bool = False  # True if sentiment dropped > threshold mid-thread
    recovery_flag: bool = False    # True if sentiment improved after a negative dip
    volatility: float = 0.0        # stddev of turn_sentiments
    csat_proxy_score: float = 3.0  # linear rescale of end_sentiment from [-1,1] to [1,5]


class NLPResult(BaseModel):
    case_id: Optional[str] = None
    conversation_id: Optional[str] = None
    intent: str
    category: str
    subcategory: Optional[str] = None
    problem_type: str = "unknown"
    sentiment: float  # -1.0 to +1.0
    sentiment_label: str  # "negative", "neutral", "positive"
    emotion: str = "neutral"  # "frustration", "anger", "satisfaction", "neutral"
    urgency: str = "medium"  # "low", "medium", "high", "critical"
    severity: NLPSeverity
    escalation_signals: List[str] = Field(default_factory=list)
    resolution_signals: List[str] = Field(default_factory=list)
    temporal_signals: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)
    evidence_spans: Dict[str, Any] = Field(default_factory=dict)
    priority_signals: List[str] = Field(default_factory=list)
    human_review_required: bool = False
    confidence: float = 1.0
    label_source: str = "local_nlp_provider"
    model_version: str = "v1.2-local"
    # ΓöÇΓöÇ Change 1: structured dimensions ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # EXTRACTION_QUALITY_FLAG: product/region are extracted via a lightweight
    # keyword gazetteer. Coverage on raw Twitter data is ~12% product / ~2.5%
    # region. Most records will remain "unknown". Replace _extract_product_and_region()
    # in stage04_nlp.py with a real NER model for higher coverage.
    product: str = "unknown"   # e.g. "broadband", "sim", "app", "unknown"
    region: str = "unknown"    # e.g. "london", "chennai", "unknown"
    # ΓöÇΓöÇ Change 2: CSAT trajectory ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    trajectory: Optional[Dict[str, Any]] = None  # SentimentTrajectory.model_dump()



class AnalyticsSnapshot(BaseModel):
    document_id: str
    document_type: str = "analytics_snapshot"
    source_type: str = "operational_analytics"
    period: str  # "daily", "weekly", "monthly", "global"
    topic: Optional[str] = None
    region: Optional[str] = None
    product: Optional[str] = None  # Change 1: product dimension
    created_at: str
    text: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class PainPointScore(BaseModel):
    pain_score: float  # 0.0 to 100.0
    volume_component: float  # 0.0 to 1.0
    negative_sentiment_component: float  # 0.0 to 1.0
    severity_component: float  # 0.0 to 1.0
    growth_component: float  # 0.0 to 1.0
    # Change 2: escalation trajectory weight
    escalation_rate_component: float = 0.0  # 0.0 to 1.0 ΓÇö fraction of members with escalation_flag=True


class IssueCluster(BaseModel):
    cluster_id: int
    cluster_name: str
    summary: str
    volume: int
    percentage: float
    dominant_topic: str
    dominant_intent: str
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    growth_rate: float = 0.0
    representative_case_ids: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    period: str = "overall"
    pain_point_impact: PainPointScore


class KnowledgeDocument(BaseModel):
    document_id: str
    doc_id: Optional[str] = None
    document_type: str  # "customer_cases", "conversations", "resolved_historical_cases", "issue_clusters", "temporal_events", "analytics_snapshots", "policies", "runbooks", "historical_insights"
    type: Optional[str] = None
    title: str = ""
    text: str = ""
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: str = "twcs_case"
    case_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: Optional[str] = None
    topic: Optional[str] = None
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    severity: Optional[str] = None
    region: Optional[str] = None
    product: Optional[str] = None
    cluster_id: Optional[int] = None
    period: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.doc_id:
            self.doc_id = self.document_id
        if not self.type:
            self.type = self.document_type
        if not self.text:
            self.text = self.content if self.content else self.title
        if not self.content:
            self.content = self.text



class EvidenceItem(BaseModel):
    doc_id: str
    source_type: str
    doc_type: str
    snippet: str
    trust_score: float
    relevance_score: float


class Insight(BaseModel):
    query: str
    intent: str
    grounded_insight_text: str
    evidence_chain: List[EvidenceItem] = Field(default_factory=list)
    confidence_score: float = 0.0
    created_at: Optional[str] = None
