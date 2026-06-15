from datetime import datetime, timezone
from scrapers.base_scraper import BaseScraper
from utils.network import safe_request
from utils.text_processing import extract_article_content
from utils.llm import rewrite_article
from config import logger

class HackerNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("HackerNews")
        self.top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        self.item_url_template = "https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        self.keywords = [
            "ai", "artificial intelligence", "llm",
            "openai", "anthropic", "chatgpt",
            "gemini", "claude", "machine learning",
            "deep learning", "neural network", "transformer"
        ]

    def scrape(self) -> list:
        logger.info("Starting scrape from HackerNews API...")
        articles = []
        
        try:
            # Fetch top story IDs
            response = safe_request(self.top_stories_url, method="GET")
            story_ids = response.json()
            
            for story_id in story_ids[:30]:
                if len(articles) >= 3:  # Retrieve up to 3 articles matching keywords
                    break
                    
                try:
                    item_url = self.item_url_template.format(story_id=story_id)
                    item_resp = safe_request(item_url, method="GET")
                    item = item_resp.json()
                    
                    if not item:
                        continue
                        
                    title = item.get("title", "")
                    
                    # Filter by keywords
                    if not any(kw in title.lower() for kw in self.keywords):
                        continue
                        
                    # Standard fallback URL is the YCombinator thread link if URL is missing
                    url = item.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                    
                    logger.info(f"Processing HackerNews story: {title}")
                    
                    # Extract original content
                    content = extract_article_content(url)
                    if len(content) < 300:
                        logger.warning(f"Skipping HackerNews story '{title}' - content too short.")
                        continue
                        
                    # Run rewrite
                    rewritten = rewrite_article(content)
                    
                    # Convert UNIX time stamp to ISO format string
                    pub_time = None
                    unix_time = item.get("time")
                    if unix_time:
                        try:
                            pub_time = datetime.fromtimestamp(unix_time, tz=timezone.utc).isoformat()
                        except Exception:
                            pass
                            
                    raw_article = {
                        "title": title,
                        "url": url,
                        "published_at": pub_time,
                        "original_content": content,
                        "rewritten_article": rewritten
                    }
                    
                    articles.append(self.normalize(raw_article))
                    
                except Exception as inner_e:
                    logger.warning(f"Failed to process HackerNews story ID {story_id}: {inner_e}")
                    
        except Exception as e:
            logger.error(f"Error occurred in HackerNews Scraper: {e}")
            
        return articles
