import re
import trafilatura
from config import logger

def clean_title(title: str) -> str:
    """
    Cleans messy article titles by removing date formats, extra whitespace,
    and trailing branding (like ' | Anthropic' or ' - Google News').
    """
    if not title:
        return ""
        
    # Remove date patterns like "Jun 15, 2026" or "June 15, 2026"
    title = re.sub(r"\b\w{3,9}\s\d{1,2},\s\d{4}", "", title)
    
    # Remove common branding suffixes
    branding_patterns = [
        r"\s*\|\s*Anthropic$",
        r"\s*-\s*NVIDIA\s+Blog$",
        r"\s*-\s*Google\s+News$",
        r"\s*\|\s*Hacker\s*News$"
    ]
    for pattern in branding_patterns:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)
        
    # Clean up double spaces and strip
    title = re.sub(r"\s+", " ", title).strip()
    return title

def extract_article_content(url: str) -> str:
    """
    Downloads and extracts the clean main article body text from a webpage URL.
    Limits output to 8,000 characters to keep it LLM-friendly.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning(f"⚠️ Trafilatura fetch returned empty for {url}")
            return ""

        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            include_links=False
        )

        if not content:
            logger.warning(f"⚠️ Trafilatura extraction returned empty for {url}")
            return ""

        return content[:8000]

    except Exception as e:
        logger.error(f"❌ Error extracting article content from {url}: {e}")
        return ""
