from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
from utils.text_processing import clean_title
from config import logger

class BaseScraper(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Executes the scraping process.
        Returns:
            A list of scraped and normalized article dictionaries.
        """
        pass

    def normalize(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes scraped article dictionaries into a consistent structure
        ready for database insertion.
        """
        raw_title = article.get("title", "")
        cleaned = clean_title(raw_title)
        
        # Format or default the publish time
        pub_time = article.get("published_at")
        if not pub_time:
            pub_time = datetime.now(timezone.utc).isoformat()
            
        return {
            "title": cleaned,
            "url": article.get("url", ""),
            "source": article.get("source", self.source_name),
            "published_at": pub_time,
            "original_content": article.get("original_content", ""),
            "rewritten_article": article.get("rewritten_article", None)
        }
