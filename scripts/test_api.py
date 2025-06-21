"""
Test script to send a sample query to the API.
"""
import requests
from config.settings import settings

API_URL = f"http://{settings.API_HOST}:{settings.API_PORT}/query"

def main():
    payload = {
        "query": "How do I reset my password?",
        "customer_id": "test_001",
        "context": {}
    }
    response = requests.post(API_URL, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    main()
