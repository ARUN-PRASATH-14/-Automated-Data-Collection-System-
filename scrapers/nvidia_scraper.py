import feedparser
from datetime import datetime, timezone
from scrapers.base_scraper import BaseScraper
from utils.text_processing import extract_article_content
from utils.llm import rewrite_article
from config import logger

class NvidiaScraper(BaseScraper):
    def __init__(self):
        super().__init__("NVIDIA")
        self.rss_url = "https://blogs.nvidia.com/feed/"

    def scrape(self) -> list:
        logger.info("Starting scrape from NVIDIA RSS feed...")
        articles = []
        
        try:
            feed = feedparser.parse(self.rss_url)
            if not feed.entries:
                logger.warning("No RSS entries found for NVIDIA.")
                return []
                
            for entry in feed.entries[:5]:
                title = entry.title
                url = entry.link
                logger.info(f"Processing NVIDIA RSS entry: {title}")
                
                # Fetch original content
                content = extract_article_content(url)
                if len(content) < 300:
                    logger.warning(f"Skipping NVIDIA article '{title}' - content too short ({len(content)} chars).")
                    continue
                    
                # Run rewrite (with fallbacks inside utility)
                rewritten = rewrite_article(content)
                
                # Parse publication date from RSS entry if available
                pub_time = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass
                if not pub_time and hasattr(entry, "published"):
                    pub_time = str(entry.published)
                    
                raw_article = {
                    "title": title,
                    "url": url,
                    "published_at": pub_time,
                    "original_content": content,
                    "rewritten_article": rewritten
                }
                
                articles.append(self.normalize(raw_article))
                
        except Exception as e:
            logger.error(f"Error occurred in NVIDIA Scraper: {e}")
            
        return articles
