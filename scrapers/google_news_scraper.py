import feedparser
from datetime import datetime, timezone
from scrapers.base_scraper import BaseScraper
from utils.network import resolve_google_news_url
from utils.text_processing import extract_article_content
from utils.llm import rewrite_article
from config import logger

class GoogleNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("Google News")
        self.rss_url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en"

    def scrape(self) -> list:
        logger.info("Starting scrape from Google News RSS feed...")
        articles = []
        
        try:
            feed = feedparser.parse(self.rss_url)
            if not feed.entries:
                logger.warning("No RSS entries found for Google News.")
                return []
                
            # Fetch up to 5 entries for reliability
            for entry in feed.entries[:5]:
                title = entry.title
                tracking_url = entry.link
                
                logger.info(f"Processing Google News tracking entry: {title}")
                
                # Rule: Resolve redirect URL to the actual publisher website before content extraction
                url = resolve_google_news_url(tracking_url)
                
                # Fetch original content from resolved source
                content = extract_article_content(url)
                if len(content) < 300:
                    logger.warning(f"Skipping Google News article '{title}' - content too short ({len(content)} chars).")
                    continue
                    
                # Run rewrite
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
            logger.error(f"Error occurred in Google News Scraper: {e}")
            
        return articles
