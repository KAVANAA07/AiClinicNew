# Automatic AI Model Training System

## 🤖 **Complete Automatic Training Implementation**

### **Problem Solved**
The AI model now automatically trains from **ALL consultation data** (not just last 30 days) and retrains whenever new consultations are completed.

---

## 🔄 **Automatic Training Triggers**

### **1. Real-time Signal-Based Training**
```python
# Triggers automatically when consultations are completed
@receiver(post_save, sender=Token)
def trigger_model_retraining(sender, instance, **kwargs):
    if instance.status == 'completed' and instance.consultation_start_time:
        # Check if we have 5+ new consultations in last 24 hours
        if recent_completions >= 5:
            # Automatically trigger background retraining
            async_task('api.tasks_ml.train_waiting_time_model')
```

**When it triggers:**
- After every 5 completed consultations in 24 hours
- Cooldown period: 6 hours (prevents excessive retraining)
- Runs in background (doesn't block system)

### **2. Scheduled Periodic Training**
```python
# Every 12 hours - check for new data and retrain if needed
schedule('conditional_training_task', schedule_type='H', minutes=12*60)

# Nightly full retrain at 2 AM with ALL data
schedule('train_waiting_time_model', schedule_type='D', next_run='02:00')
```

**Schedule:**
- **Every 12 hours**: Conditional training (if 3+ new consultations)
- **Daily 2 AM**: Full retraining with ALL historical data
- **On-demand**: Manual trigger via API

### **3. Data Usage Policy**
```python
# OLD: Only last 30 days
tokens = Token.objects.filter(created_at__date__gte=start_date)

# NEW: ALL consultation data
tokens = Token.objects.filter(
    status='completed',
    consultation_start_time__isnull=False
)
```

**Benefits:**
- Uses complete historical knowledge
- Better accuracy with more data
- Learns long-term patterns
- No data loss from time windows

---

## 📊 **Training Management APIs**

### **1. Training Status Dashboard**
```http
GET /api/training/manage/
```
**Response:**
```json
{
  "training_statistics": {
    "total_consultations": 500,
    "recent_consultations_7days": 45,
    "last_training_trigger": "2025-11-23T14:30:00Z",
    "ready_for_training": true
  },
  "training_triggers": {
    "nightly_full_retrain": "2:00 AM daily",
    "automatic_triggers": "Every 12 hours if 3+ new consultations",
    "signal_based": "After 5+ consultations in 24 hours"
  },
  "data_usage": "ALL historical consultation data"
}
```

### **2. Manual Training Control**
```http
POST /api/training/manage/
Content-Type: application/json
{
  "action": "train"
}
```
**Actions:**
- `"train"`: Force immediate retraining with all data
- `"setup_schedules"`: Reset automatic training schedules
- `"stats"`: Get detailed training statistics

### **3. Data Quality Monitoring**
```http
GET /api/training/data-quality/
```
**Response:**
```json
{
  "total_consultations": 500,
  "period_breakdown": {
    "last_24h": 8,
    "last_7d": 45,
    "last_30d": 180,
    "last_90d": 420
  },
  "data_quality_score": 100.0,
  "training_readiness": {
    "ready": true,
    "minimum_required": 10,
    "recommended": 50,
    "excellent": 100
  }
}
```

---

## ⚡ **How Automatic Training Works**

### **Step 1: Consultation Completion**
```python
# When doctor completes consultation:
token.status = 'completed'
token.consultation_start_time = timezone.now()
token.save()  # This triggers the signal
```

### **Step 2: Automatic Detection**
```python
# Signal handler automatically detects:
- New consultation completed ✓
- Has consultation_start_time ✓
- Count recent completions
- Check cooldown period
- Decide if retraining needed
```

### **Step 3: Background Training**
```python
# If criteria met, schedule background task:
async_task('api.tasks_ml.train_waiting_time_model')

# Training uses ALL data:
all_consultations = Token.objects.filter(
    status='completed',
    consultation_start_time__isnull=False
)
# Result: Model trained on complete history
```

### **Step 4: Model Update**
```python
# New model automatically replaces old one:
joblib.dump(trained_model, 'waiting_time_model.pkl')
joblib.dump(scaler, 'waiting_time_scaler.pkl')

# Next predictions use updated model
```

---

## 🎯 **Training Frequency Examples**

### **Busy Clinic Scenario**
- **Day 1**: 10 consultations completed → Auto-retrain triggered
- **Day 2**: 8 consultations completed → Auto-retrain triggered  
- **Day 3**: 3 consultations completed → No retrain (below threshold)
- **Every Night**: Full retrain at 2 AM with ALL data

### **Slow Clinic Scenario**
- **Week 1**: 15 consultations total → 2 auto-retrains
- **Week 2**: 8 consultations total → 1 auto-retrain
- **Every Night**: Full retrain at 2 AM (even with little new data)

---

## 📈 **Data Growth Impact**

### **Traditional Approach (30-day window)**
```
Month 1: 100 consultations → Model uses 100 records
Month 6: 600 consultations → Model still uses ~100 records (last 30 days)
Month 12: 1200 consultations → Model still uses ~100 records
```

### **Our Approach (ALL data)**
```
Month 1: 100 consultations → Model uses 100 records
Month 6: 600 consultations → Model uses 600 records ✓
Month 12: 1200 consultations → Model uses 1200 records ✓
```

**Result**: Model gets smarter over time, not stuck with limited data!

---

## 🔧 **Setup Instructions**

### **1. Enable Automatic Training**
```bash
# Setup schedules and signals
python manage.py shell -c "
from api.tasks_ml import setup_ml_schedules
setup_ml_schedules()
"
```

### **2. Start Background Worker**
```bash
# Required for automatic training
python manage.py qcluster
```

### **3. Test Automatic Training**
```bash
# Force immediate training with all data
curl -X POST http://localhost:8000/api/training/manage/ \
  -H "Content-Type: application/json" \
  -d '{"action": "train"}'
```

### **4. Monitor Training Status**
```bash
# Check training statistics
curl http://localhost:8000/api/training/manage/

# Check data quality
curl http://localhost:8000/api/training/data-quality/
```

---

## 🏆 **Benefits for Judges**

### **Technical Excellence**
- ✅ **Complete Data Usage**: Uses ALL consultation history
- ✅ **Real-time Learning**: Automatically improves with new data
- ✅ **Smart Triggers**: Only retrains when beneficial
- ✅ **Background Processing**: Doesn't impact system performance

### **Business Impact**
- ✅ **Continuous Improvement**: Model gets better over time
- ✅ **No Manual Intervention**: Fully automated system
- ✅ **Scalable**: Handles growing data automatically
- ✅ **Reliable**: Multiple training triggers ensure freshness

### **Innovation**
- ✅ **Signal-Based Training**: Retrains on actual events
- ✅ **Intelligent Scheduling**: Balances freshness vs efficiency
- ✅ **Complete History**: Learns from all available data
- ✅ **Production Ready**: Handles real-world clinic operations

---

## 📊 **Monitoring Dashboard**

The system provides comprehensive monitoring:

1. **Training Statistics**: How much data, when last trained
2. **Data Quality Scores**: Readiness for training
3. **Automatic Triggers**: What causes retraining
4. **Manual Controls**: Force training when needed
5. **Performance Metrics**: Model accuracy over time

**Key URLs for Judges:**
- Training Management: `/api/training/manage/`
- Data Quality: `/api/training/data-quality/`
- Model Accuracy: `/api/model/accuracy/`

The AI model now **automatically evolves** with your clinic's data, ensuring predictions stay accurate as patterns change!