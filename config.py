"""
Configuration for Job Aggregation Agent
Real extraction from WhatsApp channels with your Chrome driver and Ollama setup
"""

import os
from pathlib import Path
import requests

# ============================================================================
# YOUR CUSTOM CONFIGURATION
# ============================================================================

# Your Chrome driver location (IMPORTANT: Use your actual path)
CHROME_DRIVER_PATH = "/home/ambrish/Desktop/job-aggregation-agent/chromedriver-linux64/chromedriver"

# Your Ollama model (gpt-oss or any other installed model)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss")

# Ollama server
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Database location
DATABASE_PATH = os.getenv("DB_PATH", "jobs.db")

# ============================================================================
# REAL WHATSAPP CHANNELS TO MONITOR
# ============================================================================

WHATSAPP_CHANNELS = [
    {
        "name": "WhatsApp Jobs Channel 1",
        "url": "https://whatsapp.com/channel/0029Va6I79K60eBfQ92DwH0W",
        "enabled": True,
    },
    {
        "name": "WhatsApp Jobs Channel 2",
        "url": "https://whatsapp.com/channel/0029VaITGBX3AzNRgmw8YF3T",
        "enabled": True,
    },
    {
        "name": "WhatsApp Jobs Channel 3",
        "url": "https://whatsapp.com/channel/0029VaMEPPU89incD3YzsI3R",
        "enabled": True,
    },
]

# ============================================================================
# TELEGRAM CONFIGURATION (Optional)
# ============================================================================

# To use Telegram, set these environment variables:
# export TELEGRAM_API_ID=your_api_id
# export TELEGRAM_API_HASH=your_api_hash
# export TELEGRAM_PHONE=+1234567890
# Get these from: https://my.telegram.org/apps

TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "False").lower() == "true"
TELEGRAM_CHANNELS = [
    "@jobs_channel_1",
    "@jobs_channel_2",
]

# ============================================================================
# CHROME/SELENIUM CONFIGURATION
# ============================================================================

SELENIUM_CONFIG = {
    "chrome_driver_path": CHROME_DRIVER_PATH,
    "headless": False,  # Set to True if you don't want to see browser
    "window_size": (1920, 1080),
    "timeout": 15,  # Wait time for elements to load
    "scroll_attempts": 5,  # How many times to scroll for more messages
    "scroll_pause": 2,  # Seconds to wait between scrolls
}

# ============================================================================
# OLLAMA/LLM CONFIGURATION
# ============================================================================

OLLAMA_CONFIG = {
    "url": OLLAMA_URL,
    "model": OLLAMA_MODEL,
    "temperature": 0.1,  # Lower = more consistent, Higher = more creative
    "top_p": 0.9,
    "timeout": 60,  # Seconds to wait for LLM response
    "num_predict": 256,  # Max tokens in response
}

# ============================================================================
# DATA EXTRACTION CONFIGURATION
# ============================================================================

EXTRACTION_CONFIG = {
    "min_message_length": 30,  # Don't process messages shorter than this
    "max_messages_per_channel": 200,  # Maximum messages to extract per run
    "validate_required_fields": True,  # Require role and company name
}

# ============================================================================
# DEDUPLICATION CONFIGURATION
# ============================================================================

DEDUPLICATION_CONFIG = {
    "strategy": "tuple",  # Options: "tuple" (fast, company+role+location)
    "tuple_fields": ["company_name", "role", "location"],
    "similarity_threshold": 0.85,
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_CONFIG = {
    "path": DATABASE_PATH,
    "auto_vacuum": True,
    "journal_mode": "WAL",  # Write-Ahead Logging for better concurrency
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "[{time:%Y-%m-%d %H:%M:%S}] {level: <8} | {message}",
    "file": "aggregation.log",
}

# ============================================================================
# SETUP VERIFICATION FUNCTIONS
# ============================================================================

def verify_chrome_driver():
    """Verify Chrome driver exists and is executable"""
    path = Path(CHROME_DRIVER_PATH)
    
    if not path.exists():
        print(f"❌ Chrome driver not found at: {CHROME_DRIVER_PATH}")
        print(f"   Download from: https://chromedriver.chromium.org/")
        return False
    
    if not os.access(CHROME_DRIVER_PATH, os.X_OK):
        print(f"⚠️  Chrome driver exists but is not executable")
        print(f"   Run: chmod +x {CHROME_DRIVER_PATH}")
        return False
    
    print(f"✅ Chrome driver: {CHROME_DRIVER_PATH}")
    return True


def verify_ollama():
    """Verify Ollama server is running and has gpt-oss model"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Ollama server returned status {response.status_code}")
            return False
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "").split(":")[0] for m in models]
        
        if OLLAMA_MODEL.split(":")[0] in model_names or any(OLLAMA_MODEL in m for m in model_names):
            print(f"✅ Ollama running with model: {OLLAMA_MODEL}")
            return True
        else:
            print(f"❌ Model '{OLLAMA_MODEL}' not found in Ollama")
            print(f"   Available models: {', '.join(model_names)}")
            print(f"   Pull model with: ollama pull {OLLAMA_MODEL}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print(f"   Start Ollama with: ollama serve")
        return False


def verify_database():
    """Verify database path is writable"""
    try:
        db_dir = Path(DATABASE_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write
        test_path = db_dir / ".write_test"
        test_path.touch()
        test_path.unlink()
        
        print(f"✅ Database path: {DATABASE_PATH}")
        return True
    except:
        print(f"❌ Cannot write to database path: {DATABASE_PATH}")
        return False


def verify_python_version():
    """Verify Python 3.8+"""
    import sys
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} (need 3.8+)")
        return False


def verify_setup():
    """Run all setup verifications"""
    print("\n" + "="*70)
    print("🔍 SETUP VERIFICATION")
    print("="*70 + "\n")
    
    checks = {
        "Python Version": verify_python_version(),
        "Chrome Driver": verify_chrome_driver(),
        "Ollama Server": verify_ollama(),
        "Database Path": verify_database(),
    }
    
    print("\n" + "="*70)
    
    all_good = all(checks.values())
    
    if all_good:
        print("✅ All checks passed! Ready to extract real job data.\n")
        print("Next steps:")
        print("1. Run: python main.py")
        print("2. Monitor browser window for WhatsApp loading")
        print("3. View results: streamlit run dashboard.py\n")
    else:
        print("⚠️  Please fix the issues above before running.\n")
    
    print("="*70 + "\n")
    
    return all_good


# ============================================================================
# QUICK START INFO
# ============================================================================

QUICK_START = """
REAL JOB EXTRACTION SETUP
========================

Your Configuration:
  Chrome Driver: {chrome_driver}
  Ollama Model: {ollama_model}
  Ollama URL: {ollama_url}
  Database: {database}
  WhatsApp Channels: {channels_count}

Prerequisites:
  ✓ Chrome driver at: {chrome_driver}
  ✓ Ollama running at: {ollama_url}
  ✓ Model '{ollama_model}' installed

IMPORTANT NOTES:
================

1. WhatsApp Web Login (Required):
   - The browser will open automatically
   - You MUST be logged into WhatsApp Web on that browser
   - Or the channels must be PUBLIC
   - If prompted, scan QR code with your phone

2. Ollama Model Setup:
   - Start Ollama: ollama serve
   - Pull model: ollama pull gpt-oss
   - Verify: curl http://localhost:11434/api/tags

3. Running Real Extraction:
   - python main.py
   - Browser will open, messages will be scraped
   - Ollama will parse each message
   - Results saved to jobs.db

4. Viewing Results:
   - streamlit run dashboard.py
   - Visit http://localhost:8501

How It Works:
=============

1. Selenium launches Chrome browser
2. Navigates to WhatsApp channel URL
3. Waits for messages to load
4. Scrolls to load more messages (5 times)
5. Extracts all message text
6. For each message:
   - Sends to Ollama LLM
   - Parses JSON response
   - Validates job data
   - Saves to SQLite
7. Deduplicates similar jobs
8. Browser closes automatically
""".format(
    chrome_driver=CHROME_DRIVER_PATH,
    ollama_model=OLLAMA_MODEL,
    ollama_url=OLLAMA_URL,
    database=DATABASE_PATH,
    channels_count=len([c for c in WHATSAPP_CHANNELS if c["enabled"]])
)

# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    print(QUICK_START)
    print("\nRunning setup verification...")
    verify_setup()