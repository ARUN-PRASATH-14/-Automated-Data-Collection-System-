import time
import requests
from config import DEFAULT_USER_AGENT, REQUEST_TIMEOUT, logger

def safe_request(url: str, method: str = "GET", retries: int = 3, backoff_factor: float = 1.5, **kwargs) -> requests.Response:
    """
    Makes a network request with retry logic and exponential backoff.
    """
    headers = kwargs.get("headers", {})
    if "User-Agent" not in headers:
        # Create a copy to avoid mutating default parameters/args
        headers = headers.copy()
        headers["User-Agent"] = DEFAULT_USER_AGENT
        kwargs["headers"] = headers

    if "timeout" not in kwargs:
        kwargs["timeout"] = REQUEST_TIMEOUT

    for attempt in range(retries):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                logger.error(f"HTTP {method} request failed after {retries} attempts for {url}: {e}")
                raise e
            
            sleep_time = backoff_factor ** attempt
            logger.warning(f"HTTP request to {url} failed: {e}. Retrying in {sleep_time:.2f}s (Attempt {attempt + 1}/{retries})...")
            time.sleep(sleep_time)
            
    raise requests.exceptions.RequestException(f"Failed to request {url}")

def resolve_google_news_url(url: str) -> str:
    """
    Google News RSS feeds return redirecting URLs (e.g. news.google.com/rss/articles/...).
    This function resolves the Google News redirect URL using Google's internal batchexecute API.
    """
    if "news.google.com" not in url:
        return url
        
    try:
        from bs4 import BeautifulSoup
        import json
        
        # 1. Fetch the redirect tracking page
        response = requests.get(url, timeout=10)
        if not response.ok:
            return url
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Extract the data-p attribute
        element = soup.select_one('c-wiz[data-p]')
        if not element:
            logger.warning(f"c-wiz[data-p] element not found for Google News URL: {url}")
            return url
            
        data = element.get('data-p')
        if not data:
            return url
            
        # 3. Format data to JSON structure required by Google's backend
        obj = json.loads(data.replace('%.@.', '["garturlreq",'))
        
        # 4. Prepare request payload
        payload = {
            'f.req': json.dumps([[["Fbv4je", json.dumps(obj[:-6] + obj[-2:]), "null", "generic"]]])
        }
        headers = {
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'user-agent': DEFAULT_USER_AGENT
        }
        
        # 5. POST to the batchexecute decoding API
        batch_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
        batch_resp = requests.post(batch_url, headers=headers, data=payload, timeout=10)
        
        if batch_resp.ok:
            # 6. Parse response to extract resolved URL
            cleaned = batch_resp.text.replace(")]}'", "").strip()
            data_json = json.loads(cleaned)
            array_string = data_json[0][2]
            if array_string:
                resolved_url = json.loads(array_string)[1]
                logger.info(f"Resolved Google News redirect: {url} -> {resolved_url}")
                return resolved_url
                
    except Exception as e:
        logger.warning(f"Failed to resolve Google News redirect for {url} via batchexecute: {e}. Using original URL.")
        
    return url
