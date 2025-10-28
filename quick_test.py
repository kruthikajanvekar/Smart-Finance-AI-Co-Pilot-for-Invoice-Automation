"""Fix Python import paths for Finance AI Co-Pilot"""
import os
from pathlib import Path

# Create all necessary __init__.py files
dirs = [
    'src',
    'src/agents',
    'src/llm',
    'src/utils',
    'src/integrations',
    'src/data_processing',
]

for d in dirs:
    init_file = Path(d) / '__init__.py'
    init_file.touch(exist_ok=True)
    print(f"✓ Created {init_file}")

print("\n✅ All __init__.py files created!")
print("\nNow run: streamlit run app/streamlit_app.py")

"""
UNIVERSAL FIX: Replace ALL wrong Config API key names across entire project
This fixes: GEMINI_API_KEY, OPENAI_API_KEY -> GOOGLE_API_KEY
"""

import os
import glob

# Files to search and fix
files_to_fix = [
    'src/agents/*.py',
    'src/llm/*.py',
    'app/*.py',
    'config.py',
]

# Replacements to make
replacements = [
    ('Config.GEMINI_API_KEY', 'Config.GOOGLE_API_KEY'),
    ('Config.OPENAI_API_KEY', 'Config.GOOGLE_API_KEY'),
    ('genai.api_key = Config.GOOGLE_API_KEY', '# API key configured in config.py'),
]

files_fixed = []

for pattern in files_to_fix:
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply all replacements
            for old, new in replacements:
                content = content.replace(old, new)
            
            # Only write if changes were made
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_fixed.append(filepath)
                print(f"✓ Fixed: {filepath}")
            
        except Exception as e:
            print(f"⚠ Error processing {filepath}: {e}")

print("\n" + "="*60)
if files_fixed:
    print(f"✅ Fixed {len(files_fixed)} files:")
    for f in files_fixed:
        print(f"   - {f}")
else:
    print("⚠ No files needed fixing (or already fixed)")

print("\n" + "="*60)
print("Now run: streamlit run app/streamlit_app.py")
print("="*60)