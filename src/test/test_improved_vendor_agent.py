#!/usr/bin/env python3
from src.agents.vendor_query_agent import VendorQueryAgent

print("=" * 80)
print("IMPROVED VENDOR QUERY AGENT - FULL RESPONSE TEST")
print("=" * 80)

agent = VendorQueryAgent()

# Test with vendor email
print("\n📧 Test 1: Query with vendor email")
print("-" * 80)
response = agent.process_vendor_query(
    'What invoices do I have pending?', 
    'payments@techsupply.com'
)

print(f"Query: {response['query']}")
print(f"Vendor Email: {response['vendor_email']}")
print(f"Vendor ID: {response['vendor_id']}")
print(f"Success: {response['success']}")
print("\n📋 AI Response:")
print("-" * 80)
print(response['response'])
print("-" * 80)

# Test 2
print("\n\n📧 Test 2: Different vendor")
print("-" * 80)
response2 = agent.process_vendor_query(
    'When should I expect payment for my recent deliveries?', 
    'finance@officesolutions.com'
)

print(f"Query: {response2['query']}")
print(f"Vendor Email: {response2['vendor_email']}")
print(f"Vendor ID: {response2['vendor_id']}")
print(f"Success: {response2['success']}")
print("\n📋 AI Response:")
print("-" * 80)
print(response2['response'])
print("-" * 80)

print("\n✅ Tests completed successfully!")
