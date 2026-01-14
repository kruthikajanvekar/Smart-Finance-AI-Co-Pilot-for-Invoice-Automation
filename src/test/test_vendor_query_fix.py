#!/usr/bin/env python3
"""
Quick test script to verify vendor query agent fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.vendor_query_agent import VendorQueryAgent
from config import Config

print("=" * 60)
print("Testing Vendor Query Agent Fix")
print("=" * 60)

# Initialize agent
print("\n✓ Initializing VendorQueryAgent...")
agent = VendorQueryAgent()

# Test 1: Query with vendor email
print("\n" + "=" * 60)
print("TEST 1: Query with vendor email")
print("=" * 60)

vendor_email = "payments@techsupply.com"
query = "What's the status of my recent invoices?"

print(f"\nVendor Email: {vendor_email}")
print(f"Query: {query}")
print("\nProcessing...")

response = agent.process_vendor_query(query, vendor_email)

print("\nResponse Structure:")
for key, value in response.items():
    if key != 'response':  # Don't print full response text
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: {value[:100]}...")

# Test 2: Query without vendor email
print("\n" + "=" * 60)
print("TEST 2: Query without vendor email")
print("=" * 60)

query2 = "How do I check my invoice status?"
print(f"\nQuery: {query2}")
print("Processing...")

response2 = agent.process_vendor_query(query2)

print("\nResponse Structure:")
for key, value in response2.items():
    if key != 'response':
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: {value[:100]}...")

# Verify fixes
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

issues = []

# Check that 'status' key is NOT in response
if 'status' in response:
    issues.append("❌ 'status' key found in response (should be 'success')")
else:
    print("✅ 'status' key NOT found (correct)")

# Check that 'success' key IS in response
if 'success' not in response:
    issues.append("❌ 'success' key NOT found in response")
else:
    print("✅ 'success' key found (correct)")

# Check response structure
if 'response' not in response:
    issues.append("❌ 'response' key NOT found")
else:
    print("✅ 'response' key found (correct)")

if 'vendor_email' not in response:
    issues.append("❌ 'vendor_email' key NOT found")
else:
    print("✅ 'vendor_email' key found (correct)")

if issues:
    print("\n❌ ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe vendor query agent fix is working correctly.")
    print("The Streamlit UI error should now be resolved.")
