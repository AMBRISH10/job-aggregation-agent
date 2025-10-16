# utils.py
"""
Utility functions module for the Job Aggregation Agent.
Contains reusable helper functions for text processing, datetime parsing, and other common operations.
For scalability: These functions are stateless and pure, making them easy to parallelize or distribute
across worker processes/nodes in a multi-threaded or distributed scraping setup.
"""

import re
from datetime import datetime
from typing import Dict, Optional
from dateutil import parser as dateparser

def try_parse_datetime(dt_str: str) -> Optional[str]:
    """
    Parse a datetime string to ISO format.
    
    Args:
        dt_str: The datetime string to parse.
    
    Returns:
        ISO formatted string if successful, else None.
    """
    if not dt_str:
        return None
    
    s = dt_str.strip().replace('\u200e', '').replace('\u200f', '')
    
    for dayfirst in (False, True):
        try:
            dt = dateparser.parse(s, dayfirst=dayfirst, fuzzy=True)
            if dt:
                return dt.isoformat()
        except Exception:
            continue
    
    return None

def clean_pre_plain(raw: str) -> Optional[str]:
    """
    Clean and normalize pre-plain text by removing formatting artifacts.
    
    Args:
        raw: The raw text to clean.
    
    Returns:
        Cleaned text or None if input is None.
    """
    if raw is None:
        return None
    s = raw.strip()
    s = re.sub(r'^(?:&gt;|>)+\s*', '', s)
    s = re.sub(r'[\r\n]+', ' ', s).strip()
    return s

def parse_pre_plain(pre_raw: str) -> Dict:
    """
    Parse timestamp and sender information from pre-plain text.
    
    Args:
        pre_raw: The raw pre-plain text.
    
    Returns:
        Dictionary with 'raw' and 'ts_str' keys.
    """
    out = {'raw': pre_raw, 'ts_str': None}
    if not pre_raw:
        return out
    
    s = clean_pre_plain(pre_raw)
    
    # Format: [timestamp] sender:
    m = re.match(r'^\s*\[(?P<ts>[^\]]+)\]\s*(?P<sender>[^:]+):?\s*$', s)
    if m:
        out['ts_str'] = m.group('ts').strip()
        return out
    
    # Format: [timestamp]
    m2 = re.match(r'^\s*\[(?P<ts>[^\]]+)\]', s)
    if m2:
        out['ts_str'] = m2.group('ts').strip()
        return out
    
    # Format: HH:MM AM/PM
    m3 = re.match(r'^(?P<ts>\d{1,2}[:.]\d{2}(?:\s*(?:AM|PM|am|pm))?)', s)
    if m3:
        out['ts_str'] = m3.group('ts').strip()
        return out
    
    return out