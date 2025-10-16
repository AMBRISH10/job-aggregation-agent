# models.py
"""
Data models module for the Job Aggregation Agent.
Defines structured data classes for job postings to ensure consistency and type safety.
For scalability: These dataclasses can be extended to include additional fields (e.g., tags, categories)
or serialized to different formats (JSON, Protobuf) for microservices communication.
"""

from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class JobPost:
    """
    Standardized job post template.
    Represents a parsed job posting with essential fields for storage and display.
    """
    role: str
    company_name: str
    location: str
    experience_required: Optional[str]
    job_type: Optional[str]
    application_link: Optional[str]
    description: Optional[str]
    source: str
    date_posted: str  # ISO datetime when job was posted
    extracted_at: str  # When we extracted it
    post_id: str
    
    def to_dict(self):
        """Convert the dataclass to a dictionary for serialization."""
        return asdict(self)