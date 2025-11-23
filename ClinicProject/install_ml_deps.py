#!/usr/bin/env python
"""
Install ML dependencies for waiting time prediction
"""
import subprocess
import sys

def install_ml_dependencies():
    """Install required ML packages"""
    packages = ['pandas', 'scikit-learn', 'joblib']
    
    print("Installing ML dependencies for waiting time prediction...")
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    print("\n✓ All ML dependencies installed successfully!")
    print("You can now use the AI waiting time prediction feature.")
    return True

if __name__ == "__main__":
    success = install_ml_dependencies()
    if not success:
        sys.exit(1)