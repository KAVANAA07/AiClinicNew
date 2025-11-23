# Quick Fix: ML Dependencies Error

## Problem
Server won't start due to missing pandas/scikit-learn dependencies:
```
ModuleNotFoundError: No module named 'pandas'
```

## Solution Options

### Option 1: Install Dependencies (Recommended)
```bash
# Install ML dependencies
python install_ml_deps.py

# OR manually:
pip install pandas scikit-learn joblib
```

### Option 2: Run Without ML Features
The server will now start without ML dependencies. The waiting time prediction feature will be disabled but all other features work normally.

## Verification
After installing dependencies, test the ML system:
```bash
python test_waiting_time_prediction.py
```

## What's Fixed
- Server starts even without ML dependencies
- ML features gracefully disabled when dependencies missing
- Clear error messages guide users to install dependencies
- All other clinic features work normally

## For Your Teammate
1. **Clone repo** - All code is ready
2. **Install ML deps** - Run `python install_ml_deps.py`
3. **Start server** - `python manage.py runserver`
4. **Test ML** - `python test_waiting_time_prediction.py`

The AI waiting time prediction is now optional and won't break the server startup!