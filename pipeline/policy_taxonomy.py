"""
policy_taxonomy.py

Taxonomy & Policy-Family Blueprint for RootIQ UC18 RAG Architecture.
Covering 20 support companies and their policy families based on the company policy blueprint.

Important:
Historical TWCS-derived rules must be stored with:
  authoritativeness = "inferred"
  provenance = "historical_inference"
unless an authoritative company policy/help-center document is provided.
"""

from typing import Any, Dict, List, Optional
from pipeline.schemas import KnowledgeDocument

COMPANY_POLICY_FAMILIES: Dict[str, Dict[str, Any]] = {
    "AmazonHelp": {
        "company_name": "AmazonHelp",
        "aliases": ["amazon", "amazonhelp", "prime", "amazon customer service"],
        "policy_families": {
            "Orders & Delivery": {
                "coverage": ["late delivery", "missing package", "tracking update", "delivery estimate", "damaged package", "delivery exception"],
                "keywords": ["delivery", "order", "package", "shipping", "tracking", "courier", "dispatch"]
            },
            "Returns & Refunds": {
                "coverage": ["return eligibility", "refund eligibility", "refund timing", "partial refund", "return window"],
                "keywords": ["refund", "return", "money back", "reimburse", "replacement"]
            },
            "Payments & Billing": {
                "coverage": ["duplicate charge", "failed payment", "payment method", "billing dispute"],
                "keywords": ["payment", "card", "charged", "billing", "invoice", "debit"]
            },
            "Account & Prime": {
                "coverage": ["account access", "verification", "Prime eligibility", "membership cancellation"],
                "keywords": ["account", "prime", "login", "password", "membership", "subscription"]
            },
            "Product & Replacement": {
                "coverage": ["defective product", "damaged product", "replacement", "warranty", "troubleshooting"],
                "keywords": ["item", "product", "defective", "damaged", "broken", "hardware"]
            }
        }
    },
    "AppleSupport": {
        "company_name": "AppleSupport",
        "aliases": ["apple", "applesupport", "iphone", "ipad", "mac", "app store"],
        "policy_families": {
            "Device & Hardware": {
                "coverage": ["iPhone/iPad/Mac problems", "damage", "hardware troubleshooting"],
                "keywords": ["iphone", "ipad", "mac", "hardware", "screen", "battery", "device"]
            },
            "Apple ID & Account": {
                "coverage": ["authentication", "locked account", "password", "verification"],
                "keywords": ["apple id", "icloud", "account", "login", "password", "locked"]
            },
            "Purchases & Billing": {
                "coverage": ["App Store purchases", "duplicate charges", "payment problems"],
                "keywords": ["app store", "purchase", "billing", "charged", "itunes"]
            },
            "Subscriptions & Refunds": {
                "coverage": ["Apple Music", "subscriptions", "cancellation", "refund requests"],
                "keywords": ["subscription", "apple music", "refund", "cancel", "recurring"]
            },
            "Repairs & Warranty": {
                "coverage": ["repair eligibility", "replacement", "warranty and service requirements"],
                "keywords": ["repair", "applecare", "warranty", "genius bar", "service"]
            }
        }
    },
    "Uber_Support": {
        "company_name": "Uber_Support",
        "aliases": ["uber", "uber_support", "ubereats", "uber driver"],
        "policy_families": {
            "Ride & Driver Issues": {
                "coverage": ["wrong route", "driver problems", "ride cancellation", "trip issues"],
                "keywords": ["ride", "driver", "route", "trip", "car", "pickup"]
            },
            "Payments & Fare": {
                "coverage": ["incorrect fare", "duplicate charge", "payment failure", "fare disputes"],
                "keywords": ["fare", "charge", "payment", "toll", "tip", "overcharge"]
            },
            "Cancellation & Refunds": {
                "coverage": ["cancellation fees", "refund eligibility", "refund processing"],
                "keywords": ["cancellation fee", "refund", "cancelled ride", "reimbursement"]
            },
            "Account & Safety": {
                "coverage": ["account access", "identity verification", "safety incidents"],
                "keywords": ["account", "safety", "verification", "deactivated", "reported"]
            },
            "Uber Services & Promotions": {
                "coverage": ["passes", "credits", "promotions", "eligibility", "service-specific issues"],
                "keywords": ["promo", "pass", "credit", "discount", "code", "ubereats"]
            }
        }
    },
    "SpotifyCares": {
        "company_name": "SpotifyCares",
        "aliases": ["spotify", "spotifycares", "spotify premium"],
        "policy_families": {
            "Subscription & Billing": {
                "coverage": ["Premium charges", "duplicate billing", "failed payment"],
                "keywords": ["premium", "billing", "subscription", "charge", "payment"]
            },
            "Cancellation & Refunds": {
                "coverage": ["subscription cancellation", "refund eligibility"],
                "keywords": ["cancel", "refund", "downgrade", "money back"]
            },
            "Account & Login": {
                "coverage": ["account access", "password", "account recovery"],
                "keywords": ["account", "login", "password", "email", "reset"]
            },
            "Student & Promotional Plans": {
                "coverage": ["student eligibility", "promotional offers", "plan requirements"],
                "keywords": ["student", "family plan", "duo", "promo", "discount"]
            },
            "App & Playback": {
                "coverage": ["playback", "downloads", "device compatibility", "technical issues"],
                "keywords": ["playback", "offline", "download", "song", "playlist", "app"]
            }
        }
    },
    "Delta": {
        "company_name": "Delta",
        "aliases": ["delta", "delta air lines", "delta flight"],
        "policy_families": {
            "Flight Booking & Changes": {
                "coverage": ["booking", "changes", "cancellation", "rebooking"],
                "keywords": ["booking", "change flight", "ticket", "rebook", "reservation"]
            },
            "Baggage": {
                "coverage": ["lost baggage", "delayed baggage", "damaged baggage", "baggage limits"],
                "keywords": ["bag", "baggage", "luggage", "checked bag", "lost bag"]
            },
            "Refunds & Compensation": {
                "coverage": ["ticket refunds", "cancellation refunds", "disruption compensation"],
                "keywords": ["refund", "compensation", "voucher", "eCredit"]
            },
            "Flight Disruptions": {
                "coverage": ["delays", "cancellations", "missed connections", "rebooking"],
                "keywords": ["delayed", "cancelled", "disruption", "connection", "weather"]
            },
            "Travel Requirements": {
                "coverage": ["check-in", "documents", "seats", "airport requirements"],
                "keywords": ["check-in", "seat", "boarding", "passport", "gate"]
            }
        }
    },
    "AmericanAir": {
        "company_name": "AmericanAir",
        "aliases": ["americanair", "aa", "american airlines"],
        "policy_families": {
            "Booking & Tickets": {
                "coverage": ["ticket purchase", "changes", "cancellation"],
                "keywords": ["ticket", "booking", "flight change", "reservation"]
            },
            "Refunds & Credits": {
                "coverage": ["eligible refunds", "travel credits", "refund processing"],
                "keywords": ["refund", "credit", "trip credit", "voucher"]
            },
            "Baggage": {
                "coverage": ["baggage fees", "lost/damaged/delayed baggage"],
                "keywords": ["bag", "baggage", "luggage", "fee"]
            },
            "Flight Disruption": {
                "coverage": ["cancellations", "delays", "rebooking"],
                "keywords": ["delay", "cancel", "stranded", "rebook"]
            },
            "Travel & Check-in": {
                "coverage": ["check-in", "seats", "boarding", "travel requirements"],
                "keywords": ["checkin", "seat", "boarding pass", "gate"]
            }
        }
    },
    "British_Airways": {
        "company_name": "British_Airways",
        "aliases": ["british_airways", "ba", "british airways"],
        "policy_families": {
            "Booking & Fare Rules": {
                "coverage": ["booking", "fare restrictions", "changes"],
                "keywords": ["booking", "fare", "change flight", "avios"]
            },
            "Cancellation & Refunds": {
                "coverage": ["cancellation windows", "refunds", "fees"],
                "keywords": ["cancellation", "refund", "voucher", "claim"]
            },
            "Baggage": {
                "coverage": ["baggage allowance", "damage", "loss", "delay"],
                "keywords": ["baggage", "luggage", "allowance", "bag"]
            },
            "Seats & Boarding": {
                "coverage": ["seat selection", "check-in", "boarding"],
                "keywords": ["seat", "check-in", "boarding", "club world"]
            },
            "Flight Disruption": {
                "coverage": ["delays", "cancellations", "rebooking", "compensation"],
                "keywords": ["delay", "cancelled", "eu261", "compensation", "rebook"]
            }
        }
    },
    "SouthwestAir": {
        "company_name": "SouthwestAir",
        "aliases": ["southwestair", "southwest", "southwest airlines"],
        "policy_families": {
            "Reservations & Changes": {
                "coverage": ["booking", "changes", "fare differences"],
                "keywords": ["reservation", "change", "rebook", "flight"]
            },
            "Cancellation & Refunds": {
                "coverage": ["cancellation", "refundable/non-refundable fares"],
                "keywords": ["cancel", "refund", "travel funds", "lUV voucher"]
            },
            "Baggage": {
                "coverage": ["checked bags", "baggage limits", "lost/damaged baggage"],
                "keywords": ["bag", "two bags fly free", "luggage", "checked bag"]
            },
            "Flight Disruptions": {
                "coverage": ["delays", "cancellations", "rebooking"],
                "keywords": ["delayed", "cancelled", "weather", "reschedule"]
            },
            "Check-in & Boarding": {
                "coverage": ["EarlyBird", "boarding", "airport requirements"],
                "keywords": ["earlybird", "boarding position", "check-in", "a-list"]
            }
        }
    },
    "Tesco": {
        "company_name": "Tesco",
        "aliases": ["tesco", "tesco delivery", "clubcard"],
        "policy_families": {
            "Orders & Delivery": {
                "coverage": ["grocery delivery", "missing/late items"],
                "keywords": ["grocery", "delivery slot", "order", "van", "missing item"]
            },
            "Returns & Refunds": {
                "coverage": ["refunds", "returns", "refund timing"],
                "keywords": ["refund", "return", "receipt", "reimbursement"]
            },
            "Payments & Billing": {
                "coverage": ["payment problems", "incorrect charges"],
                "keywords": ["payment", "charged", "billing", "overcharge"]
            },
            "Products & Quality": {
                "coverage": ["damaged", "incorrect", "expired products"],
                "keywords": ["quality", "expired", "damaged", "rotten", "substituted"]
            },
            "Account & Loyalty": {
                "coverage": ["account and Clubcard issues"],
                "keywords": ["clubcard", "points", "account", "voucher"]
            }
        }
    },
    "TMobileHelp": {
        "company_name": "TMobileHelp",
        "aliases": ["tmobilehelp", "tmobile", "t-mobile"],
        "policy_families": {
            "Plans & Billing": {
                "coverage": ["plan charges", "billing disputes", "payment"],
                "keywords": ["bill", "plan", "charge", "auto-pay", "overage"]
            },
            "Devices & Upgrades": {
                "coverage": ["device eligibility", "upgrades", "device problems"],
                "keywords": ["device", "upgrade", "jump", "phone", "sim"]
            },
            "Promotions": {
                "coverage": ["BOGO", "trade-in", "promotional eligibility"],
                "keywords": ["promo", "trade-in", "rebate", "bogo", "credit"]
            },
            "Account & Authentication": {
                "coverage": ["account access", "verification", "account changes"],
                "keywords": ["account", "pin", "verification", "port", "line"]
            },
            "Network & Service": {
                "coverage": ["connectivity", "outages", "service problems"],
                "keywords": ["network", "signal", "5g", "lte", "outage", "coverage"]
            }
        }
    },
    "Comcast": {
        "company_name": "Comcast",
        "aliases": ["comcast", "xfinity", "ask_comcast"],
        "policy_families": {
            "Internet & Network": {
                "coverage": ["outages", "slow internet", "connectivity"],
                "keywords": ["internet", "wifi", "broadband", "outage", "down", "speed"]
            },
            "TV & Streaming": {
                "coverage": ["channels", "service problems"],
                "keywords": ["tv", "cable", "channel", "x1", "streaming"]
            },
            "Billing & Charges": {
                "coverage": ["incorrect charges", "fees"],
                "keywords": ["bill", "charge", "fee", "increase", "payment"]
            },
            "Equipment & Installation": {
                "coverage": ["modem/router/equipment", "technician visits"],
                "keywords": ["modem", "router", "gateway", "equipment", "tech", "installation"]
            },
            "Account & Cancellation": {
                "coverage": ["account changes", "verification", "cancellation"],
                "keywords": ["account", "cancel", "contract", "disconnect"]
            }
        }
    },
    "Ask_Spectrum": {
        "company_name": "Ask_Spectrum",
        "aliases": ["ask_spectrum", "spectrum", "charter"],
        "policy_families": {
            "Internet & Network": {
                "coverage": ["connectivity", "outages", "performance"],
                "keywords": ["internet", "outage", "slow", "connection", "wifi"]
            },
            "TV & Services": {
                "coverage": ["TV/service availability", "service issues"],
                "keywords": ["tv", "channel", "cable", "app"]
            },
            "Billing & Fees": {
                "coverage": ["billing disputes", "charges", "fees"],
                "keywords": ["bill", "charge", "fee", "price", "statement"]
            },
            "Account & Authentication": {
                "coverage": ["identity verification", "account changes"],
                "keywords": ["account", "verify", "login", "pin"]
            },
            "Cancellation & Equipment": {
                "coverage": ["cancellation", "equipment return", "service closure"],
                "keywords": ["cancel", "equipment return", "disconnect", "unreturned"]
            }
        }
    },
    "XboxSupport": {
        "company_name": "XboxSupport",
        "aliases": ["xboxsupport", "xbox", "microsoft xbox"],
        "policy_families": {
            "Account & Security": {
                "coverage": ["login", "account access", "bans"],
                "keywords": ["account", "login", "gamertag", "banned", "suspension"]
            },
            "Purchases & Refunds": {
                "coverage": ["purchases", "refund requests"],
                "keywords": ["refund", "purchase", "store", "order", "charge"]
            },
            "Subscriptions": {
                "coverage": ["Game Pass", "cancellation", "subscription issues"],
                "keywords": ["game pass", "gold", "subscription", "recurring", "cancel"]
            },
            "Games & Digital Content": {
                "coverage": ["downloads", "codes", "digital purchases"],
                "keywords": ["code", "download", "game", "content", "redeem"]
            },
            "Console & Hardware": {
                "coverage": ["controller", "console", "troubleshooting"],
                "keywords": ["console", "controller", "hardware", "series x", "repair"]
            }
        }
    },
    "AskPlayStation": {
        "company_name": "AskPlayStation",
        "aliases": ["askplaystation", "playstation", "ps4", "ps5", "sony playstation"],
        "policy_families": {
            "Account & Security": {
                "coverage": ["login", "bans", "account recovery"],
                "keywords": ["account", "psn", "login", "banned", "2fa", "hacked"]
            },
            "Purchases & Refunds": {
                "coverage": ["digital purchases", "refund eligibility"],
                "keywords": ["refund", "ps store", "purchase", "pre-order"]
            },
            "Subscriptions": {
                "coverage": ["PlayStation Plus", "cancellation"],
                "keywords": ["ps plus", "subscription", "auto-renew", "cancel"]
            },
            "Codes & Store": {
                "coverage": ["regional codes", "redemption"],
                "keywords": ["code", "voucher", "wallet", "region", "redeem"]
            },
            "Console & Hardware": {
                "coverage": ["controller", "console", "technical problems"],
                "keywords": ["ps5", "ps4", "controller", "dual sense", "console", "repair"]
            }
        }
    },
    "Sprint": {
        "company_name": "Sprint",
        "aliases": ["sprint", "sprintcare", "sprint support"],
        "policy_families": {
            "Plans & Billing": {
                "coverage": ["plan charges", "billing disputes", "payments"],
                "keywords": ["bill", "plan", "charge", "payment", "fee"]
            },
            "Devices & Upgrades": {
                "coverage": ["devices", "upgrades", "device problems"],
                "keywords": ["device", "lease", "upgrade", "phone", "sim"]
            },
            "Trade-in & Promotions": {
                "coverage": ["trade-ins", "promotional eligibility"],
                "keywords": ["trade-in", "promo", "credit", "rebate"]
            },
            "Account & Authentication": {
                "coverage": ["account access", "verification"],
                "keywords": ["account", "pin", "verification", "line"]
            },
            "Network & Service": {
                "coverage": ["connectivity", "outages", "service problems"],
                "keywords": ["network", "signal", "outage", "coverage", "data"]
            }
        }
    },
    "Hulu": {
        "company_name": "Hulu",
        "aliases": ["hulu", "hulu_support", "hulu support"],
        "policy_families": {
            "Subscription & Billing": {
                "coverage": ["subscription charges", "payment", "billing"],
                "keywords": ["billing", "subscription", "addon", "hulu live", "charge"]
            },
            "Cancellation & Refunds": {
                "coverage": ["cancellation", "refund eligibility"],
                "keywords": ["cancel", "refund", "trial", "money back"]
            },
            "Account & Eligibility": {
                "coverage": ["account access", "eligibility"],
                "keywords": ["account", "login", "profiles", "password"]
            },
            "Live TV & Location": {
                "coverage": ["home location", "live-TV requirements"],
                "keywords": ["home network", "location", "live tv", "zip code"]
            },
            "App & Playback": {
                "coverage": ["playback", "device", "technical issues"],
                "keywords": ["stream", "buffer", "playback", "error", "app"]
            }
        }
    },
    "Sainsburys": {
        "company_name": "Sainsburys",
        "aliases": ["sainsburys", "sainsbury", "nectar"],
        "policy_families": {
            "Orders & Delivery": {
                "coverage": ["orders", "delivery", "missing items"],
                "keywords": ["delivery", "slot", "order", "groceries", "missing"]
            },
            "Returns & Refunds": {
                "coverage": ["returns", "refunds", "refund timing"],
                "keywords": ["refund", "return", "reimbursement", "receipt"]
            },
            "Payments & Billing": {
                "coverage": ["payment problems", "incorrect charges"],
                "keywords": ["payment", "charged", "billing", "overcharge"]
            },
            "Product Quality": {
                "coverage": ["damaged", "incorrect", "expired products"],
                "keywords": ["quality", "expired", "damaged", "substitute", "fresh"]
            },
            "Account & Loyalty": {
                "coverage": ["account and loyalty-program issues"],
                "keywords": ["nectar", "points", "account", "card"]
            }
        }
    },
    "GWRHelp": {
        "company_name": "GWRHelp",
        "aliases": ["gwrhelp", "gwr", "great western railway"],
        "policy_families": {
            "Tickets & Booking": {
                "coverage": ["ticket purchase", "booking", "fare rules"],
                "keywords": ["ticket", "booking", "fare", "advance ticket"]
            },
            "Changes & Cancellation": {
                "coverage": ["ticket changes", "cancellation"],
                "keywords": ["change", "cancel", "rebook", "flexi"]
            },
            "Refunds": {
                "coverage": ["refund eligibility", "fees", "processing"],
                "keywords": ["refund", "admin fee", "claim refund"]
            },
            "Delays & Compensation": {
                "coverage": ["delay claims", "compensation"],
                "keywords": ["delay repay", "delayed", "compensation", "cancelled train"]
            },
            "Travel & Rail Operations": {
                "coverage": ["journey", "station", "operational issues"],
                "keywords": ["train", "station", "platform", "seat reservation"]
            }
        }
    },

    "VerizonSupport": {
        "company_name": "VerizonSupport",
        "aliases": ["verizonsupport", "verizon", "verizon wireless", "fios"],
        "policy_families": {
            "Plans & Billing": {
                "coverage": ["plans", "billing disputes", "charges"],
                "keywords": ["bill", "plan", "charge", "auto-pay", "trade-in credit"]
            },
            "Network & Connectivity": {
                "coverage": ["network performance", "outages"],
                "keywords": ["network", "outage", "signal", "5g", "fios", "internet"]
            },
            "Devices & Upgrades": {
                "coverage": ["device issues", "upgrades"],
                "keywords": ["device", "upgrade", "phone", "sim", "trade-in"]
            },
            "Promotions": {
                "coverage": ["promotion and eligibility rules"],
                "keywords": ["promo", "rebate", "gift card", "discount"]
            },
            "Account & Authentication": {
                "coverage": ["account access", "verification"],
                "keywords": ["account", "pin", "login", "transfer", "number"]
            }
        }
    }
}


def find_company_policy_family(
    query: str,
    text: str = "",
    company_hint: Optional[str] = None,
    entities: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Identifies the relevant company and policy family from query, text, company_hint, and extracted entities.
    Preserves strict company scope (e.g. AmazonHelp rules do NOT apply to AppleSupport).
    """
    clean_combined = f"{query} {text} {company_hint or ''}".lower()
    
    # 1. Match Company
    matched_company = None
    if company_hint:
        for comp, meta in COMPANY_POLICY_FAMILIES.items():
            if company_hint.lower() in [a.lower() for a in meta["aliases"]] or company_hint.lower() == comp.lower():
                matched_company = comp
                break
                
    if not matched_company:
        for comp, meta in COMPANY_POLICY_FAMILIES.items():
            for alias in meta["aliases"]:
                if alias in clean_combined:
                    matched_company = comp
                    break
            if matched_company:
                break
                
    # 2. Match Policy Family within identified company (or global if company unknown)
    target_families = COMPANY_POLICY_FAMILIES.get(matched_company, {}).get("policy_families", {}) if matched_company else {}
    
    matched_family = None
    if target_families:
        family_scores = {}
        for fam_name, fam_meta in target_families.items():
            score = sum(1 for kw in fam_meta["keywords"] if kw in clean_combined)
            if score > 0:
                family_scores[fam_name] = score
        if family_scores:
            matched_family = max(family_scores, key=family_scores.get)

    return {
        "company": matched_company or "unknown",
        "policy_family": matched_family or "General Policies",
        "available_families": list(target_families.keys()) if target_families else []
    }


def generate_policy_taxonomy_documents() -> List[Dict[str, Any]]:
    """
    Generates additive KnowledgeDocument items for the 20-company policy families taxonomy.
    Marked as document_type="policies", provenance="policy_family_blueprint", authoritativeness="taxonomy_structure".
    Does NOT overwrite or alter existing Stage 1-17 files.
    """
    docs = []
    for comp_name, comp_data in COMPANY_POLICY_FAMILIES.items():
        for fam_name, fam_info in comp_data["policy_families"].items():
            doc_id = f"DOC-TAXONOMY-{comp_name}-{fam_name.replace(' ', '_').replace('&', 'and')}"
            coverage_str = ", ".join(fam_info["coverage"])
            content = f"Company: {comp_name} | Policy Family: {fam_name} | Scope: {coverage_str}."
            
            kdoc = KnowledgeDocument(
                document_id=doc_id,
                doc_id=doc_id,
                document_type="policies",
                type="policies",
                title=f"{comp_name} Policy Family: {fam_name}",
                text=content,
                content=content,
                metadata={
                    "company": comp_name,
                    "policy_family": fam_name,
                    "coverage": fam_info["coverage"],
                    "provenance": "policy_family_blueprint",
                    "authoritativeness": "taxonomy_structure",
                    "is_rule": False
                },
                source_type="policy_taxonomy_blueprint",
                topic=fam_name
            ).model_dump()
            docs.append(kdoc)
    return docs
