# #!/usr/bin/env python3
# """
# Troubleshooting and Verification Script
# Tests all components before running real extraction
# """

# import sys
# import os
# import subprocess
# from pathlib import Path
# import requests
# import json

# # Colors for output
# GREEN = '\033[92m'
# RED = '\033[91m'
# YELLOW = '\033[93m'
# BLUE = '\033[94m'
# RESET = '\033[0m'
# BOLD = '\033[1m'

# # Your configuration
# CHROME_DRIVER_PATH = "/home/ambrish/Desktop/job-aggregation-agent/chromedriver-linux64/chromedriver"
# OLLAMA_URL = "http://localhost:11434"
# OLLAMA_MODEL = "gpt-oss"

# def print_header(title):
#     """Print formatted header"""
#     print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
#     print(f"{BOLD}{BLUE}{title.center(70)}{RESET}")
#     print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

# def print_check(item, passed, message=""):
#     """Print check result"""
#     symbol = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
#     print(f"{symbol} {item}")
#     if message:
#         print(f"   {message}")

# def check_python_version():
#     """Check Python version is 3.8+"""
#     print_header("1. Python Version")
    
#     version = sys.version_info
#     version_str = f"{version.major}.{version.minor}.{version.micro}"
    
#     passed = version.major >= 3 and version.minor >= 8
#     print_check(f"Python {version_str}", passed)
    
#     return passed

# def check_chrome_driver():
#     """Check Chrome driver exists and is executable"""
#     print_header("2. Chrome WebDriver")
    
#     print(f"Looking for: {CHROME_DRIVER_PATH}")
    
#     # Check exists
#     path = Path(CHROME_DRIVER_PATH)
#     exists = path.exists()
#     print_check("File exists", exists, CHROME_DRIVER_PATH if exists else f"NOT FOUND: {CHROME_DRIVER_PATH}")
    
#     if not exists:
#         return False
    
#     # Check executable
#     is_executable = os.access(CHROME_DRIVER_PATH, os.X_OK)
#     print_check("Is executable", is_executable)
    
#     if not is_executable:
#         print(f"   {YELLOW}Fix: chmod +x {CHROME_DRIVER_PATH}{RESET}")
#         return False
    
#     # Test version
#     try:
#         result = subprocess.run(
#             [CHROME_DRIVER_PATH, "--version"],
#             capture_output=True,
#             text=True,
#             timeout=5
#         )
#         version_output = result.stdout.strip()
#         print_check("Version check", result.returncode == 0, version_output)
#         return result.returncode == 0
#     except Exception as e:
#         print_check("Version check", False, str(e))
#         return False

# def check_selenium():
#     """Check Selenium package"""
#     print_header("3. Selenium Package")
    
#     try:
#         import selenium
#         version = selenium.__version__
#         print_check("Selenium installed", True, f"Version {version}")
        
#         # Test import
#         from selenium import webdriver
#         from selenium.webdriver.common.by import By
#         print_check("Selenium imports", True)
        
#         return True
#     except ImportError as e:
#         print_check("Selenium installed", False, "Install with: pip install selenium")
#         return False

# def check_ollama_server():
#     """Check Ollama server is running"""
#     print_header("4. Ollama Server")
    
#     print(f"Checking: {OLLAMA_URL}")
    
#     try:
#         response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        
#         server_running = response.status_code == 200
#         print_check("Server running", server_running)
        
#         if not server_running:
#             print(f"   {YELLOW}Fix: ollama serve{RESET}")
#             return False
        
#         return True
        
#     except requests.exceptions.ConnectionError:
#         print_check("Server running", False, f"Cannot connect to {OLLAMA_URL}")
#         print(f"   {YELLOW}Fix: Run 'ollama serve' in a terminal{RESET}")
#         return False
#     except requests.exceptions.Timeout:
#         print_check("Server running", False, "Connection timeout")
#         return False

# def check_ollama_model():
#     """Check if gpt-oss model is available"""
#     print_header("5. Ollama Model")
    
#     print(f"Looking for model: {OLLAMA_MODEL}")
    
#     try:
#         response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        
#         if response.status_code != 200:
#             print_check("Model check", False, f"Ollama server error")
#             return False
        
#         models = response.json().get("models", [])
#         model_names = [m.get("name", "") for m in models]
        
#         # Check if our model is available
#         model_found = any(OLLAMA_MODEL in name for name in model_names)
        
#         print(f"Available models: {', '.join(model_names) if model_names else 'None'}")
#         print_check(f"Model '{OLLAMA_MODEL}' available", model_found)
        
#         if not model_found:
#             print(f"   {YELLOW}Fix: ollama pull {OLLAMA_MODEL}{RESET}")
        
#         return model_found
        
#     except Exception as e:
#         print_check("Model check", False, str(e))
#         return False

# def check_ollama_inference():
#     """Test Ollama can parse JSON"""
#     print_header("6. Ollama Inference")
    
#     test_prompt = 'Return only this JSON: {"test": "value"}'
    
#     try:
#         print("Testing inference with sample prompt...")
        
#         response = requests.post(
#             f"{OLLAMA_URL}/api/generate",
#             json={
#                 "model": OLLAMA_MODEL,
#                 "prompt": test_prompt,
#                 "stream": False,
#                 "temperature": 0.1,
#                 "num_predict": 50,
#             },
#             timeout=60
#         )
        
#         if response.status_code != 200:
#             print_check("Inference test", False, f"HTTP {response.status_code}")
#             return False
        
#         result = response.json()
#         response_text = result.get("response", "")
        
#         # Check if response contains JSON
#         has_json = "{" in response_text and "}" in response_text
        
#         print(f"Response: {response_text[:100]}...")
#         print_check("Inference working", True)
#         print_check("Returns JSON", has_json)
        
#         return True
        
#     except requests.exceptions.Timeout:
#         print_check("Inference test", False, "Timeout (model may be slow on CPU)")
#         return False
#     except Exception as e:
#         print_check("Inference test", False, str(e))
#         return False

# def check_database():
#     """Check database can be created"""
#     print_header("7. SQLite Database")
    
#     try:
#         import sqlite3
#         print_check("SQLite3 available", True)
        
#         # Try to create test database
#         test_db = Path("test_check.db")
#         conn = sqlite3.connect(str(test_db))
#         cursor = conn.cursor()
#         cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
#         conn.commit()
#         conn.close()
        
#         print_check("Database creation", True, "jobs.db")
        
#         # Cleanup
#         test_db.unlink()
        
#         return True
        
#     except Exception as e:
#         print_check("Database creation", False, str(e))
#         return False

# def check_streamlit():
#     """Check Streamlit is installed"""
#     print_header("8. Streamlit")
    
#     try:
#         import streamlit
#         version = streamlit.__version__
#         print_check("Streamlit installed", True, f"Version {version}")
#         return True
#     except ImportError:
#         print_check("Streamlit installed", False, "Install with: pip install streamlit")
#         return False

# def check_dependencies():
#     """Check all required packages"""
#     print_header("9. Python Dependencies")
    
#     required = {
#         "requests": "HTTP client",
#         "selenium": "Browser automation",
#         "pandas": "Data processing",
#         "streamlit": "Dashboard",
#     }
    
#     all_ok = True
#     for package, description in required.items():
#         try:
#             __import__(package)
#             print_check(package, True, description)
#         except ImportError:
#             print_check(package, False, f"Install with: pip install {package}")
#             all_ok = False
    
#     return all_ok

# def run_quick_test():
#     """Run quick functional test"""
#     print_header("10. Quick Functional Test")
    
#     try:
#         # Test 1: Import all modules
#         print("Importing main modules...")
#         from main import JobAggregator, WhatsAppChannelAdapter, OllamaJobParser
#         print_check("Module imports", True)
        
#         # Test 2: Create parser
#         print("Creating Ollama parser...")
#         parser = OllamaJobParser(OLLAMA_MODEL, OLLAMA_URL)
#         print_check("Parser creation", True)
        
#         # Test 3: Simple parse
#         print("Testing LLM parsing...")
#         test_text = "Python Developer at TechCorp, Bangalore, 2-3 years, Remote"
#         result = parser.parse_job_post(test_text, "Test")
        
#         if result and isinstance(result, dict):
#             print_check("LLM parsing", True, f"Got: {result.get('role', 'Unknown')}")
#             return True
#         else:
#             print_check("LLM parsing", False, "Invalid response")
#             return False
            
#     except Exception as e:
#         print_check("Functional test", False, str(e))
#         return False

# def print_summary(results):
#     """Print summary of all checks"""
#     print_header("SUMMARY")
    
#     passed = sum(results.values())
#     total = len(results)
    
#     print(f"Passed: {passed}/{total}\n")
    
#     for check_name, result in results.items():
#         symbol = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
#         print(f"{symbol} {check_name}")
    
#     if passed == total:
#         print(f"\n{GREEN}{BOLD}✅ ALL CHECKS PASSED!{RESET}")
#         print(f"\n{BOLD}Next steps:{RESET}")
#         print(f"1. Run: {BOLD}python main.py{RESET}")
#         print(f"2. Monitor browser for WhatsApp loading")
#         print(f"3. View results: {BOLD}streamlit run dashboard.py{RESET}")
#         return True
#     else:
#         print(f"\n{RED}{BOLD}❌ SOME CHECKS FAILED{RESET}")
#         print(f"\nFix the issues above before running extraction.")
#         return False

# def main():
#     """Run all checks"""
#     print(f"\n{BOLD}{BLUE}")
#     print("╔" + "="*68 + "╗")
#     print("║" + " REAL JOB EXTRACTION - VERIFICATION SCRIPT ".center(68) + "║")
#     print("╚" + "="*68 + "╝")
#     print(f"{RESET}\n")
    
#     results = {}
    
#     # Run all checks
#     results["Python Version"] = check_python_version()
#     results["Chrome Driver"] = check_chrome_driver()
#     results["Selenium Package"] = check_selenium()
#     results["Ollama Server"] = check_ollama_server()
#     results["Ollama Model"] = check_ollama_model()
#     results["Ollama Inference"] = check_ollama_inference()
#     results["SQLite Database"] = check_database()
#     results["Streamlit"] = check_streamlit()
#     results["Dependencies"] = check_dependencies()
#     results["Functional Test"] = run_quick_test()
    
#     # Print summary
#     success = print_summary(results)
    
#     return 0 if success else 1

# if __name__ == "__main__":
#     sys.exit(main())

import fitz  # PyMuPDF

def count_substances_in_pdf(pdf_path):
    # Open the PDF
    doc = fitz.open(pdf_path)
    
    substances = set()  # Using a set to avoid duplicates
    
    # Iterate through each page
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # Get the page
        text = page.get_text("text")   # Extract text in plain format
        lines = text.splitlines()      # Split text into lines
        
        for line in lines:
            # Split each line by commas and strip extra spaces
            entries = [entry.strip() for entry in line.split(",")]
            substances.update(entries)  # Add to set of substances
    
    return len(substances)  # Return the count of distinct substances

# Example usage
pdf_path = "/home/ambrish/Downloads/appendix_a_22.pdf"  # Replace with your PDF file path

count = count_substances_in_pdf(pdf_path)
print(f"Total number of distinct substances: {count}")# print(substances)
