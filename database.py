from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, logger

# Initialize Supabase client
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    supabase = None

def get_supabase_client():
    return supabase

def save_article(article: dict) -> bool:
    """
    Saves an article to Supabase.
    If the article already exists (by URL), updates the record.
    If the new article doesn't have a rewrite but the database already does,
    it preserves the existing rewrite.
    
    Returns:
        True if successfully saved/updated, False otherwise.
    """
    if not supabase:
        logger.error("Supabase client is not initialized. Cannot save article.")
        return False
        
    url = article.get("url")
    if not url:
        logger.error("Article missing URL, skipping insertion.")
        return False
        
    try:
        # Check if article exists
        existing = (
            supabase.table("articles")
            .select("id, rewritten_article")
            .eq("url", url)
            .execute()
        )
        
        if existing.data:
            # Article exists: perform update
            db_row = existing.data[0]
            db_id = db_row.get("id")
            
            # If the database already has a rewrite but the incoming article does not, preserve it
            if db_row.get("rewritten_article") and not article.get("rewritten_article"):
                article["rewritten_article"] = db_row["rewritten_article"]
                
            # Perform update on matching ID
            supabase.table("articles").update(article).eq("id", db_id).execute()
            logger.info(f"🔄 Updated existing article: {article.get('title')}")
            return True
        else:
            # Article is new: perform insert
            supabase.table("articles").insert(article).execute()
            logger.info(f"✅ Inserted new article: {article.get('title')}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to save article '{article.get('title')}': {e}")
        return False
