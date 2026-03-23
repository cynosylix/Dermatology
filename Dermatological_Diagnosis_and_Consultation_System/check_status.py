"""
Simple training status checker
"""
import os
from datetime import datetime

print("=" * 70)
print("Training Status Check")
print("=" * 70)

# Check if model exists
model_path = 'ml_model/models/skin_disease_model.h5'
if os.path.exists(model_path):
    size = os.path.getsize(model_path)
    mod_time = os.path.getmtime(model_path)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[OK] Final Model file exists")
    print(f"  Location: {model_path}")
    print(f"  Size: {size / (1024*1024):.2f} MB")
    print(f"  Last modified: {mod_date}")
else:
    print(f"\n[ ] Final model file not found (training in progress)")

# Check for best model
best_model_path = 'ml_model/models/best_model.h5'
if os.path.exists(best_model_path):
    size = os.path.getsize(best_model_path)
    mod_time = os.path.getmtime(best_model_path)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[OK] Best model checkpoint exists")
    print(f"  Location: {best_model_path}")
    print(f"  Size: {size / (1024*1024):.2f} MB")
    print(f"  Last modified: {mod_date}")
    print(f"  This is the best model so far during training")
else:
    print(f"\n[ ] Best model checkpoint not found yet")

# Check for checkpoints
checkpoint_dir = 'ml_model/models/checkpoints'
if os.path.exists(checkpoint_dir):
    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith('.h5')]
    if checkpoints:
        print(f"\n[OK] Found {len(checkpoints)} checkpoint(s)")
        checkpoints.sort()
        latest = checkpoints[-1]
        mod_time = os.path.getmtime(os.path.join(checkpoint_dir, latest))
        mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  Latest checkpoint: {latest}")
        print(f"  Last updated: {mod_date}")

# Check for training log
log_path = 'ml_model/models/training_log.csv'
if os.path.exists(log_path):
    mod_time = os.path.getmtime(log_path)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[OK] Training log exists")
    print(f"  Last updated: {mod_date}")
    
    # Read last line to show progress
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_line = lines[-1].strip()
                print(f"  Latest metrics: {last_line}")
    except Exception as e:
        print(f"  Could not read log: {str(e)}")

print("\n" + "=" * 70)
print("Training is running in the background.")
print("This may take 2-4 hours depending on your hardware.")
print("The model will be saved automatically when training completes.")
print("=" * 70)

