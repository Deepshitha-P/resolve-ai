import os
import duckdb
from typing import Dict, List, Optional
from datetime import datetime

from pipeline.config_loader import load_config
from pipeline.logger import get_logger

logger = get_logger("WarehouseEngine")

class WarehouseEngine:
    """
    Simulates an Enterprise Bulk Analytical Warehouse (like Snowflake) using DuckDB
    over our persistent Parquet data lake.
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.con = duckdb.connect(database=":memory:")
        
        # Load Parquet files into views for easy querying
        base_dir = self.config.get("storage", {}).get("base_dir", "data")
        
        self.raw_path = os.path.join(base_dir, "parquet", "raw_cases.parquet").replace("\\", "/")
        self.conv_path = os.path.join(base_dir, "conversations", "conversations.parquet").replace("\\", "/")
        self.nlp_path = os.path.join(base_dir, "nlp", "nlp_results.parquet").replace("\\", "/")
        
    def _check_files(self) -> bool:
        return os.path.exists(self.conv_path) and os.path.exists(self.nlp_path)

    def run_date_range_report(self, start_date: str, end_date: str) -> Dict:
        """
        Executes a complex analytical query over the historical parquet lake
        for a specific date range.
        Dates should be 'YYYY-MM-DD'.
        """
        if not self._check_files():
            return {"error": "Warehouse data files not found. Run the batch pipeline first."}
            
        query = f"""
            SELECT 
                COUNT(*) as total_volume,
                SUM(CAST(c.has_company_response AS INT)) * 100.0 / NULLIF(COUNT(*), 0) as response_rate,
                SUM(CAST(TRY_CAST(n.trajectory.escalation_flag AS BOOLEAN) AS INT)) * 100.0 / NULLIF(COUNT(*), 0) as escalation_rate,
                AVG(n.trajectory.csat_proxy_score) as avg_csat,
                AVG(n.sentiment) as avg_sentiment
            FROM '{self.conv_path}' c
            JOIN '{self.nlp_path}' n ON c.conversation_id = n.conversation_id
            WHERE TRY_CAST(c.start_time AS TIMESTAMP) >= '{start_date} 00:00:00'
              AND TRY_CAST(c.start_time AS TIMESTAMP) <= '{end_date} 23:59:59'
        """
        
        try:
            res = self.con.execute(query).fetchone()
            
            # Top Intents
            intent_query = f"""
                SELECT n.intent, COUNT(*) as count
                FROM '{self.conv_path}' c
                JOIN '{self.nlp_path}' n ON c.conversation_id = n.conversation_id
                WHERE TRY_CAST(c.start_time AS TIMESTAMP) >= '{start_date} 00:00:00'
                  AND TRY_CAST(c.start_time AS TIMESTAMP) <= '{end_date} 23:59:59'
                GROUP BY n.intent
                ORDER BY count DESC
                LIMIT 5
            """
            top_intents = self.con.execute(intent_query).fetchall()
            
            return {
                "date_range": {"start": start_date, "end": end_date},
                "total_volume": res[0] or 0,
                "response_rate": round(res[1] or 0, 2),
                "escalation_rate": round(res[2] or 0, 2),
                "avg_csat": round(res[3] or 0, 2),
                "avg_sentiment": round(res[4] or 0, 2),
                "top_intents": [{"intent": row[0], "count": row[1]} for row in top_intents]
            }
        except Exception as e:
            logger.error(f"Date range report failed: {e}")
            return {"error": str(e)}

    def search_raw_data(self, query_string: str, limit: int = 5) -> List[Dict]:
        """
        Implements the Retrieval Loop: Searches the raw conversations for specific keywords.
        Returns a formatted list representing the raw records.
        """
        if not self._check_files():
            return []
            
        import re
        # Exclude common stop words to improve basic text search
        stopwords = {"what", "who", "is", "a", "at", "is", "he", "was", "the", "and", "find", "me", "cases", "where", "customer", "complained", "about", "raw", "data", "tweets", "deep", "dive"}
        words = [w for w in re.split(r'\W+', query_string.lower()) if len(w) > 3 and w not in stopwords]
        
        if not words:
            words = [query_string.lower().strip()]
            
        # Simple OR match across the stringified turns array
        like_clauses = " OR ".join([f"LOWER(CAST(c.turns AS VARCHAR)) LIKE '%{w}%'" for w in words])
        
        sql = f"""
            SELECT c.conversation_id, c.start_time, c.company_handle, CAST(c.turns AS VARCHAR) as text_content
            FROM '{self.conv_path}' c
            WHERE {like_clauses}
            LIMIT {limit}
        """
        
        try:
            results = self.con.execute(sql).fetchall()
            
            evidence = []
            for r in results:
                cid, start_time, company, content = r
                clean_content = content[:400] + "..." if len(content) > 400 else content
                
                evidence.append({
                    "layer": "raw_data_warehouse",
                    "doc_id": f"RAW-{cid}",
                    "title": f"Raw Thread from {start_time} ({company})",
                    "excerpt": clean_content,
                    "relevance_score": 0.99,
                    "trust_score": 1.0 
                })
            return evidence
        except Exception as e:
            logger.error(f"Search raw data failed: {e}")
            return []
