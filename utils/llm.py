import time
from huggingface_hub import InferenceClient
from config import HF_TOKEN, PRIMARY_LLM, FALLBACK_LLM, SECONDARY_FALLBACK_LLM, logger

# Initialize client if token is available
hf_client = InferenceClient(api_key=HF_TOKEN) if HF_TOKEN else None

def rewrite_article(content: str) -> str:
    """
    Rewrites the scraped article content into a professional, human-readable format.
    Includes rate-limit retry logic and fallback models if API limits/credits are hit.
    
    Returns:
        The rewritten article text, or None if rewriting failed/could not be run.
    """
    if not hf_client:
        logger.warning("Hugging Face InferenceClient is not initialized (missing HF_TOKEN).")
        return None
        
    if not content or len(content.strip()) < 100:
        logger.warning("Content too short to rewrite, skipping.")
        return None

    # Truncate content to keep it within safe token limits for inference
    content_payload = content[:4000]
    
    prompt = f"""Rewrite the following article.

Rules:
- Use ONLY the provided content.
- Do NOT invent facts or add assumptions.
- Keep the meaning unchanged.
- Write in a professional, human-readable journalistic style.
- Maintain a structured layout of 3-5 paragraphs.

CONTENT:
{content_payload}
"""

    models = [PRIMARY_LLM, FALLBACK_LLM, SECONDARY_FALLBACK_LLM]
    
    for model in models:
        logger.info(f"🤖 Attempting article rewrite using LLM model: {model}")
        
        # Simple local retry loop per model (for transient network/rate limit issues)
        for attempt in range(2):
            try:
                response = hf_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )
                
                article_text = response.choices[0].message.content
                if article_text:
                    # Clean up formatting noise (like hashtags, markdown header symbols)
                    cleaned_text = article_text.replace("#", "").replace("*", "").strip()
                    logger.info(f"✨ Successfully rewrote article with model: {model}")
                    return cleaned_text
                    
            except Exception as e:
                err_msg = str(e).lower()
                
                # Check for rate limit or credit exhaustion issues
                is_quota_error = any(kw in err_msg for kw in ["quota", "credits", "exhausted", "429", "403", "limit"])
                
                if is_quota_error:
                    logger.warning(f"⚠️ Quota/Credit limit reached or rate limit hit on model {model}: {e}")
                    # Don't retry this model, break to proceed to the next fallback model immediately
                    break
                else:
                    logger.warning(f"⚠️ Transient error rewriting article with model {model} (Attempt {attempt+1}/2): {e}")
                    if attempt < 1:
                        time.sleep(2)  # Short delay before retry
                        
        logger.warning(f"❌ Failed to generate rewrite with model {model}. Trying next fallback...")
        
    logger.error("❌ All LLM rewriting models failed or credits were fully exhausted.")
    return None
