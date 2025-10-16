# parser.py
"""
LLM job parser module for the Job Aggregation Agent.
Uses Ollama to parse unstructured text into structured job data.
For scalability: Parsing can be offloaded to a dedicated service (e.g., via gRPC) or batched
for high-throughput processing in a microservices architecture, with rate limiting to handle API quotas.
"""

import json
import requests
from typing import Optional, Dict

from config import OLLAMA_URL, OLLAMA_MODEL

class OllamaJobParser:
    """
    Parser class for job postings using Ollama LLM.
    Analyzes text to extract structured job information, validating against criteria.
    """
    
    def __init__(self, model_name: str = OLLAMA_MODEL, ollama_url: str = OLLAMA_URL):
        self.model_name = model_name
        self.ollama_url = ollama_url
    
    def parse_job_post(self, text: str, timestamp: str, source: str) -> Optional[Dict]:
        """
        Extract structured job info from text, return None if not a valid job posting.
        
        Args:
            text: The raw message text.
            timestamp: Posting timestamp.
            source: Source name.
        
        Returns:
            Parsed dictionary if valid, else None.
        """
        
        prompt = f"""You are a job posting analyzer. Analyze the following text and determine if it is a valid job posting.

RULES:
1. Text MUST contain a job title/role
2. Text MUST contain a company name
3. Text MUST contain at least one of: location, job type (remote/hybrid/on-site), experience level, salary
4. Ignore single-word messages, vague terms, or non-job content
5. Return ONLY valid JSON, no markdown or comments
6. If this is NOT a valid job posting, return exactly: {{"valid": false}}

If valid, return this JSON structure:
{{
    "valid": true,
    "role": "Job title",
    "company_name": "Company name",
    "location": "Location or 'Not specified'",
    "experience_required": "Years/Level or null",
    "job_type": "Remote/On-site/Hybrid or null",
    "application_link": "URL or contact email or null",
    "description": "Brief summary (2-3 sentences)"
}}

Text: {text}
Timestamp: {timestamp}

Respond ONLY with the JSON object, nothing else."""
        
        try:
            print(f"   Parsing with {self.model_name}...", end=" ", flush=True)
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 300,
                },
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"(HTTP {response.status_code})")
                return None
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            # Extract JSON
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx < 0 or end_idx <= start_idx:
                    print("(No JSON)")
                    return None
                
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Check if valid
                if not parsed.get('valid', False):
                    print("(Not a job posting)")
                    return None
                
                print("Success")
                return parsed
                
            except json.JSONDecodeError as e:
                print("(JSON error)")
                return None
        
        except requests.exceptions.Timeout:
            print("(Timeout)")
            return None
        except requests.exceptions.ConnectionError:
            print("(Ollama not running)")
            return None
        except Exception as e:
            print(f"(Error: {str(e)[:30]})")
            return None