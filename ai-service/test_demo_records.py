import requests
import json

BASE_URL = "http://127.0.0.1:5000"

demo_records = [
    {"role_name": "System Admin",      "permissions": "read, write, delete, manage_users", "department": "IT",          "risk_level": "high"},
    {"role_name": "HR Manager",        "permissions": "read, write, manage_employees",     "department": "HR",          "risk_level": "high"},
    {"role_name": "Finance Analyst",   "permissions": "read, export_reports",              "department": "Finance",     "risk_level": "medium"},
    {"role_name": "DevOps Engineer",   "permissions": "deploy, restart_services, read",    "department": "Engineering", "risk_level": "high"},
    {"role_name": "Read Only Auditor", "permissions": "read",                              "department": "Finance",     "risk_level": "low"},
    {"role_name": "Support Agent",     "permissions": "read, update_tickets",              "department": "Support",     "risk_level": "low"},
    {"role_name": "Marketing Editor",  "permissions": "read, write, publish",              "department": "Marketing",   "risk_level": "medium"},
    {"role_name": "Database Admin",    "permissions": "read, write, delete, backup",       "department": "IT",          "risk_level": "high"},
    {"role_name": "Sales Manager",     "permissions": "read, write, export",               "department": "Sales",       "risk_level": "medium"},
    {"role_name": "Security Analyst",  "permissions": "read, audit, monitor",              "department": "Security",    "risk_level": "medium"},
]

print("=" * 60)
print("Testing all endpoints against demo records")
print("=" * 60)

passed = 0
failed = 0

for i, record in enumerate(demo_records, 1):
    print(f"\nRecord {i}: {record['role_name']}")

    # Test /describe
    try:
        r = requests.post(f"{BASE_URL}/describe", json=record)
        data = r.json()
        if r.status_code == 200 and not data.get("is_fallback"):
            print(f"  /describe    PASS  risk_level: {data.get('risk_level')}")
            passed += 1
        else:
            print(f"  /describe    FAIL  is_fallback: {data.get('is_fallback')}")
            failed += 1
    except Exception as e:
        print(f"  /describe    FAIL  Error: {e}")
        failed += 1

    # Test /recommend
    try:
        r = requests.post(f"{BASE_URL}/recommend", json=record)
        data = r.json()
        recs = data.get("recommendations", [])
        if r.status_code == 200 and len(recs) == 3:
            print(f"  /recommend   PASS  {len(recs)} recommendations")
            passed += 1
        else:
            print(f"  /recommend   FAIL  got {len(recs)} recommendations")
            failed += 1
    except Exception as e:
        print(f"  /recommend   FAIL  Error: {e}")
        failed += 1

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print(f"Total:   {passed + failed} tests")
print("=" * 60)