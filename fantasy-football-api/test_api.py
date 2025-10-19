#!/usr/bin/env python3
"""
Run this after starting the API with: uv run uvicorn api:app --host 0.0.0.0 --port 8000
"""
"""
Simple test script to verify API functionality
"""
import requests
import time
import sys

API_BASE = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint working")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_league_data_endpoint():
    """Test the league data endpoint"""
    try:
        response = requests.get(f"{API_BASE}/league/data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ League data endpoint working")
            print(f"   League: {data.get('league_name', 'Unknown')}")
            print(f"   Week: {data.get('week', 'Unknown')}")
            print(f"   Teams: {len(data.get('teams', []))}")
            return True
        else:
            print(f"❌ League data endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ League data endpoint failed: {e}")
        return False

def main():
    print("Testing Fantasy Football Matrix API...")
    print(f"API Base URL: {API_BASE}")
    print("-" * 50)
    
    # Test basic endpoints
    health_ok = test_health_endpoint()
    root_ok = test_root_endpoint()
    
    # Test league data (this will fail without proper .env setup)
    print("\nTesting league data endpoint...")
    print("(This will fail without proper ESPN league configuration)")
    league_ok = test_league_data_endpoint()
    
    print("-" * 50)
    if health_ok and root_ok:
        print("✅ Basic API functionality working!")
        if league_ok:
            print("✅ League data working - API fully functional!")
        else:
            print("⚠️  League data failed - check your .env configuration")
    else:
        print("❌ Basic API endpoints failing")
        sys.exit(1)

if __name__ == "__main__":
    main()