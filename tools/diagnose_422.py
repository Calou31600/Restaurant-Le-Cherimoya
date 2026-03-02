import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def diagnose_422():
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = "Settings_Cherimoya"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # 1. Get current record
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    response = requests.get(url, headers=headers)
    records = response.json().get('records', [])
    if not records:
        print("No records found.")
        return
    
    record_id = records[0]['id']
    print(f"Diagnosing record: {record_id}")
    
    # 2. Try to update with EXACTLY what the app sends
    # simulate the frontend data
    data = {
        "totalSeats": 50,
        "maxReservationsPerDay": 100,
        "lunchStartTime": "12:00",
        "lunchEndTime": "14:00",
        "dinnerStartTime": "19:00",
        "dinnerEndTime": "22:00",
        "closedDays": ["1", "2"],
        "minAdvanceBookingHours": 2,
        "maxAdvanceBookingDays": 90
    }
    
    # Apply the same logic as settings_manager.py
    fields = {
        "totalSeats": data.get('totalSeats'),
        "maxReservationsPerDay": data.get('maxReservationsPerDay'),
        "lunchStartTime": data.get('lunchStartTime'),
        "lunchEndTime": data.get('lunchEndTime'),
        "dinnerStartTime": data.get('dinnerStartTime'),
        "dinnerEndTime": data.get('dinnerEndTime'),
        "closedDays": [str(day) for day in data.get('closedDays', [])],
        "minAdvanceBookingHours": data.get('minAdvanceBookingHours'),
        "maxAdvanceBookingDays": data.get('maxAdvanceBookingDays')
    }
    
    update_url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
    payload = {"fields": fields}
    
    print("\nSending Payload:")
    print(json.dumps(payload, indent=2))
    
    res = requests.patch(update_url, json=payload, headers=headers)
    print(f"\nResponse Code: {res.status_code}")
    print("Response Body:")
    print(res.text)

if __name__ == "__main__":
    diagnose_422()
