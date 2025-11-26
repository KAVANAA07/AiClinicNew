# 🎯 HOW TO UPDATE CODE - SIMPLE GUIDE

## For Teammates Who Already Have the Project

---

## 🖱️ METHOD 1: Using Batch File (EASIEST - Just 2 Clicks!)

### **Step 1: Find the File**
1. Open your project folder: `AiClinicNew`
2. Look for file named: **`QUICK_UPDATE.bat`**
3. It looks like this: 📄 QUICK_UPDATE.bat

### **Step 2: Double-Click It**
1. **Double-click** on `QUICK_UPDATE.bat`
2. A black window will open
3. Wait for it to finish (shows progress)
4. Press any key when it says "Press any key to continue..."

### **That's it! ✅ Your code is updated!**

---

## ⌨️ METHOD 2: Using Commands (Manual Way)

### **Step 1: Open Command Prompt**
1. Press `Windows Key + R`
2. Type: `cmd`
3. Press Enter

### **Step 2: Go to Project Folder**
```bash
cd C:\Users\VITUS\AiClinicNew
```
(Replace with your actual path)

### **Step 3: Run These 3 Commands**

**Command 1 - Pull Latest Code:**
```bash
git pull origin main
```
Wait for it to finish...

**Command 2 - Update Dependencies:**
```bash
cd ClinicProject
pip install -r requirements.txt
```
Wait for it to finish...

**Command 3 - Update Database:**
```bash
python manage.py migrate
```
Done! ✅

---

## 📸 Visual Guide - Using Batch File

### **What You'll See:**

**1. Before Running:**
```
📁 AiClinicNew
   📄 QUICK_UPDATE.bat  ← Double-click this file
   📁 ClinicProject
   📁 frontend
   📄 README.md
```

**2. After Double-Clicking:**
```
========================================
  AI CLINIC - QUICK UPDATE SCRIPT
========================================

[1/5] Pulling latest code from GitHub...
✓ Code updated successfully

[2/5] Updating Python dependencies...
✓ Dependencies updated

[3/5] Running database migrations...
✓ Database migrated

[4/5] Checking ML model...
✓ Test MAE: 13.78 minutes
✓ Test R²: 0.8047

[5/5] Update complete!

========================================
  NEXT STEPS:
========================================
1. Start backend:  python manage.py runserver
2. Start frontend: cd frontend && npm start
3. Start Django-Q: python manage.py qcluster
========================================

Press any key to continue...
```

**3. Press Any Key:**
- Window will close
- Your code is updated! ✅

---

## ❓ Common Questions

### **Q: Where is the batch file?**
**A:** In your main project folder `AiClinicNew`, look for `QUICK_UPDATE.bat`

### **Q: What if I don't see .bat extension?**
**A:** 
1. Open File Explorer
2. Click "View" menu
3. Check "File name extensions"
4. Now you'll see `.bat` at the end

### **Q: What if double-clicking doesn't work?**
**A:** 
1. Right-click on `QUICK_UPDATE.bat`
2. Select "Run as administrator"

### **Q: What if I get an error?**
**A:** 
1. Make sure you have internet connection
2. Make sure you're in the correct folder
3. Try METHOD 2 (manual commands) instead

### **Q: Do I need to do this every time?**
**A:** Only when your team lead says "New update pushed to GitHub"

---

## 🎬 Step-by-Step with Screenshots

### **For Windows Users:**

**Step 1:** Open your project folder
```
This PC → Documents → AiClinicNew
```

**Step 2:** Find QUICK_UPDATE.bat
```
Look for a file with gear icon ⚙️ or document icon 📄
Name: QUICK_UPDATE.bat
```

**Step 3:** Double-click it
```
Left mouse button → Click twice quickly
```

**Step 4:** Wait for it to finish
```
Black window appears → Shows progress → Finishes
```

**Step 5:** Press any key
```
Keyboard → Press any key → Window closes
```

**Done!** ✅

---

## 🔍 What Does the Batch File Do?

The batch file automatically runs these commands for you:

1. **`git pull origin main`** - Downloads latest code from GitHub
2. **`pip install -r requirements.txt`** - Installs any new Python packages
3. **`python manage.py migrate`** - Updates database structure
4. **`python demo_for_judges.py`** - Tests if ML model works

Instead of typing 4 commands, you just double-click! 🎯

---

## ⚠️ Before Running Update

### **Save Your Work First!**
If you made any changes to the code:

**Option A - Save Your Changes:**
```bash
git add .
git commit -m "My changes"
git pull origin main
```

**Option B - Temporarily Save:**
```bash
git stash
git pull origin main
git stash pop
```

**Option C - Discard Your Changes:**
```bash
git reset --hard
git pull origin main
```

---

## ✅ After Update - Verify It Worked

### **Check 1: See if code updated**
```bash
git log -1
```
Should show latest commit

### **Check 2: Test backend**
```bash
cd ClinicProject
python manage.py runserver
```
Visit: http://localhost:8000

### **Check 3: Test ML model**
```bash
python demo_for_judges.py
```
Should show: MAE: 13.78, R²: 0.8047

---

## 🆘 If Something Goes Wrong

### **Error: "git is not recognized"**
**Solution:** Install Git first
- Download: https://git-scm.com/download/win
- Install it
- Restart computer
- Try again

### **Error: "python is not recognized"**
**Solution:** Python not in PATH
- Open Command Prompt as Administrator
- Type: `where python`
- If nothing shows, reinstall Python with "Add to PATH" checked

### **Error: "pip is not recognized"**
**Solution:** 
```bash
python -m pip install -r requirements.txt
```

### **Error: "Permission denied"**
**Solution:** 
- Right-click `QUICK_UPDATE.bat`
- Select "Run as administrator"

---

## 📞 Still Confused?

### **Ask Your Team Lead:**
"Hey, I need help updating the code. Can you show me how to run QUICK_UPDATE.bat?"

### **Or Use This Simple Way:**
1. Open project folder
2. Find file: `QUICK_UPDATE.bat`
3. Double-click it
4. Wait
5. Done!

---

## 🎓 Summary

### **Easiest Way:**
```
1. Find QUICK_UPDATE.bat in project folder
2. Double-click it
3. Wait for it to finish
4. Press any key
5. Done! ✅
```

### **Manual Way:**
```
1. Open Command Prompt
2. cd AiClinicNew
3. git pull origin main
4. cd ClinicProject
5. pip install -r requirements.txt
6. python manage.py migrate
7. Done! ✅
```

---

**That's it! You're now updated with the latest code! 🚀**
