"""
Scalable Intelligent Job Aggregation Agent
Real data extraction from WhatsApp channels
"""

import os
import json
import sqlite3
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import hashlib
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service



# CONFIGURATION


CHROME_DRIVER_PATH = "/home/ambrish/Desktop/job-aggregation-agent/chromedriver-linux64/chromedriver"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss")
DATABASE_PATH = "jobs.db"

# WhatsApp channels to monitor (REAL channels)
CHANNELS = {
    "WhatsApp": [
        {
            "name": "WhatsApp Channel 1",
            "url": "https://whatsapp.com/channel/0029Va6I79K60eBfQ92DwH0W",
            "enabled": True,
        },
        {
            "name": "WhatsApp Channel 2",
            "url": "https://whatsapp.com/channel/0029VaITGBX3AzNRgmw8YF3T",
            "enabled": True,
        },
        {
            "name": "WhatsApp Channel 3",
            "url": "https://whatsapp.com/channel/0029VaMEPPU89incD3YzsI3R",
            "enabled": True,
        },
    ],
}


# DATA MODELS


@dataclass
class JobPost:
    """Standardized job post template"""
    role: str
    company_name: str
    location: str
    experience_required: Optional[str]
    job_type: Optional[str]  # Remote, On-site, Hybrid
    application_link: Optional[str]
    description: Optional[str]
    source: str  # Channel name
    posted_date: str
    extracted_at: str
    post_id: str  # Unique hash for deduplication
    
    def to_dict(self):
        return asdict(self)



# SOURCE ADAPTERS (MODULAR)


class SourceAdapter(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
    
    @abstractmethod
    def fetch_posts(self) -> List[str]:
        """Fetch raw job posts from source"""
        pass


"""
Updated WhatsApp Channel Adapter with Chrome Profile Support
This allows reusing your logged-in WhatsApp session
"""

import time
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service


class WhatsAppChannelAdapter(SourceAdapter):
    """Real extraction from WhatsApp channels using Selenium with profile reuse"""
    
    def __init__(self, channel_url: str, source_name: str, chrome_driver_path: str, 
                 user_data_dir: str = "/home/ambrish/selenium-profile"):
        self.source_name = source_name
        self.channel_url = channel_url
        self.chrome_driver_path = chrome_driver_path
        self.user_data_dir = user_data_dir
    
    def fetch_posts(self) -> List[str]:
        """Scrape real WhatsApp channel posts using Selenium with persistent profile"""
        posts = []
        driver = None
        
        try:
            # Configure Chrome options with user profile
            options = webdriver.ChromeOptions()
            
            # CRITICAL: Use existing Chrome profile to maintain WhatsApp login
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument("--profile-directory=Default")  # Use default profile
            
            # Remote debugging port (use unique port if running multiple instances)
            options.add_argument("--remote-debugging-port=9222")
            
            # Standard options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Disable automation flags to avoid detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Optional: Disable images for faster loading
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # options.add_experimental_option("prefs", prefs)
            
            # Initialize Chrome driver with profile
            service = Service(self.chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
            print(f"\n🔗 Opening WhatsApp channel: {self.channel_url}")
            print(f"📂 Using profile: {self.user_data_dir}")
            
            # First, navigate to WhatsApp Web to ensure login
            driver.get("https://web.whatsapp.com")
            print("⏳ Checking WhatsApp Web login status...")
            
            # Wait for WhatsApp to load (either QR code or chat interface)
            try:
                # Wait for either QR code or main chat interface
                WebDriverWait(driver, 20).until(
                    lambda d: d.find_elements(By.XPATH, "//canvas[@aria-label='Scan me!']") or
                             d.find_elements(By.XPATH, "//*[@id='side']") or
                             d.find_elements(By.XPATH, "//*[@data-testid='chat-list']")
                )
                
                # Check if QR code is present
                qr_elements = driver.find_elements(By.XPATH, "//canvas[@aria-label='Scan me!']")
                if qr_elements:
                    print("\n" + "="*70)
                    print("⚠️  QR CODE DETECTED - PLEASE SCAN TO LOGIN")
                    print("="*70)
                    print("1. Scan the QR code with your phone")
                    print("2. Wait for WhatsApp Web to load")
                    print("3. The script will continue automatically...")
                    print("="*70 + "\n")
                    
                    # Wait for user to scan QR code (max 60 seconds)
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, "//*[@id='side']"))
                    )
                    print("✅ Successfully logged in to WhatsApp Web!")
                    time.sleep(3)  # Give time for chats to load
                else:
                    print("✅ Already logged in to WhatsApp Web!")
                    
            except Exception as e:
                print(f"❌ WhatsApp Web login timeout or error: {str(e)}")
                print("   Please make sure you're logged in to WhatsApp Web")
                return []
            
            # Now navigate to the specific channel
            print(f"\n🔗 Navigating to channel: {self.source_name}")
            driver.get(self.channel_url)
            
            # Wait for page to load and check for "View channel" button
            print("⏳ Checking for 'View channel' button...")
            time.sleep(3)
            
            try:
                # Try to find and click "View channel" button
                view_channel_selectors = [
                    # Based on the HTML structure you provided
                    "//a[contains(@class, '_9vcv') and contains(@class, '_advm')]",
                    "//span[contains(@class, '_advp') and contains(@class, '_aeam') and contains(text(), 'View channel')]/..",
                    "//a[@title='Use WhatsApp Web' and contains(., 'View channel')]",
                    "//span[text()='View channel']/parent::a",
                    "//a[contains(@href, 'channel_invite_code')]",
                    # Fallback selectors
                    "//button[contains(text(), 'View channel')]",
                    "//div[contains(text(), 'View channel')]",
                    "//a[contains(text(), 'View channel')]",
                ]
                
                button_clicked = False
                for idx, selector in enumerate(view_channel_selectors):
                    try:
                        print(f"   Trying selector {idx + 1}/{len(view_channel_selectors)}...", end=" ")
                        button = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        
                        # Scroll button into view
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        
                        # Try to click
                        try:
                            button.click()
                        except:
                            # If regular click fails, try JavaScript click
                            driver.execute_script("arguments[0].click();", button)
                        
                        print("✅ Success!")
                        button_clicked = True
                        time.sleep(3)  # Wait for channel to load
                        break
                    except Exception as e:
                        print("✗")
                        continue
                
                if not button_clicked:
                    print("⚠️  'View channel' button not found, proceeding anyway...")
                    
            except Exception as e:
                print(f"⚠️  Error checking for 'View channel' button: {str(e)}")
            
            # Wait for channel messages to load
            print("⏳ Waiting for messages to load...")
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@class, 'message') or contains(@class, 'msg') or @data-testid='msg-container']")
                    )
                )
            except Exception as e:
                print(f"⚠️  Timeout waiting for messages: {str(e)}")
                print("   The channel might be loading slowly or unavailable")
            
            time.sleep(3)  # Extra wait for messages to render
            
            # Scroll down to load more messages
            print("📜 Scrolling to load more messages...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 5
            
            for scroll_attempt in range(max_scrolls):
                # Scroll down
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(2)
                
                # Check for new messages
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print(f"✓ Reached end of messages after {scroll_attempt + 1} scrolls")
                    break
                last_height = new_height
                scroll_attempts += 1
                print(f"   Scroll {scroll_attempt + 1}/{max_scrolls}...")
            
            # Extract all messages with multiple selectors
            print("📥 Extracting messages...")
            message_selectors = [
                "//div[@data-testid='msg-container']//span[@dir='auto']",
                "//div[@data-testid='msg-container']//span[@class='selectable-text']",
                "//div[contains(@class, 'message-in')]//span[@dir='ltr']",
                "//div[contains(@class, 'message-out')]//span[@dir='ltr']",
                "//div[@role='row']//span[@dir='auto']",
                "//span[contains(@class, 'selectable-text') and @dir='ltr']",
            ]
            
            messages = []
            for selector in message_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 30:  # Filter short messages
                            messages.append(text)
                except Exception as e:
                    pass
            
            # Remove duplicates while preserving order
            seen = set()
            unique_messages = []
            for msg in messages:
                if msg not in seen:
                    seen.add(msg)
                    unique_messages.append(msg)
            
            posts = unique_messages
            print(f"✓ Extracted {len(posts)} unique messages from {self.source_name}")
            
            # Save screenshot for debugging (optional)
            try:
                screenshot_path = f"debug_{self.source_name.replace(' ', '_')}.png"
                driver.save_screenshot(screenshot_path)
                print(f"📸 Screenshot saved: {screenshot_path}")
            except:
                pass
            
        except Exception as e:
            print(f"❌ Error scraping {self.source_name}: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
        
        finally:
            if driver:
                driver.quit()
                print(f"🔒 Browser closed for {self.source_name}")
        
        return posts



# UPDATED CONFIGURATION


CHROME_DRIVER_PATH = "/home/ambrish/Desktop/job-aggregation-agent/chromedriver-linux64/chromedriver"
CHROME_PROFILE_DIR = "/home/ambrish/selenium-profile"  # Your Chrome profile directory

# Usage example in initialize_aggregator function:
"""
def initialize_aggregator() -> JobAggregator:
    aggregator = JobAggregator()
    
    for channel in CHANNELS["WhatsApp"]:
        if channel["enabled"]:
            adapter = WhatsAppChannelAdapter(
                channel_url=channel["url"],
                source_name=channel["name"],
                chrome_driver_path=CHROME_DRIVER_PATH,
                user_data_dir=CHROME_PROFILE_DIR  # Add this parameter
            )
            aggregator.add_source(adapter)
    
    return aggregator
"""




# LLM INTEGRATION (Ollama with gpt-oss model)


class OllamaJobParser:
    """Parse job posts using Ollama LLM (gpt-oss model)"""
    
    def __init__(self, model_name: str = "gpt-oss", ollama_url: str = OLLAMA_URL):
        self.model_name = model_name
        self.ollama_url = ollama_url
    
    def parse_job_post(self, raw_text: str, source: str) -> Optional[Dict]:
        """Extract structured job info from raw text using Ollama gpt-oss"""
        
        prompt = f"""Extract job information from this text and return ONLY valid JSON (no markdown, no comments):
{{
    "role": "Job title",
    "company_name": "Company name",
    "location": "Location",
    "experience_required": "Years/Experience level or null",
    "job_type": "Remote/On-site/Hybrid or null",
    "application_link": "URL or contact or null",
    "description": "Brief summary"
}}

Text: {raw_text}

Return ONLY the JSON object, nothing else."""
        
        try:
            print(f"   🤖 Parsing with {self.model_name}...", end=" ", flush=True)
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 256,
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                
                # Extract JSON from response
                try:
                    # Find JSON object in response
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        parsed = json.loads(json_str)
                        print("✓")
                        return parsed
                    else:
                        print("✗ (No JSON found)")
                        return None
                        
                except json.JSONDecodeError as e:
                    print(f"✗ (JSON error: {str(e)[:30]})")
                    return None
            else:
                print(f"✗ (HTTP {response.status_code})")
                return None
                
        except requests.exceptions.Timeout:
            print("✗ (Timeout)")
            return None
        except requests.exceptions.ConnectionError:
            print("✗ (Connection failed - is Ollama running?)")
            return None
        except Exception as e:
            print(f"✗ (Error: {str(e)[:30]})")
            return None



# DATABASE LAYER


class JobDatabase:
    """SQLite database for job storage and deduplication"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                role TEXT NOT NULL,
                company_name TEXT NOT NULL,
                location TEXT,
                experience_required TEXT,
                job_type TEXT,
                application_link TEXT,
                description TEXT,
                source TEXT,
                posted_date TEXT,
                extracted_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_post_id TEXT,
                duplicate_post_id TEXT,
                similarity_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_job(self, job: JobPost) -> bool:
        """Insert job into database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO jobs 
                (post_id, role, company_name, location, experience_required, 
                 job_type, application_link, description, source, posted_date, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.post_id, job.role, job.company_name, job.location,
                job.experience_required, job.job_type, job.application_link,
                job.description, job.source, job.posted_date, job.extracted_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate post_id
    
    def get_all_jobs(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Retrieve jobs with optional filters"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if filters:
            if filters.get("job_type"):
                query += " AND job_type = ?"
                params.append(filters["job_type"])
            if filters.get("location"):
                query += " AND location LIKE ?"
                params.append(f"%{filters['location']}%")
            if filters.get("company_name"):
                query += " AND company_name LIKE ?"
                params.append(f"%{filters['company_name']}%")
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def get_job_count(self) -> int:
        """Get total job count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def deduplicate_jobs(self, threshold: float = 0.8):
        """Simple deduplication based on (company, role, location)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find duplicates
        cursor.execute('''
            SELECT j1.id, j2.id, j1.post_id, j2.post_id
            FROM jobs j1, jobs j2
            WHERE j1.id < j2.id
            AND j1.company_name = j2.company_name
            AND j1.role = j2.role
            AND j1.location = j2.location
        ''')
        
        duplicates = cursor.fetchall()
        
        # Mark newer duplicates for review
        for dup in duplicates:
            cursor.execute('''
                INSERT OR IGNORE INTO duplicates (original_post_id, duplicate_post_id, similarity_score)
                VALUES (?, ?, ?)
            ''', (dup[2], dup[3], threshold))
        
        conn.commit()
        conn.close()
        
        return len(duplicates)



# JOB AGGREGATOR ENGINE


class JobAggregator:
    """Main orchestrator for the job aggregation system"""
    
    def __init__(self, db_path: str = DATABASE_PATH, ollama_url: str = OLLAMA_URL):
        self.db = JobDatabase(db_path)
        self.parser = OllamaJobParser(model_name=OLLAMA_MODEL, ollama_url=ollama_url)
        self.sources: List[SourceAdapter] = []
    
    def add_source(self, source: SourceAdapter):
        """Register a new data source"""
        self.sources.append(source)
    
    def process_post(self, raw_text: str, source_name: str) -> Optional[JobPost]:
        """Convert raw text to structured JobPost"""
        
        # Parse using Ollama
        parsed_data = self.parser.parse_job_post(raw_text, source_name)
        
        if not parsed_data:
            return None
        
        # Validate required fields
        if not parsed_data.get("role") or not parsed_data.get("company_name"):
            return None
        
        # Generate unique post_id
        post_hash = hashlib.md5(
            f"{parsed_data.get('company_name')}{parsed_data.get('role')}{parsed_data.get('location')}".encode()
        ).hexdigest()
        
        job = JobPost(
            role=str(parsed_data.get("role", "Unknown")).strip(),
            company_name=str(parsed_data.get("company_name", "Unknown")).strip(),
            location=str(parsed_data.get("location", "Unknown")).strip(),
            experience_required=parsed_data.get("experience_required"),
            job_type=parsed_data.get("job_type"),
            application_link=parsed_data.get("application_link"),
            description=parsed_data.get("description"),
            source=source_name,
            posted_date=datetime.now().isoformat(),
            extracted_at=datetime.now().isoformat(),
            post_id=post_hash
        )
        
        return job
    
    def aggregate(self):
        """Main aggregation pipeline - REAL DATA EXTRACTION"""
        print("\n" + "="*70)
        print("🚀 STARTING REAL JOB AGGREGATION FROM LIVE CHANNELS")
        print("="*70)
        
        new_jobs_count = 0
        total_posts_processed = 0
        
        for source in self.sources:
            print(f"\n{'─'*70}")
            print(f"📡 Processing source: {source.source_name}")
            print(f"{'─'*70}")
            
            raw_posts = source.fetch_posts()
            print(f"\n📊 Found {len(raw_posts)} messages to process\n")
            
            for idx, raw_post in enumerate(raw_posts, 1):
                total_posts_processed += 1
                print(f"[{idx}/{len(raw_posts)}] Processing message ({len(raw_post)} chars)...")
                
                job = self.process_post(raw_post, source.source_name)
                
                if job:
                    if self.db.insert_job(job):
                        new_jobs_count += 1
                        print(f"    ✅ Added: {job.role} at {job.company_name} ({job.location})")
                    else:
                        print(f"    ⚠️  Duplicate: {job.role} at {job.company_name}")
                else:
                    print(f"    ❌ Failed to parse (invalid/incomplete data)")
        
        # Deduplicate
        print(f"\n{'─'*70}")
        print("🔄 Running deduplication...")
        dup_count = self.db.deduplicate_jobs()
        print(f"✓ Found {dup_count} potential duplicates")
        
        # Summary
        print(f"\n{'='*70}")
        print("📈 AGGREGATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total messages processed: {total_posts_processed}")
        print(f"New jobs added: {new_jobs_count}")
        print(f"Total jobs in database: {self.db.get_job_count()}")
        print(f"{'='*70}\n")
        
        return new_jobs_count



# INITIALIZATION


def initialize_aggregator() -> JobAggregator:
    """Set up the aggregator with REAL data sources"""
    
    aggregator = JobAggregator()
    
    # Add REAL WhatsApp channels with profile support
    for channel in CHANNELS["WhatsApp"]:
        if channel["enabled"]:
            adapter = WhatsAppChannelAdapter(
                channel_url=channel["url"],
                source_name=channel["name"],
                chrome_driver_path=CHROME_DRIVER_PATH,
                user_data_dir=CHROME_PROFILE_DIR  # NEW: Use persistent profile
            )
            aggregator.add_source(adapter)
    
    return aggregator


if __name__ == "__main__":
    print(f"\n🔍 Checking Ollama connection ({OLLAMA_MODEL})...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running!")
        else:
            print(f"❌ Ollama server returned status {response.status_code}")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Start it with: ollama serve")
        exit(1)
    
    aggregator = initialize_aggregator()
    aggregator.aggregate()