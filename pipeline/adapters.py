import csv
import json
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Generator, List, Optional
from pipeline.schemas import CaseRecord
from pipeline.logger import get_logger

logger = get_logger("DatasetAdapter")


class DatasetAdapter(ABC):
    @abstractmethod
    def load_data(self, limit: Optional[int] = None) -> List[CaseRecord]:
        pass

    @abstractmethod
    def stream_data(self, chunk_size: int = 10000, limit: Optional[int] = None, offset: int = 0) -> Generator[List[CaseRecord], None, None]:
        pass


class CSVDatasetAdapter(DatasetAdapter):
    def __init__(self, file_path: str, source_type: str = "twcs_case"):
        self.file_path = file_path
        self.source_type = source_type

    def load_data(self, limit: Optional[int] = None) -> List[CaseRecord]:
        records = []
        for chunk in self.stream_data(chunk_size=limit or 50000, limit=limit):
            records.extend(chunk)
            if limit and len(records) >= limit:
                return records[:limit]
        return records

    def stream_data(self, chunk_size: int = 10000, limit: Optional[int] = None, offset: int = 0) -> Generator[List[CaseRecord], None, None]:
        if not os.path.exists(self.file_path):
            logger.error(f"CSV file not found: {self.file_path}")
            return

        total_yielded = 0
        current_chunk = []

        with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            # Skip offset rows
            for _ in range(offset):
                try:
                    next(reader)
                except StopIteration:
                    break

            for row in reader:
                tweet_id = row.get("tweet_id", "").strip()
                author_id = row.get("author_id", "").strip()
                inbound_str = str(row.get("inbound", "")).strip().lower()
                inbound = inbound_str in ("true", "1", "t")
                created_at = row.get("created_at", "").strip()
                raw_text = row.get("text", "").strip()
                clean_text = row.get("clean_text", "").strip() or None
                response_tweet_id = row.get("response_tweet_id", "").strip() or None
                in_response_to_tweet_id = row.get("in_response_to_tweet_id", "").strip() or None

                rec = CaseRecord(
                    case_id=f"TW-{tweet_id}",
                    conversation_id=None,
                    customer_id=author_id if inbound else f"BRAND-{author_id}",
                    channel="twitter",
                    area=None,
                    timestamp=created_at,
                    raw_text=raw_text,
                    clean_text=clean_text,
                    inbound=inbound,
                    response_tweet_id=response_tweet_id,
                    in_response_to_tweet_id=in_response_to_tweet_id,
                    source_type=self.source_type,
                    metadata={"tweet_id": tweet_id, "author_id": author_id},
                )
                current_chunk.append(rec)
                total_yielded += 1

                if len(current_chunk) >= chunk_size:
                    yield current_chunk
                    current_chunk = []

                if limit and total_yielded >= limit:
                    break

            if current_chunk:
                yield current_chunk


class JSONDatasetAdapter(DatasetAdapter):
    def __init__(self, file_path: str, source_type: str = "json_case"):
        self.file_path = file_path
        self.source_type = source_type

    def load_data(self, limit: Optional[int] = None) -> List[CaseRecord]:
        if not os.path.exists(self.file_path):
            logger.error(f"JSON file not found: {self.file_path}")
            return []
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            records = [CaseRecord(**item) for item in data]
            return records[:limit] if limit else records

    def stream_data(self, chunk_size: int = 10000, limit: Optional[int] = None) -> Generator[List[CaseRecord], None, None]:
        records = self.load_data(limit=limit)
        for i in range(0, len(records), chunk_size):
            yield records[i:i + chunk_size]


class SyntheticDatasetAdapter(DatasetAdapter):
    def __init__(self, source_type: str = "synthetic_case"):
        self.source_type = source_type

    def load_data(self, limit: Optional[int] = 100) -> List[CaseRecord]:
        n = limit or 100
        records = []
        start = datetime(2026, 8, 1, 8, 0, 0)
        categories = ["network", "payment", "account", "delivery"]
        areas = ["Chennai-Anna Nagar", "Chennai-Velachery", "Coimbatore-RS Puram", "Chennai-Adyar", "Madurai-Central"]

        for i in range(n):
            cat = random.choice(categories)
            area = "Chennai-Anna Nagar" if (cat == "network" and i % 3 == 0) else random.choice(areas)
            ts = start + timedelta(days=random.randint(0, 9), hours=random.randint(0, 20))
            cid = 1000 + i

            rec = CaseRecord(
                case_id=f"CMP-{cid}",
                conversation_id=f"CONV-{cid}",
                customer_id=f"CUST-{random.randint(1, 200):03d}",
                channel=random.choice(["twitter", "app_chat", "call_transcript"]),
                area=area,
                timestamp=ts.isoformat(),
                raw_text=f"Sample complaint about {cat} in {area}",
                clean_text=f"sample complaint about {cat} in {area}",
                inbound=True,
                source_type=self.source_type,
            )
            records.append(rec)
        return records

    def stream_data(self, chunk_size: int = 10000, limit: Optional[int] = None) -> Generator[List[CaseRecord], None, None]:
        yield self.load_data(limit=limit)
