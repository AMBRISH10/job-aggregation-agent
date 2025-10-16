# extractors.py
"""
HTML extraction module for the Job Aggregation Agent.
Handles parsing of WhatsApp HTML using BeautifulSoup to extract messages and timestamps.
For scalability: This module can be extended to support parallel extraction via multiprocessing
or integrated with a message queue (e.g., RabbitMQ) for handling large volumes of HTML files asynchronously.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from utils import try_parse_datetime, clean_pre_plain, parse_pre_plain

class HTMLMessageExtractor:
    """
    Extractor class for text and timestamps from WhatsApp HTML using BeautifulSoup.
    Processes HTML tags to pull out message content and associated metadata.
    """
    
    @staticmethod
    def extract_from_tag(tag) -> Dict:
        """
        Extract text and timestamp from a single message tag.
        
        Args:
            tag: BeautifulSoup tag element.
        
        Returns:
            Dictionary with 'text' and 'timestamp' keys.
        """
        pre = tag.get('data-pre-plain-text') or tag.get('data-pre_plain_text')
        parsed = parse_pre_plain(pre)
        
        # Get visible text
        visible = tag.get_text(separator=' ', strip=True) or ''
        
        # Remove pre-plain visible part if present
        if parsed['raw']:
            raw = parsed['raw'].strip()
            if visible.startswith(raw):
                visible = visible[len(raw):].strip()
        
        ts_iso = try_parse_datetime(parsed.get('ts_str'))
        timestamp_out = ts_iso or parsed.get('ts_str')
        
        return {'text': visible, 'timestamp': timestamp_out}
    
    @staticmethod
    def extract_from_html(html_path: str) -> List[Dict]:
        """
        Extract all messages from an HTML file.
        
        Args:
            html_path: Path to the HTML file.
        
        Returns:
            List of message dictionaries.
        """
        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
        except Exception as e:
            print(f"   Error reading HTML: {e}")
            return []
        
        # Try multiple selectors for message containers
        elems = soup.find_all(attrs={'data-pre-plain-text': True})
        if not elems:
            elems = soup.find_all(attrs={'data-pre_plain_text': True})
        if not elems:
            elems = soup.select('.copyable-text') or []
        
        messages = []
        for elem in elems:
            try:
                msg = HTMLMessageExtractor.extract_from_tag(elem)
                if msg['text'] and msg['timestamp']:  # Only keep if both exist
                    messages.append(msg)
            except Exception:
                continue
        
        return messages