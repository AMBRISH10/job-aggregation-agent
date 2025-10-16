# adapters.py
"""
Source adapter module for the Job Aggregation Agent.
Defines abstract and concrete adapters for different data sources (e.g., WhatsApp channels).
Supports modular extension to new sources without altering core aggregation logic.
For scalability: Adapters follow the Adapter pattern, allowing easy addition of parallel fetchers
(e.g., using asyncio for concurrent scraping) or integration with cloud services (e.g., AWS Lambda for on-demand scraping).
"""

import os
import time
from abc import ABC, abstractmethod
from typing import List, Dict

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from config import CHROME_DRIVER_PATH, CHROME_PROFILE_DIR, DEBUG_DIR
from extractors import HTMLMessageExtractor

class SourceAdapter(ABC):
    """
    Abstract base class for data sources.
    Ensures all adapters provide a consistent fetch_posts interface.
    """
    
    def __init__(self, source_name: str):
        self.source_name = source_name
    
    @abstractmethod
    def fetch_posts(self) -> List[Dict]:
        """
        Fetch messages as {text, timestamp} dicts.
        
        Returns:
            List of message dictionaries.
        """
        pass

class WhatsAppChannelAdapter(SourceAdapter):
    """
    Adapter for scraping WhatsApp channels.
    Handles Selenium-based navigation, scrolling, and HTML export for message extraction.
    """
    
    def __init__(self, channel_url: str, source_name: str, chrome_driver_path: str, 
                 user_data_dir: str = CHROME_PROFILE_DIR):
        super().__init__(source_name)
        self.channel_url = channel_url
        self.chrome_driver_path = chrome_driver_path
        self.user_data_dir = user_data_dir
        self.html_path = None
    
    def fetch_posts(self) -> List[Dict]:
        """
        Scrape the channel, save HTML, and extract messages.
        
        Returns:
            List of extracted message dictionaries.
        """
        driver = None
        
        try:
            # Create debug directory
            os.makedirs(DEBUG_DIR, exist_ok=True)
            
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(self.chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
            print(f"\nOpening WhatsApp channel: {self.channel_url}")
            
            # Login
            driver.get("https://web.whatsapp.com")
            print("Checking WhatsApp Web login status...")
            
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: d.find_elements(By.XPATH, "//canvas[@aria-label='Scan me!']") or
                            d.find_elements(By.XPATH, "//*[@id='side']") or
                            d.find_elements(By.XPATH, "//*[@data-testid='chat-list']")
                )
                
                qr_elements = driver.find_elements(By.XPATH, "//canvas[@aria-label='Scan me!']")
                if qr_elements:
                    print("\n" + "="*70)
                    print("QR CODE DETECTED - PLEASE SCAN TO LOGIN")
                    print("="*70)
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, "//*[@id='side']"))
                    )
                    print("Successfully logged in!")
                    time.sleep(10)
                else:
                    print("Already logged in!")
            except Exception as e:
                print(f"Login error: {e}")
                return []
            
            # Navigate to channel
            print(f"\nNavigating to channel...")
            driver.get(self.channel_url)
            time.sleep(10)
            
            # Try to click "View channel" button
            view_channel_selectors = [
                "//a[contains(@class, '_9vcv') and contains(@class, '_advm')]",
                "//span[contains(@class, '_advp') and contains(text(), 'View channel')]/..",
                "//a[contains(text(), 'View channel')]",
                "//button[contains(text(), 'View channel')]",
            ]
            
            for selector in view_channel_selectors:
                try:
                    button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(2)
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(10)
                    break
                except Exception:
                    continue
            
            # Wait for message pane
            print("Waiting for messages to load...")
            try:
                messages_pane = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='conversation-panel-messages']"))
                )
                print("Message pane loaded")
            except Exception:
                messages_pane = driver.find_element(By.ID, "main")
                print("Using main container")
            
            time.sleep(15)
            
            # Scroll to load history
            print("Scrolling to load message history...")
            last_height = driver.execute_script("return arguments[0].scrollHeight", messages_pane)
            
            for attempt in range(15):
                driver.execute_script("arguments[0].scrollTop = 0;", messages_pane)
                time.sleep(5)
                new_height = driver.execute_script("return arguments[0].scrollHeight", messages_pane)
                
                if new_height == last_height:
                    print(f"Reached top after {attempt + 1} scrolls")
                    break
                
                last_height = new_height
                print(f"   Scroll {attempt + 1}/15...")
            
            time.sleep(10)
            
            # Save full page HTML
            self.html_path = f"{DEBUG_DIR}/messages_{self.source_name.replace(' ', '_')}.html"
            page_html = driver.page_source
            
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            print(f"\nSaved HTML: {self.html_path}")
            print(f"   File size: {len(page_html) / 1024:.2f} KB")
            
            # Extract messages using BeautifulSoup
            print("\nExtracting messages from HTML...")
            messages = HTMLMessageExtractor.extract_from_html(self.html_path)
            
            print(f"Extracted {len(messages)} messages with valid timestamps")
            
            if messages:
                print("\n   Sample messages:")
                for i, msg in enumerate(messages[:5]):
                    text_preview = msg['text'][:70] + "..." if len(msg['text']) > 70 else msg['text']
                    ts_preview = msg['timestamp'][:16] if msg['timestamp'] else "N/A"
                    print(f"      {i+1}. [{ts_preview}] {text_preview}")
            
            return messages
            
        except Exception as e:
            print(f"Error scraping {self.source_name}: {e}")
            import traceback
            print(traceback.format_exc())
            return []
        
        finally:
            if driver:
                driver.quit()
                print("Browser closed")