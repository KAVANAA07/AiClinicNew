@echo off
echo ========================================
echo   AI CLINIC - QUICK UPDATE SCRIPT
echo ========================================
echo.

echo [1/5] Pulling latest code from GitHub...
git pull origin main
if errorlevel 1 (
    echo ERROR: Failed to pull from GitHub
    pause
    exit /b 1
)
echo ✓ Code updated successfully
echo.

echo [2/5] Updating Python dependencies...
cd ClinicProject
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies updated
echo.

echo [3/5] Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Migration failed
    pause
    exit /b 1
)
echo ✓ Database migrated
echo.

echo [4/5] Checking ML model...
python demo_for_judges.py
echo.

echo [5/5] Update complete!
echo.
echo ========================================
echo   NEXT STEPS:
echo ========================================
echo 1. Start backend:  python manage.py runserver
echo 2. Start frontend: cd frontend ^&^& npm start
echo 3. Start Django-Q: python manage.py qcluster
echo ========================================
echo.
pause
