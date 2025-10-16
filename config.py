# config.py
"""
Configuration module for the Job Aggregation Agent.
Centralizes all configuration constants, paths, and settings to improve maintainability.
This allows easy modification of parameters without altering core logic.
For scalability: Configurations can be externalized to environment variables, YAML files,
or a configuration management system (e.g., Consul, etcd) in distributed environments.
"""

import os

# Chrome and Selenium configuration
CHROME_DRIVER_PATH = "/home/ambrish/Desktop/job-aggregation-agent/chromedriver-linux64/chromedriver"
CHROME_PROFILE_DIR = "/home/ambrish/selenium-profile"

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss")

# Database and file paths
DATABASE_PATH = "newjobdb.db"
DEBUG_DIR = "debug_html"

# WhatsApp channels to monitor
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