import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AI-Content-Collector")

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Validate configuration
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("Supabase credentials are not fully configured. Database operations will fail.")
if not HF_TOKEN:
    logger.warning("Hugging Face token (HF_TOKEN) is not configured. AI rewriting will fail.")

# Application Constants
PRIMARY_LLM = "Qwen/Qwen2.5-72B-Instruct"
FALLBACK_LLM = "Qwen/Qwen2.5-7B-Instruct"
SECONDARY_FALLBACK_LLM = "meta-llama/Llama-3-8B-Instruct"

REQUEST_TIMEOUT = 15
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
