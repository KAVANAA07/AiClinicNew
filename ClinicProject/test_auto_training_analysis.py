#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from api.models import Token
from api.auto_training_triggers import AutoTrainingManager, last_training_trigger

def analyze_auto_training_triggers():
    print("=== AUTO TRAINING TRIGGER ANALYSIS ===\n")
    
    # 1. Check training statistics
    print("1. TRAINING STATISTICS:")
    stats = AutoTrainingManager.get_training_stats()
    print(f"   Total consultations: {stats['total_consultations']}")
    print(f"   Recent consultations (7 days): {stats['recent_consultations_7days']}")
    print(f"   Last training trigger: {stats['last_training_trigger']}")
    print(f"   Ready for training: {stats['ready_for_training']}")
    
    # 2. Check recent completions (last 24 hours)
    print("\n2. RECENT COMPLETIONS (24 hours):")
    now = timezone.now()
    recent_24h = Token.objects.filter(
        status='completed',
        completed_at__isnull=False,
        completed_at__gte=now - timedelta(hours=24)
    ).count()
    print(f"   Completions in last 24h: {recent_24h}")
    print(f"   Trigger threshold: 5 completions")
    print(f"   Will trigger: {'YES' if recent_24h >= 5 else 'NO'}")
    
    # 3. Check cooldown status
    print("\n3. COOLDOWN STATUS:")
    if last_training_trigger:
        time_since_last = (now - last_training_trigger).total_seconds() / 3600
        cooldown_hours = 6
        print(f"   Time since last trigger: {time_since_last:.1f} hours")
        print(f"   Cooldown period: {cooldown_hours} hours")
        print(f"   Cooldown active: {'YES' if time_since_last < cooldown_hours else 'NO'}")
    else:
        print("   No previous training trigger recorded")
    
    # 4. Check signal registration
    print("\n4. SIGNAL REGISTRATION:")
    from django.db.models.signals import post_save
    
    # Check if our signal is registered
    receivers = post_save._live_receivers(sender=Token)
    auto_training_registered = any(
        'trigger_model_retraining' in str(receiver) 
        for receiver in receivers
    )
    print(f"   Auto training signal registered: {'YES' if auto_training_registered else 'NO'}")
    
    # 5. Check Django-Q setup
    print("\n5. DJANGO-Q SETUP:")
    try:
        from django_q.models import Schedule
        ml_schedules = Schedule.objects.filter(func='api.tasks_ml.train_waiting_time_model')
        print(f"   Scheduled ML tasks: {ml_schedules.count()}")
        for schedule in ml_schedules:
            print(f"     - {schedule.name}: {schedule.schedule_type}, next run: {schedule.next_run}")
    except Exception as e:
        print(f"   Django-Q error: {e}")
    
    # 6. Test trigger conditions
    print("\n6. TRIGGER CONDITIONS ANALYSIS:")
    
    # Check if we have enough data for training
    total_completed = Token.objects.filter(
        status='completed',
        completed_at__isnull=False
    ).count()
    
    print(f"   Minimum data requirement: 10 completed consultations")
    print(f"   Current completed consultations: {total_completed}")
    print(f"   Data requirement met: {'YES' if total_completed >= 10 else 'NO'}")
    
    # Check recent activity
    recent_12h = Token.objects.filter(
        status='completed',
        completed_at__isnull=False,
        completed_at__gte=now - timedelta(hours=12)
    ).count()
    
    print(f"   Recent activity (12h): {recent_12h} completions")
    print(f"   Conditional training threshold: 3 completions")
    print(f"   Conditional training ready: {'YES' if recent_12h >= 3 else 'NO'}")
    
    # 7. Recommendations
    print("\n7. RECOMMENDATIONS:")
    
    issues = []
    if not auto_training_registered:
        issues.append("❌ Auto training signal not registered - check apps.py ready() method")
    
    if total_completed < 10:
        issues.append("⚠️  Insufficient training data - need more completed consultations")
    
    if recent_24h < 5 and recent_12h < 3:
        issues.append("ℹ️  Low recent activity - training triggers won't activate")
    
    if not issues:
        print("   ✅ Auto training system appears to be configured correctly!")
        print("   ✅ All requirements met for automatic training")
    else:
        for issue in issues:
            print(f"   {issue}")
    
    return {
        'signal_registered': auto_training_registered,
        'sufficient_data': total_completed >= 10,
        'recent_activity': recent_24h >= 5 or recent_12h >= 3,
        'cooldown_clear': not last_training_trigger or (now - last_training_trigger).total_seconds() >= 6 * 3600
    }

if __name__ == "__main__":
    result = analyze_auto_training_triggers()
    print(f"\n=== SUMMARY ===")
    print(f"Overall Status: {'✅ WORKING' if all(result.values()) else '❌ NEEDS ATTENTION'}")