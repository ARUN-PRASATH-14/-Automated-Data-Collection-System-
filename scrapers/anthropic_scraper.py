import requests
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from utils.network import safe_request
from utils.text_processing import extract_article_content
from utils.llm import rewrite_article
from config import logger

class AnthropicScraper(BaseScraper):
    def __init__(self):
        super().__init__("Anthropic")
        self.url = "https://www.anthropic.com/news"

    def scrape(self) -> list:
        logger.info("Starting scrape from Anthropic News page...")
        articles = []
        seen = set()
        
        try:
            # Request page via network utility
            response = safe_request(self.url, method="GET")
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find all anchor tags with links
            for link in soup.find_all("a", href=True):
                if len(articles) >= 3:  # Retrieve up to 3 articles
                    break
                    
                href = link.get("href", "")
                
                # Resolve relative links
                url = href
                if url.startswith("/"):
                    url = "https://www.anthropic.com" + url
                    
                # Rule: Only scrape news sub-pages, excluding the listing page itself
                if not url.startswith("https://www.anthropic.com/news/") or url.rstrip("/") == "https://www.anthropic.com/news":
                    continue
                    
                if url in seen:
                    continue
                seen.add(url)
                
                # Rule: Resolve messy title by searching for structured header tag (h1-h6) inside the anchor card
                # If there are dates (e.g. 'June 20, 2026') or categories in raw anchor text, this filters them out.
                header_elem = link.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                if header_elem:
                    title = header_elem.get_text(strip=True)
                else:
                    title = link.get_text(strip=True)
                
                # Basic validation
                if not title or len(title) < 15:
                    logger.warning(f"Skipping link with empty or too short title: {title}")
                    continue
                    
                logger.info(f"Processing Anthropic article: {title}")
                
                # Fetch original content
                content = extract_article_content(url)
                if len(content) < 300:
                    logger.warning(f"Skipping Anthropic article '{title}' - content too short ({len(content)} chars).")
                    continue
                    
                # Run rewrite
                rewritten = rewrite_article(content)
                
                raw_article = {
                    "title": title,
                    "url": url,
                    "published_at": None,  # Will default to current time
                    "original_content": content,
                    "rewritten_article": rewritten
                }
                
                articles.append(self.normalize(raw_article))
                
        except Exception as e:
            logger.error(f"Error occurred in Anthropic Scraper: {e}")
            
        return articles
