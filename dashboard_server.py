# dashboard_server.py
"""
Job Aggregator Dashboard Server
Modern Flask-based web interface for job aggregation system
"""

from flask import Flask, render_template, jsonify, request
from typing import Dict, List
import json

from database import get_statistics, get_chart_data, get_filtered_jobs, get_filter_options

app = Flask(__name__)

DATABASE_PATH = "newjobdb.db"  # Kept for compatibility, but functions use it internally

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """
    Render the main dashboard template.
    """
    return render_template('dashboard.html')

@app.route('/api/statistics')
def api_statistics():
    """
    API endpoint to get dashboard statistics.
    """
    return jsonify(get_statistics())

@app.route('/api/charts')
def api_charts():
    """
    API endpoint to get data for charts.
    """
    return jsonify(get_chart_data())

@app.route('/api/jobs')
def api_jobs():
    """
    API endpoint to get filtered and paginated jobs.
    """
    filters = {
        'search': request.args.get('search', ''),
        'date_range': request.args.get('date_range', 'all'),
        'job_type': request.args.get('job_type', 'all'),
        'location': request.args.get('location', ''),
        'company': request.args.get('company', ''),
        'source': request.args.get('source', 'all'),
        'experience': request.args.get('experience', 'all'),
        'page': request.args.get('page', 1),
        'per_page': request.args.get('per_page', 20)
    }
    return jsonify(get_filtered_jobs(filters))

@app.route('/api/filter-options')
def api_filter_options():
    """
    API endpoint to get available filter options.
    """
    return jsonify(get_filter_options())

if __name__ == '__main__':
    print("\nStarting Job Aggregator Dashboard...")
    print("Dashboard URL: http://localhost:5000")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)