# 🚀 Job Aggregation Agent

An intelligent, modular job aggregation system that automatically collects job updates from multiple WhatsApp and Telegram channels, parses them using open-source LLMs (Ollama), and presents results on an interactive Streamlit dashboard.

---

## 📋 Project Overview

### **Objective**
Design and build a scalable AI-powered agent that:
- Collects job posts from multiple messaging channels
- Converts unstructured text into standardized job templates
- Deduplicates similar postings across sources
- Displays aggregated data on an interactive dashboard
- Scales to support new content types and delivery methods

### **Key Features**
✅ **Modular Architecture** — Easy to add new sources, parsers, and delivery methods  
✅ **LLM-Powered Parsing** — Uses Ollama for intelligent job extraction  
✅ **Smart Deduplication** — Identifies duplicate jobs across channels  
✅ **Interactive Dashboard** — Real-time filtering, statistics, and visualizations  
✅ **SQLite Backend** — Lightweight, portable database  
✅ **Production-Ready** — Clean code, comprehensive documentation, extensible design  

---

## 🏗️ Architecture

### **Modular Component Design**

The system follows a **plugin-based architecture** with clear separation of concerns:

```
DATA SOURCES (WhatsApp, Telegram, Future Platforms)
         ↓
    SOURCE ADAPTERS (Abstract base class + implementations)
         ↓
    RAW JOB TEXT EXTRACTION
         ↓
    OLLAMA LLM PARSER (Structured JSON output)
         ↓
    STANDARDIZED JOB TEMPLATE (JobPost dataclass)
         ↓
    SQLite DATABASE (Storage + Deduplication)
         ↓
    STREAMLIT DASHBOARD (UI + Analytics)
```

### **Component Breakdown**

**1. Source Adapters (Pluggable)**
- `SourceAdapter` — Abstract base class defining interface
- `WhatsAppChannelAdapter` — Fetches from WhatsApp channels (Selenium)

**2. LLM Integration (Ollama)**
- Uses open-source models (gpt-oss, Mistral, Llama 2, etc.)
- Structured JSON extraction with prompt engineering
- Fallback mechanisms for parsing errors
- Low latency, no API keys required

**3. Data Models**
- `JobPost` — Standardized dataclass with fields:
  - `role`, `company_name`, `location`
  - `experience_required`, `job_type`
  - `application_link`, `description`
  - `source`, `posted_date`, `post_id`

**4. Database Layer**
- SQLite for portability and simplicity
- Deduplication using MD5 hash of (company, role, location)
- Duplicate detection table for analytics
- Optional vector-based similarity (future enhancement)

**5. Dashboard**
- Streamlit for rapid UI development
- Real-time filtering and search
- Statistics and visualizations
- Multiple view modes (Cards/Table)

---

## 💻 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.8+ |
| **Web Scraping** | Selenium WebDriver |
| **LLM** | Ollama (Local OSS Models) |
| **Database** | SQLite3 |
| **Dashboard** | Streamlit |
| **Data Processing** | Pandas |
| **Parsing** | JSON, Regex |

---

## 📦 Installation & Setup

### **Prerequisites**
- Python 3.8 or higher
- Ollama installed and running ([Download here](https://ollama.ai))
- Chrome/Chromium browser (for Selenium)

### **Step 1: Install Dependencies**

```bash
# Clone repository
git clone <your-repo-url>
cd job-aggregation-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### **Step 2: Setup Ollama**

```bash
# Download and install Ollama from https://ollama.ai

# Start Ollama server
ollama serve

# In another terminal, pull a model
ollama pull mistral  # Or: llama2, neural-chat, etc.

# Verify it's running
curl http://localhost:11434/api/tags
```

### **Step 3: Configure Application**

Edit `config.py` (or create it):

```python
# config.py
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"
DATABASE_PATH = "jobs.db"
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"  # Adjust for your OS
```

### **Step 4: Run the Application**

```bash
# Terminal 1: Start the aggregation (one-time or scheduled)
python main.py

# Terminal 2: Launch the Streamlit dashboard
streamlit run dashboard.py
```

The dashboard will open at `http://localhost:8501`

---

## 🚀 Usage

### **1. Collecting Jobs (Aggregation)**

```python
from main import JobAggregator, MockSourceAdapter

# Initialize
aggregator = JobAggregator()

# Add sources
aggregator.add_source(MockSourceAdapter("Test Channel 1"))

# Run aggregation
aggregator.aggregate()
# Output: "✓ Added: Python Developer at TechCorp"
#         "⊗ Duplicate: Data Engineer at DataSystems Inc"
```

### **2. Adding New Data Sources**

Create a custom adapter:

```python
from main import SourceAdapter

class GitHubJobsAdapter(SourceAdapter):
    def __init__(self):
        super().__init__("GitHub Jobs")
    
    def fetch_posts(self):
        # Your scraping logic here
        return ["Senior DevOps Engineer..."]

# Register it
aggregator.add_source(GitHubJobsAdapter())
```

### **3. Scheduling Regular Aggregations**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from main import initialize_aggregator

def scheduled_job():
    aggregator = initialize_aggregator()
    aggregator.aggregate()

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, 'interval', hours=6)
scheduler.start()
```

### **4. Querying Jobs Programmatically**

```python
from main import JobDatabase

db = JobDatabase()

# Get all remote jobs
jobs = db.get_all_jobs({"job_type": "Remote"})

# Get jobs in Bangalore
jobs = db.get_all_jobs({"location": "Bangalore"})

# Combine filters
jobs = db.get_all_jobs({
    "job_type": "Hybrid",
    "location": "Mumbai"
})
```

---

## 📊 Dashboard Features

### **Statistics**
- **Total Jobs** — Complete job count
- **Jobs Today** — Daily aggregation count
- **Remote Jobs** — Filter by type
- **Active Sources** — Number of data sources

### **Visualizations**
- **Jobs by Type** — Bar chart (Remote, On-site, Hybrid)
- **Jobs by Source** — Channel distribution
- **Top Hiring Companies** — Most active recruiters

### **Filtering**
- Job Type (Remote/On-site/Hybrid)
- Location (text search)
- Company Name (text search)
- Experience Level
- Source Channel

### **View Modes**
- **Card View** — Rich, readable job cards with badges
- **Table View** — Spreadsheet-style for bulk review

---

## 🔧 Extensibility Examples

### **Adding Email Source**
```python
class EmailJobsAdapter(SourceAdapter):
    def __init__(self, email_account):
        super().__init__("Email Jobs")
        self.email = email_account
    
    def fetch_posts(self):
        # Connect to email and extract job emails
        pass
```

### **Adding RSS Feed Source**
```python
class RSSFeedAdapter(SourceAdapter):
    def __init__(self, feed_url):
        super().__init__(f"RSS: {feed_url}")
        self.feed_url = feed_url
    
    def fetch_posts(self):
        # Parse RSS feed
        pass
```

### **Changing Output (WhatsApp Delivery)**
```python
from twilio.rest import Client

def send_jobs_to_whatsapp(jobs: List[JobPost], phone: str):
    client = Client(account_sid, auth_token)
    
    for job in jobs:
        message = f"""
        *{job.role}*
        {job.company_name} | {job.location}
        Experience: {job.experience_required}
        Apply: {job.application_link}
        """
        client.messages.create(
            from_=f"whatsapp:{twilio_number}",
            to=f"whatsapp:{phone}",
            body=message
        )
```

---

## 📝 requirements.txt

```
selenium==4.15.0
requests==2.31.0
pandas==2.0.0
streamlit==1.28.0
pydantic==2.0.0
apscheduler==3.10.4
```
