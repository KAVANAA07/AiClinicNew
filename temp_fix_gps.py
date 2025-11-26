#!/usr/bin/env python3
"""
TEMPORARY FIX: Increase GPS distance limit for testing
This will allow arrival confirmation from a larger distance
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('c:\\Users\\VITUS\\AiClinicNew\\ClinicProject')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

def create_temp_fix():
    """Create a temporary fix by modifying the distance check"""
    
    views_file = 'c:\\Users\\VITUS\\AiClinicNew\\ClinicProject\\api\\views.py'
    
    # Read the current file
    with open(views_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the 1km limit with 10km for testing
    old_line = "if distance > 1.0: # 1km radius check"
    new_line = "if distance > 10.0: # TEMPORARY: 10km radius check for testing"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Write back the modified content
        with open(views_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ TEMPORARY FIX APPLIED!")
        print("GPS distance limit increased from 1km to 10km")
        print("You should now be able to confirm arrival from further away")
        print()
        print("⚠️  IMPORTANT: This is temporary for testing only!")
        print("Remember to change it back to 1km for production use")
        print()
        print("To revert back to 1km:")
        print("1. Change '10.0' back to '1.0' in api/views.py")
        print("2. Or run the revert script")
        
    else:
        print("❌ Could not find the distance check line to modify")
        print("You may need to manually edit api/views.py")
        print(f"Look for: {old_line}")
        print(f"Change to: {new_line}")

def create_revert_script():
    """Create a script to revert the temporary fix"""
    revert_script = '''#!/usr/bin/env python3
"""
REVERT SCRIPT: Change GPS distance limit back to 1km
"""

views_file = 'c:\\\\Users\\\\VITUS\\\\AiClinicNew\\\\ClinicProject\\\\api\\\\views.py'

with open(views_file, 'r', encoding='utf-8') as f:
    content = f.read()

old_line = "if distance > 10.0: # TEMPORARY: 10km radius check for testing"
new_line = "if distance > 1.0: # 1km radius check"

if old_line in content:
    content = content.replace(old_line, new_line)
    with open(views_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ GPS distance limit reverted back to 1km")
else:
    print("❌ Temporary fix not found or already reverted")
'''
    
    with open('c:\\Users\\VITUS\\AiClinicNew\\revert_gps_fix.py', 'w') as f:
        f.write(revert_script)
    
    print("📝 Created revert_gps_fix.py script")

if __name__ == "__main__":
    print("=== TEMPORARY GPS FIX ===")
    print()
    create_temp_fix()
    create_revert_script()
    print()
    print("Next steps:")
    print("1. Restart your Django server")
    print("2. Try confirming arrival again")
    print("3. Check the distance shown in the error message")
    print("4. Use that info to fix the real GPS coordinates")
    print("5. Run revert_gps_fix.py to restore 1km limit")