# 🎯 FIRST TIME UPDATE - Get the Batch File

## For Teammates Who Don't Have the Update Files Yet

---

## ⚡ THE PROBLEM

You need `QUICK_UPDATE.bat` to update easily, but you need to pull code first to get that file! 😅

---

## ✅ SOLUTION: Do This ONCE (First Time Only)

### **Step 1: Open Command Prompt**
1. Press `Windows Key + R`
2. Type: `cmd`
3. Press Enter

### **Step 2: Go to Your Project Folder**
```bash
cd C:\Users\YourName\AiClinicNew
```
(Replace `YourName` with your actual username)

### **Step 3: Pull Latest Code (ONE TIME)**
```bash
git pull origin main
```

### **Step 4: Check if You Got the Files**
```bash
dir *.bat
```

You should see: `QUICK_UPDATE.bat`

---

## 🎉 NOW YOU HAVE THE BATCH FILE!

### **From Now On (Every Future Update):**
Just double-click `QUICK_UPDATE.bat` - that's it! ✅

---

## 📋 Complete First Time Steps

```bash
# 1. Open Command Prompt (Windows Key + R, type cmd)

# 2. Go to project folder
cd C:\Users\YourName\AiClinicNew

# 3. Pull latest code
git pull origin main

# 4. Update dependencies
cd ClinicProject
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Done! ✅
```

---

## 🔄 FUTURE UPDATES (After First Time)

Just double-click: `QUICK_UPDATE.bat`

That's it! No more commands needed! 🚀

---

## 📞 Quick Reference

**First Time (Do Once):**
```
cmd → cd AiClinicNew → git pull origin main
```

**Every Time After:**
```
Double-click QUICK_UPDATE.bat
```

---

**After this first pull, you'll have all the update files and can use the easy method!** ✅
