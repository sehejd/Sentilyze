#!/usr/bin/env python3
"""
Test script for Sentilyze API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, ticker="AAPL"):
    """Test a specific API endpoint"""
    url = f"{BASE_URL}{endpoint}?ticker={ticker}"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            if endpoint == "/api/analyze":
                # Show comprehensive analysis summary
                if 'analysis' in data and 'summary' in data['analysis']:
                    print("AI Analysis Summary:")
                    print(data['analysis']['summary'][:200] + "...")
            else:
                print(f"Data keys: {list(data.keys())}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print("-" * 50)

def main():
    print("🧪 Testing Sentilyze API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    test_endpoint("/health")
    
    # Test individual scrapers
    test_endpoint("/api/yahoo")
    test_endpoint("/api/reddit")
    test_endpoint("/api/twitter")
    
    # Test comprehensive analysis
    print("🧠 Testing AI-powered comprehensive analysis...")
    test_endpoint("/api/analyze")
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
