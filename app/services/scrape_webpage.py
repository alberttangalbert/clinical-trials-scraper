import os
import re
import json
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

# Load environment variables from .env file
load_dotenv()

# BrightData proxy configuration
BRIGHTDATA_ENDPOINT = os.getenv("BRIGHTDATA_ENDPOINT")
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")  # May be used for API calls if needed
BRIGHTDATA_USERNAME = os.getenv("BRIGHTDATA_USERNAME")
BRIGHTDATA_ZONE_NAME = os.getenv("BRIGHTDATA_ZONE_NAME")
BRIGHTDATA_ZONE_PASSWORD = os.getenv("BRIGHTDATA_ZONE_PASSWORD")

# Global caches
url_cache: Dict[str, Dict[str, str]] = {}
html_mapping: Dict[str, str] = {}
drug_cache: Dict[str, Dict[str, str]] = {}


def load_caches() -> None:
    """
    Load existing caches (URL results, HTML mappings, and drug info) from disk.
    """
    global url_cache, html_mapping, drug_cache
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Load URL cache
    url_cache_file = os.path.join(cache_dir, "url_cache.json")
    if os.path.exists(url_cache_file):
        with open(url_cache_file, 'r') as f:
            url_cache = json.load(f)

    # Load HTML mapping cache
    mapping_file = os.path.join(cache_dir, "html_mapping.json")
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            html_mapping = json.load(f)

    # Load drug cache
    drug_cache_file = os.path.join(cache_dir, "drug_cache.json")
    if os.path.exists(drug_cache_file):
        with open(drug_cache_file, 'r') as f:
            drug_cache = json.load(f)


def save_caches() -> None:
    """
    Save current caches (URL results, HTML mappings, drug info) to disk.
    """
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Save URL cache
    with open(os.path.join(cache_dir, "url_cache.json"), 'w') as f:
        json.dump(url_cache, f, indent=2)

    # Save HTML mapping
    with open(os.path.join(cache_dir, "html_mapping.json"), 'w') as f:
        json.dump(html_mapping, f, indent=2)

    # Save drug cache
    with open(os.path.join(cache_dir, "drug_cache.json"), 'w') as f:
        json.dump(drug_cache, f, indent=2)


def get_cached_drug_info(drug_name: str) -> Optional[Dict[str, str]]:
    """
    Return cached drug information if available.

    Args:
        drug_name: Name of the drug (may include trial ID).

    Returns:
        Cached info dict or None if not found.
    """
    clean_name = re.sub(r"[^\w\-]", "", drug_name.split()[0].split(",")[0])
    if clean_name in drug_cache:
        print(f"[DEBUG] Using cached drug info for: {clean_name}")
        return drug_cache[clean_name]
    return None


def get_brightdata_proxies() -> Dict[str, str]:
    """
    Construct proxy settings for BrightData.

    Returns:
        Dictionary suitable for requests.proxies.
    """
    # Basic HTTP proxy URL with authentication
    proxy_auth = f"{BRIGHTDATA_USERNAME}:{BRIGHTDATA_ZONE_PASSWORD}"
    proxy_url = f"http://{proxy_auth}@{BRIGHTDATA_ENDPOINT}"
    return {"http": proxy_url, "https": proxy_url}


def clean_text(text: str) -> str:
    """
    Normalize text by collapsing whitespace and trimming punctuation.
    """
    text = ' '.join(text.split())
    return text.strip(' .,')


def format_results(texts: set) -> str:
    """
    Format a set of strings into a sorted, comma-separated string.
    """
    cleaned = {clean_text(t) for t in texts if clean_text(t)}
    return ', '.join(sorted(cleaned))


def extract_text_from_element(element) -> str:
    """
    Extract clean text from a BeautifulSoup element, handling links.
    """
    link = element.find('a')
    if link:
        return clean_text(link.get_text())
    return clean_text(element.get_text())


def save_to_cache(url: str, overview_html: str, drug_name: str) -> str:
    """
    Save overview section HTML to disk and update mapping.

    Args:
        url: Original page URL.
        overview_html: HTML string of the overview section.
        drug_name: Drug identifier for mapping.

    Returns:
        Filepath where HTML was stored.
    """
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    filename = re.sub(r'[^\w\-]', '_', url)
    filename = filename[:100]  # Limit length
    filepath = os.path.join(cache_dir, f"{filename}.html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(overview_html)

    html_mapping[drug_name] = filepath
    save_caches()
    print(f"[DEBUG] Saved overview HTML to {filepath}")
    return filepath


def _scrape(url: str, target_elements: List[str], drug_name: str,
            proxies: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Internal helper to perform scraping with optional proxies.
    """
    # Use cached data if available
    if url in url_cache:
        print(f"[DEBUG] Using cached content for URL: {url}")
        return url_cache[url]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    # Perform GET request (with or without proxies)
    response = requests.get(url, headers=headers, proxies=proxies)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    # Save overview section if present
    overview_div = soup.find('div', id='overview')
    if overview_div:
        save_to_cache(url, str(overview_div.prettify()), drug_name)

    results: Dict[str, str] = {}
    for element_id in target_elements:
        elements = soup.find_all(attrs={"data-testid": element_id})
        unique_texts = set()
        for elem in elements:
            # Organization tags handled specially
            if element_id == "entity-tag--organization":
                link = elem.find('a')
                if link:
                    txt = clean_text(link.get_text())
                    if txt:
                        unique_texts.add(txt)
            else:
                spans = elem.find_all(['span', 'a'], recursive=True)
                if spans:
                    for span in spans:
                        txt = extract_text_from_element(span)
                        if txt and not txt.startswith('+'):
                            unique_texts.add(txt)
                else:
                    txt = extract_text_from_element(elem)
                    if txt and not txt.startswith('+'):
                        unique_texts.add(txt)
        if unique_texts:
            results[element_id] = format_results(unique_texts)

    # Cache and persist
    url_cache[url] = results
    drug_cache[drug_name] = results
    save_caches()
    return results


def scrape_and_parse_webpage(url: str, target_elements: List[str], drug_name: str) -> Dict[str, str]:
    """
    Scrape a webpage for specified data-testid elements. Tries direct requests first,
    and falls back to BrightData proxy on failure or empty results.

    Args:
        url: URL to scrape.
        target_elements: List of data-testid attributes to extract.
        drug_name: Identifier for caching purposes.

    Returns:
        Mapping of data-testid to extracted text content.
    """
    # Attempt direct scrape
    try:
        results = _scrape(url, target_elements, drug_name)
        if results:
            return results
        # If results empty, treat as failure
        raise ValueError("Empty results, retrying with proxy.")
    except Exception as e:
        print(f"[DEBUG] Direct scrape failed: {e}")
        print("[DEBUG] Retrying via BrightData proxy...")
        proxies = get_brightdata_proxies()
        try:
            return _scrape(url, target_elements, drug_name, proxies=proxies)
        except Exception as err:
            print(f"[DEBUG] Proxy scrape also failed: {err}")
            return {}

# Initialize caches on import
load_caches()
