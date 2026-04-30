import os
from dotenv import load_dotenv
load_dotenv()

from services.groq_client import call_groq

# 5 test inputs — run all of them
test_cases = [
    {
        "role_name": "Admin",
        "permissions": "read, write, delete, manage_users",
        "department": "IT"
    },
    {
        "role_name": "HR Manager",
        "permissions": "read_employee_records, edit_salaries",
        "department": "Human Resources"
    },
    {
        "role_name": "Read Only Auditor",
        "permissions": "read",
        "department": "Finance"
    },
    {
        "role_name": "DevOps Engineer",
        "permissions": "deploy, read, write, restart_services, access_logs",
        "department": "Engineering"
    },
    {
        "role_name": "Customer Support",
        "permissions": "read_tickets, update_tickets, view_customer_info",
        "department": "Support"
    }
]

with open("prompts/describe.txt", "r") as f:
    template = f.read()

for i, tc in enumerate(test_cases, 1):
    print(f"\n{'='*50}")
    print(f"Test {i}: {tc['role_name']}")
    print(f"{'='*50}")
    prompt = template.format(**tc)
    messages = [{"role": "user", "content": prompt}]
    result = call_groq(messages, temperature=0.3)
    print(result)