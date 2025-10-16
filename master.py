# master.py
"""
Scalable Intelligent Job Aggregation Agent (v2)
Improved pipeline: HTML scraping → BeautifulSoup extraction → LLM parsing

This is the main entry point and orchestrator for the job aggregation system.
It coordinates sources, parsing, and database operations without altering existing functionality.
For scalability: The JobAggregator class uses dependency injection for sources and parsers,
enabling easy extension to multiple workers (e.g., via Celery) or distributed execution across nodes.
"""

import hashlib
import json
import requests
import time
from typing import List, Optional

from config import CHANNELS, OLLAMA_URL, OLLAMA_MODEL, DATABASE_PATH, CHROME_DRIVER_PATH, CHROME_PROFILE_DIR
from models import JobPost
from adapters import WhatsAppChannelAdapter, SourceAdapter
from parser import OllamaJobParser
from database import JobDatabase

class JobAggregator:
    """
    Main orchestrator class for the job aggregation pipeline.
    Manages sources, parsing, and persistence in a modular way.
    """
    
    def __init__(self, db_path: str, ollama_url: str = OLLAMA_URL):
        """
        Initialize the aggregator with database and parser.
        
        Args:
            db_path: Path to the database file.
            ollama_url: URL for the Ollama service.
        """
        self.db = JobDatabase(db_path)
        self.parser = OllamaJobParser(model_name=OLLAMA_MODEL, ollama_url=ollama_url)
        self.sources: List[SourceAdapter] = []
    
    def add_source(self, source: SourceAdapter):
        """Register a data source adapter."""
        self.sources.append(source)
    
    def process_post(self, text: str, timestamp: str, source_name: str) -> Optional[JobPost]:
        """
        Convert a raw message to a structured JobPost using the LLM parser.
        
        Args:
            text: Raw message text.
            timestamp: Message timestamp.
            source_name: Name of the source.
        
        Returns:
            JobPost if valid, else None.
        """
        
        parsed_data = self.parser.parse_job_post(text, timestamp, source_name)
        
        if not parsed_data or not parsed_data.get('valid'):
            return None
        
        # Generate unique post_id using hash for deduplication
        post_hash = hashlib.md5(
            f"{parsed_data.get('company_name')}{parsed_data.get('role')}{timestamp}".encode()
        ).hexdigest()
        
        job = JobPost(
            role=str(parsed_data.get("role", "Unknown")).strip(),
            company_name=str(parsed_data.get("company_name", "Unknown")).strip(),
            location=str(parsed_data.get("location", "Not specified")).strip(),
            experience_required=parsed_data.get("experience_required"),
            job_type=parsed_data.get("job_type"),
            application_link=parsed_data.get("application_link"),
            description=parsed_data.get("description"),
            source=source_name,
            date_posted=timestamp,
            extracted_at=time.strftime('%Y-%m-%dT%H:%M:%S'),  # Use current time in ISO format
            post_id=post_hash
        )
        
        return job
    
    def aggregate(self):
        """
        Execute the main aggregation pipeline across all sources.
        Processes messages, parses jobs, and inserts into database.
        
        Returns:
            Count of new jobs added.
        """
        print("\n" + "="*70)
        print("STARTING JOB AGGREGATION")
        print("="*70)
        
        new_jobs_count = 0
        total_messages_processed = 0
        total_valid_jobs = 0
        
        for source in self.sources:
            print(f"\n{'─'*70}")
            print(f"Processing source: {source.source_name}")
            print(f"{'─'*70}")
            
            messages = source.fetch_posts()
            print(f"\nFound {len(messages)} messages to process\n")
            
            for idx, msg in enumerate(messages, 1):
                total_messages_processed += 1
                text = msg.get('text', '')
                timestamp = msg.get('timestamp', '')
                
                print(f"[{idx}/{len(messages)}] Processing: {text[:60]}...")
                
                job = self.process_post(text, timestamp, source.source_name)
                
                if job:
                    total_valid_jobs += 1
                    if self.db.insert_job(job):
                        new_jobs_count += 1
                        print(f"    Added: {job.role} at {job.company_name}")
                        print(f"       Location: {job.location} | Posted: {timestamp[:10]}")
                    else:
                        print(f"    Duplicate entry")
        
        # Summary
        print(f"\n{'='*70}")
        print("AGGREGATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total messages processed: {total_messages_processed}")
        print(f"Valid job postings found: {total_valid_jobs}")
        print(f"New jobs added: {new_jobs_count}")
        print(f"Total jobs in database: {self.db.get_job_count()}")
        print(f"{'='*70}\n")
        
        return new_jobs_count

def initialize_aggregator() -> JobAggregator:
    """
    Set up the aggregator instance with configured sources.
    
    Returns:
        Initialized JobAggregator.
    """
    aggregator = JobAggregator(DATABASE_PATH)
    
    for channel in CHANNELS["WhatsApp"]:
        if channel["enabled"]:
            adapter = WhatsAppChannelAdapter(
                channel_url=channel["url"],
                source_name=channel["name"],
                chrome_driver_path=CHROME_DRIVER_PATH,
                user_data_dir=CHROME_PROFILE_DIR
            )
            aggregator.add_source(adapter)
    
    return aggregator

if __name__ == "__main__":
    print(f"\nChecking Ollama connection ({OLLAMA_MODEL})...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("Ollama server is running!")
        else:
            print(f"Ollama returned status {response.status_code}")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to Ollama. Start it with: ollama serve")
        exit(1)
    
    aggregator = initialize_aggregator()
    aggregator.aggregate()