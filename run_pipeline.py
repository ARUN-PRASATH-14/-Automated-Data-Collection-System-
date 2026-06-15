from config import logger
from database import save_article
from scrapers.nvidia_scraper import NvidiaScraper
from scrapers.anthropic_scraper import AnthropicScraper
from scrapers.hackernews_scraper import HackerNewsScraper

def run_all_sources():
    """
    Orchestrates the entire AI news pipeline:
    1. Instantiates all modular scrapers.
    2. Gathers and normalizes articles from each source.
    3. Performs an upsert update in Supabase.
    """
    logger.info("🚀 Starting Refactored AI & Startup Content Collector Pipeline")
    
    scrapers = [
        NvidiaScraper(),
        AnthropicScraper(),
        HackerNewsScraper()
    ]
    
    total_saved = 0
    total_scraped = 0
    
    for scraper in scrapers:
        source_name = scraper.source_name
        logger.info(f"\n--- Scraping Source: {source_name} ---")
        
        try:
            articles = scraper.scrape()
            logger.info(f"📋 Retrieved {len(articles)} normalized articles from {source_name}")
            total_scraped += len(articles)
            
            source_saved = 0
            for article in articles:
                success = save_article(article)
                if success:
                    source_saved += 1
                    
            total_saved += source_saved
            logger.info(f"✔️ Saved {source_saved}/{len(articles)} articles from {source_name}")
            
        except Exception as e:
            logger.error(f"❌ Critical pipeline error for source {source_name}: {e}")
            
    logger.info("\n==================================================")
    logger.info(f"🎉 Pipeline Completed: Scraped {total_scraped} items, successfully processed {total_saved} items.")
    logger.info("==================================================")
    
    return total_saved

if __name__ == "__main__":
    run_all_sources()
