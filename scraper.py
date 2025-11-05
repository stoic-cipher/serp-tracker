"""
SERP scraping with anti-detection measures.
Supports both requests-based and Selenium-based scraping.
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urlparse
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class SERPScraper:
    def __init__(self, use_selenium: bool = False, proxy_service: Optional[str] = None):
        self.use_selenium = use_selenium
        self.proxy_service = proxy_service
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def search_google(
        self,
        keyword: str,
        target_domain: str,
        num_results: int = 100
    ) -> Optional[Tuple[int, str, str, str]]:
        """
        Search Google and find target domain position.
        
        Returns: (position, url, title, snippet) or None if not found
        """
        if self.use_selenium:
            return self._search_with_selenium(keyword, target_domain, num_results)
        else:
            return self._search_with_requests(keyword, target_domain, num_results)
    
    def _search_with_requests(
        self,
        keyword: str,
        target_domain: str,
        num_results: int
    ) -> Optional[Tuple[int, str, str, str]]:
        """Fast scraping using requests library."""
        
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Build Google search URL
        encoded_keyword = quote_plus(keyword)
        url = f"https://www.google.com/search?q={encoded_keyword}&num={num_results}"
        
        try:
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(2, 5))
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Parse search results
            results = self._parse_google_results(soup, target_domain)
            return results
            
        except Exception as e:
            print(f"Error scraping {keyword}: {e}")
            return None
    
    def _search_with_selenium(
        self,
        keyword: str,
        target_domain: str,
        num_results: int
    ) -> Optional[Tuple[int, str, str, str]]:
        """More reliable but slower scraping using headless Chrome."""
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.ua.random}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            encoded_keyword = quote_plus(keyword)
            url = f"https://www.google.com/search?q={encoded_keyword}&num={num_results}"
            
            driver.get(url)
            
            # Wait for results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            # Random human-like delay
            time.sleep(random.uniform(1, 3))
            
            # Get page source and parse
            soup = BeautifulSoup(driver.page_source, 'lxml')
            results = self._parse_google_results(soup, target_domain)
            
            return results
            
        except Exception as e:
            print(f"Error with Selenium for {keyword}: {e}")
            return None
        finally:
            driver.quit()
    
    def _parse_google_results(
        self,
        soup: BeautifulSoup,
        target_domain: str
    ) -> Optional[Tuple[int, str, str, str]]:
        """Parse Google SERP HTML to find target domain."""
        
        # Find all search result divs
        # Google's structure changes, so we try multiple selectors
        search_divs = soup.find_all('div', class_='g')
        
        if not search_divs:
            # Try alternative selector
            search_divs = soup.find_all('div', {'data-sokoban-container': True})
        
        position = 0
        
        for div in search_divs:
            # Find the link
            link_tag = div.find('a')
            if not link_tag or not link_tag.get('href'):
                continue
            
            url = link_tag['href']
            
            # Skip Google's own results
            if 'google.com' in url:
                continue
            
            position += 1
            
            # Extract domain from URL
            try:
                domain = urlparse(url).netloc.replace('www.', '')
            except:
                continue
            
            # Check if this is our target
            if target_domain.lower() in domain.lower():
                # Extract title
                title_tag = div.find('h3')
                title = title_tag.get_text() if title_tag else ""
                
                # Extract snippet
                snippet_div = div.find('div', {'data-sncf': '1'})
                if not snippet_div:
                    snippet_div = div.find('div', class_='VwiC3b')
                snippet = snippet_div.get_text() if snippet_div else ""
                
                return (position, url, title, snippet)
        
        return None  # Not found in results


class ScraperAPIWrapper:
    """Optional wrapper for ScraperAPI or similar services."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.scraperapi.com"
    
    def search_google(
        self,
        keyword: str,
        target_domain: str,
        num_results: int = 100
    ) -> Optional[Tuple[int, str, str, str]]:
        """Use ScraperAPI to scrape Google."""
        
        encoded_keyword = quote_plus(keyword)
        google_url = f"https://www.google.com/search?q={encoded_keyword}&num={num_results}"
        
        params = {
            'api_key': self.api_key,
            'url': google_url,
            'render': 'false'  # Set to 'true' if you need JS rendering
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Use same parsing logic
            scraper = SERPScraper()
            return scraper._parse_google_results(soup, target_domain)
            
        except Exception as e:
            print(f"ScraperAPI error for {keyword}: {e}")
            return None


def create_scraper(config: dict) -> SERPScraper:
    """Factory function to create appropriate scraper."""
    
    proxy_service = config.get('scraping', {}).get('proxy_service')
    
    if proxy_service == 'scraperapi':
        api_key = config.get('scraping', {}).get('scraperapi_key')
        if not api_key:
            print("Warning: scraperapi selected but no API key provided")
            return SERPScraper(use_selenium=False)
        return ScraperAPIWrapper(api_key)
    
    use_selenium = config.get('scraping', {}).get('use_selenium', False)
    return SERPScraper(use_selenium=use_selenium)
