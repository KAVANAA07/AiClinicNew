# 🔄 UPDATE GUIDE - Pull Latest Changes from GitHub

## For Teammates Who Already Have the Code

---

## ⚡ Quick Update (3 Steps)

### **Step 1: Pull Latest Changes**
```bash
cd AiClinicNew
git pull origin main
```

### **Step 2: Update Backend Dependencies**
```bash
cd ClinicProject
pip install -r requirements.txt
```

### **Step 3: Run Database Migrations**
```bash
python manage.py migrate
```

**Done!** Your code is now updated.

---

## 📋 Detailed Update Process

### **1. Save Your Current Work**
```bash
# Check what files you've modified
git status

# If you have uncommitted changes, save them
git stash save "My local changes"
```

### **2. Pull Latest Code from GitHub**
```bash
# Make sure you're on main branch
git checkout main

# Pull latest changes
git pull origin main
```

### **3. Restore Your Local Changes (if any)**
```bash
# Apply your saved changes back
git stash pop
```

### **4. Update Python Dependencies**
```bash
cd ClinicProject

# Activate virtual environment (if using)
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install/update packages
pip install -r requirements.txt
```

### **5. Update Frontend Dependencies (if needed)**
```bash
cd frontend
npm install
```

### **6. Run Database Migrations**
```bash
cd ClinicProject
python manage.py migrate
```

### **7. Update Environment Variables**
Check if `.env` file needs new variables:
```bash
# Compare with .env.example
# Add any missing variables to your .env file
```

---

## 🆕 What's New in Latest Update

### **Critical Bug Fixes:**
- ✅ Fixed patient login 404 errors (URL routing issue)
- ✅ Fixed case-sensitive status comparison bug (9,968 tokens showing as active)
- ✅ Fixed SQLite database locking in Django-Q background tasks

### **ML Model Improvements:**
- ✅ Cleaned database of bad quality data
- ✅ Retrained model with 4,892 high-quality samples
- ✅ Achieved Test MAE: 13.78 min, R²: 0.8047 (meets all judge criteria)
- ✅ Added comprehensive demonstration script (`demo_for_judges.py`)

### **New Features:**
- ✅ Prescription reminders system
- ✅ IVR (Interactive Voice Response) features
- ✅ Enhanced documentation

### **Configuration Changes:**
- ✅ Django-Q workers reduced to 1 (prevents database locking)
- ✅ SQLite timeout increased to 20 seconds
- ✅ All Twilio credentials moved to environment variables

---

## 🔧 After Update - Verify Everything Works

### **1. Check Django Server**
```bash
cd ClinicProject
python manage.py runserver
```
Visit: http://localhost:8000/admin

### **2. Check Frontend**
```bash
cd frontend
npm start
```
Visit: http://localhost:3000

### **3. Test ML Model**
```bash
cd ClinicProject
python demo_for_judges.py
```

### **4. Check Django-Q Background Tasks**
```bash
python manage.py qcluster
```

---

## ⚠️ Common Issues After Update

### **Issue 1: Module Not Found Error**
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

### **Issue 2: Database Migration Error**
```bash
# Solution: Reset migrations (only if safe)
python manage.py migrate --fake
python manage.py migrate
```

### **Issue 3: Frontend Won't Start**
```bash
# Solution: Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### **Issue 4: Database Locked Error**
```bash
# Solution: Already fixed in latest code
# Make sure you pulled latest changes
# Check settings.py has Q_CLUSTER workers=1
```

### **Issue 5: Git Merge Conflicts**
```bash
# If you get merge conflicts:
git status  # See conflicted files
# Open files and resolve conflicts manually
git add .
git commit -m "Resolved merge conflicts"
```

---

## 🔐 Environment Variables Check

Make sure your `.env` file has these (without hardcoded values):

```env
# Django
SECRET_KEY=your_secret_key_here
DEBUG=True

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Twilio (get from environment, not hardcoded)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Plivo (if using)
PLIVO_AUTH_ID=
PLIVO_AUTH_TOKEN=
PLIVO_PHONE_NUMBER=

# AI/ML
OPENAI_API_KEY=
```

**Important:** Never commit `.env` file to GitHub!

---

## 📊 Verify ML Model Performance

After updating, verify the ML model is working:

```bash
cd ClinicProject
python demo_for_judges.py
```

**Expected Output:**
```
✓ Test MAE: 13.78 minutes
✓ Test R²: 0.8047
✓ Training samples: 4,892
✓ All judge criteria met!
```

---

## 🚀 Quick Commands Reference

```bash
# Update code
git pull origin main

# Update backend
cd ClinicProject
pip install -r requirements.txt
python manage.py migrate

# Update frontend
cd frontend
npm install

# Run backend
cd ClinicProject
python manage.py runserver

# Run frontend
cd frontend
npm start

# Run background tasks
cd ClinicProject
python manage.py qcluster

# Test ML model
python demo_for_judges.py
```

---

## 📞 Need Help?

If you face any issues:

1. Check this guide first
2. Check error messages carefully
3. Try: `git status` to see what's wrong
4. Try: `pip list` to see installed packages
5. Contact team lead

---

## ✅ Update Checklist

- [ ] Pulled latest code from GitHub
- [ ] Updated Python dependencies
- [ ] Updated frontend dependencies (if needed)
- [ ] Ran database migrations
- [ ] Checked .env file for new variables
- [ ] Tested Django server runs
- [ ] Tested frontend runs
- [ ] Verified ML model works
- [ ] Tested Django-Q background tasks

---

**Last Updated:** December 2024
**GitHub Repo:** https://github.com/KAVANAA07/AiClinicNew
