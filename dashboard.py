"""
Streamlit Dashboard for Job Aggregation Agent
Real-time visualization and filtering of aggregated jobs
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="Job Aggregator Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .job-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .role-title {
        font-size: 18px;
        font-weight: bold;
        color: #1f77b4;
    }
    .company-name {
        font-size: 14px;
        color: #666;
    }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 5px;
    }
    .badge-remote {
        background-color: #d4edda;
        color: #155724;
    }
    .badge-onsite {
        background-color: #fff3cd;
        color: #856404;
    }
    .badge-hybrid {
        background-color: #d1ecf1;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================

@st.cache_resource
def get_db_connection():
    """Create database connection (cached)"""
    return sqlite3.connect("jobs.db")


def fetch_jobs(filters: Dict = None) -> List[Dict]:
    """Fetch jobs from database with optional filters"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if filters:
        if filters.get("job_type") and filters["job_type"] != "All":
            query += " AND job_type = ?"
            params.append(filters["job_type"])
        
        if filters.get("location") and filters["location"].strip():
            query += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        
        if filters.get("company_name") and filters["company_name"].strip():
            query += " AND company_name LIKE ?"
            params.append(f"%{filters['company_name']}%")
        
        if filters.get("source") and filters["source"] != "All":
            query += " AND source = ?"
            params.append(filters["source"])
        
        if filters.get("experience") and filters["experience"] != "All":
            query += " AND experience_required LIKE ?"
            params.append(f"%{filters['experience']}%")
    
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    jobs = [dict(row) for row in cursor.fetchall()]
    
    return jobs


def get_unique_values(column: str) -> List[str]:
    """Get unique values for a column"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT {column} FROM jobs WHERE {column} IS NOT NULL ORDER BY {column}")
    values = [row[0] for row in cursor.fetchall()]
    return values


def get_statistics() -> Dict:
    """Get dashboard statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total jobs
    cursor.execute("SELECT COUNT(*) FROM jobs")
    stats["total_jobs"] = cursor.fetchone()[0]
    
    # Jobs by type
    cursor.execute("SELECT job_type, COUNT(*) FROM jobs WHERE job_type IS NOT NULL GROUP BY job_type")
    stats["jobs_by_type"] = dict(cursor.fetchall())
    
    # Jobs by source
    cursor.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source")
    stats["jobs_by_source"] = dict(cursor.fetchall())
    
    # Jobs today
    cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE DATE(created_at) = DATE('now')
    """)
    stats["jobs_today"] = cursor.fetchone()[0]
    
    # Top companies
    cursor.execute("""
        SELECT company_name, COUNT(*) as count FROM jobs 
        GROUP BY company_name 
        ORDER BY count DESC 
        LIMIT 5
    """)
    stats["top_companies"] = dict(cursor.fetchall())
    
    return stats


# ============================================================================
# PAGE HEADER
# ============================================================================

st.markdown("# 💼 Job Aggregation Dashboard")
st.markdown("Automated job collection from multiple channels with intelligent parsing")

# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================

with st.sidebar:
    st.markdown("## 🔍 Filters & Controls")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    
    # Filter section
    st.markdown("### Filter Options")
    
    job_type_filter = st.selectbox(
        "Job Type",
        ["All"] + get_unique_values("job_type"),
        key="job_type_filter"
    )
    
    location_filter = st.text_input(
        "Location (Search)",
        placeholder="e.g., Bangalore, Remote",
        key="location_filter"
    )
    
    company_filter = st.text_input(
        "Company Name (Search)",
        placeholder="e.g., TechCorp",
        key="company_filter"
    )
    
    source_filter = st.selectbox(
        "Source Channel",
        ["All"] + get_unique_values("source"),
        key="source_filter"
    )
    
    experience_filter = st.selectbox(
        "Experience Level",
        ["All", "1-2 years", "2-3 years", "3-5 years", "5+ years"],
        key="experience_filter"
    )
    
    st.divider()
    
    # Manual run aggregation
    if st.button("▶️ Run Aggregation", use_container_width=True):
        st.info("Aggregation started... (Check console for details)")
        # In production, this would trigger: aggregator.aggregate()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Get statistics
stats = get_statistics()

# Statistics cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 Total Jobs",
        value=stats["total_jobs"]
    )

with col2:
    st.metric(
        label="🆕 Jobs Today",
        value=stats["jobs_today"]
    )

with col3:
    remote_count = stats["jobs_by_type"].get("Remote", 0)
    st.metric(
        label="🌍 Remote Jobs",
        value=remote_count
    )

with col4:
    sources_count = len(stats["jobs_by_source"])
    st.metric(
        label="📡 Active Sources",
        value=sources_count
    )

st.divider()

# Charts section
col1, col2 = st.columns(2)

with col1:
    if stats["jobs_by_type"]:
        st.subheader("Jobs by Type")
        df_type = pd.DataFrame(
            list(stats["jobs_by_type"].items()),
            columns=["Job Type", "Count"]
        )
        st.bar_chart(df_type.set_index("Job Type"))

with col2:
    if stats["jobs_by_source"]:
        st.subheader("Jobs by Source")
        df_source = pd.DataFrame(
            list(stats["jobs_by_source"].items()),
            columns=["Source", "Count"]
        )
        st.bar_chart(df_source.set_index("Source"))

st.divider()

# Top companies section
if stats["top_companies"]:
    st.subheader("🏢 Top Hiring Companies")
    df_companies = pd.DataFrame(
        list(stats["top_companies"].items()),
        columns=["Company", "Job Postings"]
    ).reset_index(drop=True)
    st.dataframe(df_companies, use_container_width=True)

st.divider()

# ============================================================================
# JOBS LIST WITH FILTERING
# ============================================================================

st.markdown("## 📋 Job Listings")

# Apply filters
filters = {
    "job_type": job_type_filter,
    "location": location_filter,
    "company_name": company_filter,
    "source": source_filter,
    "experience": experience_filter
}

jobs = fetch_jobs(filters)

# Display job count
st.markdown(f"**Showing {len(jobs)} job(s)**")

if not jobs:
    st.warning("No jobs found matching your filters.")
else:
    # Toggle between card and table view
    view_type = st.radio(
        "View Type",
        ["Cards", "Table"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_type == "Cards":
        for job in jobs:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {job['role']}")
                    st.markdown(f"**{job['company_name']}**")
                    
                    # Badges
                    badge_html = ""
                    if job['job_type']:
                        badge_class = f"badge-{job['job_type'].lower().replace('-', '')}"
                        badge_html += f"<span class='badge {badge_class}'>{job['job_type']}</span>"
                    
                    if job['location']:
                        badge_html += f"<span class='badge' style='background-color: #e7f3ff; color: #004085;'>{job['location']}</span>"
                    
                    if job['experience_required']:
                        badge_html += f"<span class='badge' style='background-color: #f8f9fa; color: #333;'>{job['experience_required']}</span>"
                    
                    st.markdown(badge_html, unsafe_allow_html=True)
                    
                    if job['description']:
                        st.markdown(f"*{job['description'][:200]}...*" if len(job['description']) > 200 else f"*{job['description']}*")
                    
                    col_apply, col_source = st.columns([2, 1])
                    with col_apply:
                        if job['application_link']:
                            st.markdown(f"[📝 Apply]({job['application_link']})")
                    with col_source:
                        st.caption(f"Source: {job['source']}")
                
                with col2:
                    st.caption(f"Added: {job['created_at'][:10]}")
            
            st.divider()
    
    else:  # Table view
        df = pd.DataFrame(jobs)
        df = df[['role', 'company_name', 'location', 'job_type', 'experience_required', 'source', 'created_at']]
        df.columns = ['Role', 'Company', 'Location', 'Type', 'Experience', 'Source', 'Added Date']
        st.dataframe(df, use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Job Aggregation Agent | Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)