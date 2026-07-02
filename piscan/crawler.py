import re
import time
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

class ChatbotCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def discover(self, url: str) -> List[Dict]:
        """Discover chatbot endpoints on a URL."""
        results = []
        
        # Try Playwright first (catches JS-loaded content)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(30000)
                
                # Go to page, wait for network to settle
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)  # Give widgets time to load
                
                # Get page content
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                
                # Check for Intercom
                intercom = page.evaluate("""
                    () => {
                        if (window.Intercom) return 'intercom';
                        if (document.querySelector('#intercom-container')) return 'intercom';
                        return null;
                    }
                """)
                if intercom:
                    results.append({
                        "url": url,
                        "method": "POST",
                        "confidence": "high",
                        "type": "intercom_widget",
                        "note": "Intercom chat detected"
                    })
                
                # Check for Zendesk
                zendesk = page.evaluate("""
                    () => {
                        if (document.querySelector('iframe[src*="zendesk"]')) return 'zendesk';
                        if (document.querySelector('#launcher')) return 'zendesk';
                        return null;
                    }
                """)
                if zendesk:
                    results.append({
                        "url": url,
                        "method": "POST",
                        "confidence": "high",
                        "type": "zendesk_widget",
                        "note": "Zendesk chat detected"
                    })
                
                # Check for Drift
                drift = page.evaluate("""
                    () => {
                        if (window.drift) return 'drift';
                        if (document.querySelector('#drift-widget')) return 'drift';
                        return null;
                    }
                """)
                if drift:
                    results.append({
                        "url": url,
                        "method": "POST",
                        "confidence": "high",
                        "type": "drift_widget",
                        "note": "Drift chat detected"
                    })
                
                # Parse the HTML for any chat indicators
                results.extend(self._parse_html(soup, url))
                
                # Also check network requests for API endpoints
                requests_data = page.evaluate("""
                    () => {
                        // This is a simplified version - you'd use page.on('request') in real code
                        // For now, we'll rely on HTML parsing
                        return [];
                    }
                """)
                
                browser.close()
                
        except Exception as e:
            print(f"Playwright render failed: {e}")
        
        # Remove duplicates
        unique_results = []
        seen = set()
        for r in results:
            key = r["url"]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results
    
    def _parse_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Parse HTML for chatbot endpoints."""
        results = []
        
        # Find all forms
        for form in soup.find_all("form"):
            action = form.get("action", "")
            if action:
                full_url = urljoin(base_url, action)
                if self._is_chat_endpoint(full_url):
                    results.append({
                        "url": full_url,
                        "method": form.get("method", "GET").upper(),
                        "confidence": "medium",
                        "type": "form"
                    })
        
        # Check script tags for API endpoints
        for script in soup.find_all("script"):
            if script.string:
                text = script.string
                api_patterns = [
                    r'/api/chat',
                    r'/v1/messages',
                    r'/chat/completions',
                    r'/conversation',
                    r'/widget/messages',
                    r'/api/.*chat',
                    r'/bot.*/chat',
                    r'/chatbot',
                    r'/intercom',
                    r'/zendesk',
                    r'/drift',
                ]
                for pattern in api_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        full_url = urljoin(base_url, match)
                        results.append({
                            "url": full_url,
                            "method": "POST",
                            "confidence": "high",
                            "type": "api_discovery"
                        })
        
        # Check input fields for chatbot patterns
        for input_tag in soup.find_all("input"):
            placeholder = input_tag.get("placeholder", "").lower()
            if any(word in placeholder for word in ["ask", "message", "chat", "question", "search"]):
                form = input_tag.find_parent("form")
                if form:
                    action = form.get("action", "")
                    if action:
                        full_url = urljoin(base_url, action)
                        results.append({
                            "url": full_url,
                            "method": form.get("method", "GET").upper(),
                            "confidence": "high",
                            "type": "chat_input"
                        })
        
        # Check for common chat widgets
        widget_patterns = [
            ('intercom', r'intercom', 'Intercom chat widget'),
            ('zendesk', r'zendesk', 'Zendesk chat widget'),
            ('drift', r'drift', 'Drift chat widget'),
            ('crisp', r'crisp', 'Crisp chat widget'),
            ('tawk', r'tawk', 'Tawk.to chat widget'),
            ('livechat', r'livechat', 'LiveChat widget'),
            ('chatra', r'chatra', 'Chatra widget'),
        ]
        
        for widget_name, pattern, note in widget_patterns:
            if re.search(pattern, str(soup), re.IGNORECASE):
                results.append({
                    "url": base_url,
                    "method": "POST",
                    "confidence": "high",
                    "type": f"{widget_name}_detected",
                    "note": note
                })
        
        return results
    
    def _is_chat_endpoint(self, url: str) -> bool:
        """Check if URL looks like a chat endpoint."""
        chat_patterns = [
            r'/chat',
            r'/api/v1/chat',
            r'/conversation',
            r'/message',
            r'/completion',
            r'/widget',
            r'/bot',
            r'/assistant',
            r'/intercom',
            r'/zendesk',
            r'/drift',
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in chat_patterns)