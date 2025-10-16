# database.py
"""
Database module for the Job Aggregation Agent.
Provides SQLite-based storage for jobs and duplicates, with query helpers for dashboard.
For scalability: While SQLite is suitable for single-node setups, this layer can be abstracted
to support migration to PostgreSQL/MySQL for sharding/replication in high-traffic scenarios.
Common operations are parameterized to prevent SQL injection and support connection pooling.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config import DATABASE_PATH
from models import JobPost

class JobDatabase:
    """
    SQLite database class for job storage and querying.
    Manages schema, insertions, and retrievals with optional filtering.
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database schema if it does not exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newjobdb (
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
                date_posted TEXT NOT NULL,
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
        """
        Insert a job post into the database.
        
        Args:
            job: JobPost instance.
        
        Returns:
            True if inserted (new), False if duplicate.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO newjobdb 
                (post_id, role, company_name, location, experience_required, 
                 job_type, application_link, description, source, date_posted, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.post_id, job.role, job.company_name, job.location,
                job.experience_required, job.job_type, job.application_link,
                job.description, job.source, job.date_posted, job.extracted_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_jobs(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve jobs with optional filters applied.
        
        Args:
            filters: Optional dictionary of filters (e.g., {'job_type': 'Remote'}).
        
        Returns:
            List of job dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM newjobdb WHERE 1=1"
        params = []
        
        if filters:
            if filters.get("job_type"):
                query += " AND job_type = ?"
                params.append(filters["job_type"])
            if filters.get("location"):
                query += " AND location LIKE ?"
                params.append(f"%{filters['location']}%")
            if filters.get("date_range") == "last_7_days":
                seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
                query += " AND date_posted >= ?"
                params.append(seven_days_ago)
        
        query += " ORDER BY date_posted DESC"
        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def get_job_count(self) -> int:
        """Get the total count of jobs in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM newjobdb")
        count = cursor.fetchone()[0]
        conn.close()
        return count

# Dashboard-specific database helpers
# These functions provide aggregated data for the web dashboard.
# For scalability: These can be cached (e.g., Redis) or computed asynchronously to handle concurrent requests.

def get_db_connection():
    """
    Create a database connection with row factory enabled.
    
    Returns:
        SQLite connection object.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_statistics() -> Dict:
    """
    Retrieve key dashboard statistics (total jobs, remote, etc.).
    
    Returns:
        Dictionary of statistics.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total jobs
    cursor.execute("SELECT COUNT(*) as total FROM newjobdb")
    total_jobs = cursor.fetchone()['total']
    
    # Remote jobs
    cursor.execute("SELECT COUNT(*) as remote FROM newjobdb WHERE job_type LIKE '%remote%'")
    remote_jobs = cursor.fetchone()['remote']
    
    # Jobs posted today
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT COUNT(*) as today FROM newjobdb WHERE date(date_posted) = ?", (today,))
    jobs_today = cursor.fetchone()['today']
    
    # Jobs in last 7 days
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(*) as last_week FROM newjobdb WHERE date_posted >= ?", (seven_days_ago,))
    jobs_last_week = cursor.fetchone()['last_week']
    
    # Top companies count
    cursor.execute("SELECT COUNT(DISTINCT company_name) as companies FROM newjobdb")
    top_companies = cursor.fetchone()['companies']
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'remote_jobs': remote_jobs,
        'jobs_today': jobs_today,
        'jobs_last_week': jobs_last_week,
        'top_companies': top_companies
    }

def get_chart_data() -> Dict:
    """
    Retrieve data for dashboard charts (job types, sources).
    
    Returns:
        Dictionary with chart datasets.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Job type distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN job_type LIKE '%remote%' THEN 'Remote'
                WHEN job_type LIKE '%hybrid%' THEN 'Hybrid'
                WHEN job_type LIKE '%on-site%' OR job_type LIKE '%onsite%' THEN 'On-site'
                ELSE 'Not Specified'
            END as type,
            COUNT(*) as count
        FROM newjobdb
        GROUP BY type
    """)
    job_types = cursor.fetchall()
    
    # Jobs by source
    cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM newjobdb
        GROUP BY source
        ORDER BY count DESC
        LIMIT 5
    """)
    sources = cursor.fetchall()
    
    conn.close()
    
    return {
        'job_types': [{'label': row['type'], 'value': row['count']} for row in job_types],
        'sources': [{'label': row['source'], 'value': row['count']} for row in sources]
    }

def get_filtered_jobs(filters: Dict) -> Dict:
    """
    Retrieve filtered and paginated jobs for the dashboard.
    
    Args:
        filters: Dictionary of filter parameters.
    
    Returns:
        Dictionary with jobs list, pagination info.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM newjobdb WHERE 1=1"
    params = []
    
    # Search filter
    if filters.get('search'):
        query += " AND (role LIKE ? OR company_name LIKE ? OR description LIKE ?)"
        search_term = f"%{filters['search']}%"
        params.extend([search_term, search_term, search_term])
    
    # Date range filter
    if filters.get('date_range'):
        if filters['date_range'] == 'today':
            today = datetime.now().date().isoformat()
            query += " AND date(date_posted) = ?"
            params.append(today)
        elif filters['date_range'] == '3days':
            three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
            query += " AND date_posted >= ?"
            params.append(three_days_ago)
        elif filters['date_range'] == '7days':
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            query += " AND date_posted >= ?"
            params.append(seven_days_ago)
    
    # Job type filter
    if filters.get('job_type') and filters['job_type'] != 'all':
        query += " AND job_type LIKE ?"
        params.append(f"%{filters['job_type']}%")
    
    # Location filter
    if filters.get('location'):
        query += " AND location LIKE ?"
        params.append(f"%{filters['location']}%")
    
    # Company filter
    if filters.get('company'):
        query += " AND company_name LIKE ?"
        params.append(f"%{filters['company']}%")
    
    # Source filter
    if filters.get('source') and filters['source'] != 'all':
        query += " AND source = ?"
        params.append(filters['source'])
    
    # Experience filter
    if filters.get('experience') and filters['experience'] != 'all':
        query += " AND experience_required LIKE ?"
        params.append(f"%{filters['experience']}%")
    
    query += " ORDER BY date_posted DESC"
    
    # Get total count before pagination
    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as total')
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Pagination
    page = int(filters.get('page', 1))
    per_page = int(filters.get('per_page', 20))
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"
    
    cursor.execute(query, params)
    jobs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'jobs': jobs,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }

def get_filter_options() -> Dict:
    """
    Retrieve available options for dashboard filters (sources, locations, companies).
    
    Returns:
        Dictionary of filter option lists.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get unique sources
    cursor.execute("SELECT DISTINCT source FROM newjobdb ORDER BY source")
    sources = [row['source'] for row in cursor.fetchall()]
    
    # Get unique locations
    cursor.execute("SELECT DISTINCT location FROM newjobdb WHERE location IS NOT NULL ORDER BY location LIMIT 20")
    locations = [row['location'] for row in cursor.fetchall()]
    
    # Get unique companies
    cursor.execute("SELECT DISTINCT company_name FROM newjobdb ORDER BY company_name LIMIT 50")
    companies = [row['company_name'] for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'sources': sources,
        'locations': locations,
        'companies': companies
    }