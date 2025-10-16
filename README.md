# Job Aggregation Agent

A modular job aggregation system that collects job listings from WhatsApp and Telegram channels, extracts relevant information using open-source large language models (via Ollama), and presents the results in a Streamlit dashboard.

---

## Overview

### Objective

This project aims to build a scalable, AI-powered agent that:

- Aggregates job posts from multiple messaging channels
- Extracts structured data from unstructured text
- Identifies and removes duplicates
- Displays job data through an interactive dashboard
- Supports future extensibility with new sources and delivery methods

### Key Features

- **Modular Architecture** – Add or modify data sources with ease
- **LLM-Based Parsing** – Uses Ollama for job info extraction
- **Deduplication Logic** – Avoids repeated listings
- **Streamlit Dashboard** – View, filter, and analyze job listings
- **SQLite Storage** – Lightweight and easy to manage
- **Production-Ready** – Clean codebase, extendable design

---

## Architecture

The system is built with a plugin-based architecture:

Data Sources (WhatsApp, Telegram)
↓
Source Adapters (custom fetchers)
↓
Unstructured Text
↓
Ollama LLM Parser → Structured Output
↓
Job Template (Standardized Dataclass)
↓
SQLite DB (Storage & Deduplication)
↓
Streamlit Dashboard (UI & Analytics)


---

## Tech Stack

| Component        | Technology        |
|------------------|-------------------|
| Language         | Python 3.8+        |
| Scraping         | Selenium WebDriver |
| LLM Integration  | Ollama (Local LLMs)|
| Dashboard        | Streamlit          |
| Database         | SQLite             |
| Data Handling    | Pandas             |

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running ([https://ollama.ai](https://ollama.ai))
- Chrome browser and compatible Chromedriver

### Installation

```bash
git clone <your-repo-url>
cd job-aggregation-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```
### Configure Ollama
ollama serve
ollama pull mistral  # or another supported model

### Edit config.py:
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"
DATABASE_PATH = "jobs.db"
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"


## Run the Application
python master.py
python dashboard_server.py

Project Structure
job-aggregation-agent/
├── config.py
├── models.py
├── adapters.py
├── parser.py
├── database.py
├── dashboard_server.py
├── main.py
├── templates/
│   └── dashboard.html
└── requirements.txt


**Dashboard Features**

Search and filter by role, location, experience, and job type

View aggregated data in card or table view

Visual analytics on job types and source distribution

Real-time stats and refresh

Share jobs via WhatsApp with direct application links

**Extending the System**
You can easily add:

New sources (e.g., email, RSS, API-based)

New LLM models or parsing strategies

Output channels (e.g., email, WhatsApp, Telegram bots)
