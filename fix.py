"""
COMPLETE ALL-IN-ONE FIX
Solves ALL errors at once:
1. API key names (GEMINI_API_KEY, OPENAI_API_KEY, GENAI_API_KEY -> GOOGLE_API_KEY)
2. Incomplete vendor_query_agent.py
3. Incorrect try-except blocks
4. All import path issues
"""

import os
import glob

# ============================================================================
# FIX 1: Replace ALL API key naming variations
# ============================================================================
print("="*70)
print("STEP 1: Fixing API key naming issues...")
print("="*70)

files_to_fix = [
    'src/agents/*.py',
    'src/llm/*.py',
    'src/utils/*.py',
    'src/integrations/*.py',
    'src/data_processing/*.py',
    'app/*.py',
    'config.py',
]

replacements = [
    ('Config.GEMINI_API_KEY', 'Config.GOOGLE_API_KEY'),
    ('Config.OPENAI_API_KEY', 'Config.GOOGLE_API_KEY'),
    ('Config.GENAI_API_KEY', 'Config.GOOGLE_API_KEY'),
    ('Config.GeminiAPIKey', 'Config.GOOGLE_API_KEY'),
    ('Config.OpenAIAPIKey', 'Config.GOOGLE_API_KEY'),
]

api_fixed = 0
for pattern in files_to_fix:
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ {filepath}")
                api_fixed += 1
        except Exception as e:
            pass

print(f"\n✅ Fixed {api_fixed} files for API key naming")

# ============================================================================
# FIX 2: Complete vendor_query_agent.py (it's truncated!)
# ============================================================================
print("\n" + "="*70)
print("STEP 2: Fixing incomplete vendor_query_agent.py...")
print("="*70)

vendor_agent_path = 'src/agents/vendor_query_agent.py'