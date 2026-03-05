"""
Quick script to check if training is running and model status
"""
import os
import time
import csv
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
    print(f"\n✓ Final Model file exists")
    print(f"  - Location: {model_path}")
    print(f"  - Size: {size / (1024*1024):.2f} MB")
    print(f"  - Last modified: {mod_date}")
else:
    print(f"\n✗ Final model file not found at {model_path}")

# Check for best model
best_model_path = 'ml_model/models/best_model.h5'
if os.path.exists(best_model_path):
    size = os.path.getsize(best_model_path)
    mod_time = os.path.getmtime(best_model_path)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n✓ Best model checkpoint exists")
    print(f"  - Location: {best_model_path}")
    print(f"  - Size: {size / (1024*1024):.2f} MB")
    print(f"  - Last modified: {mod_date}")
    print(f"  - This is the best model so far during training")
else:
    print(f"\n✗ Best model checkpoint not found yet (training may be in progress)")

# Check for checkpoints
checkpoint_dir = 'ml_model/models/checkpoints'
if os.path.exists(checkpoint_dir):
    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith('.h5')]
    if checkpoints:
        print(f"\n✓ Found {len(checkpoints)} checkpoint(s)")
        checkpoints.sort()
        latest = checkpoints[-1]
        mod_time = os.path.getmtime(os.path.join(checkpoint_dir, latest))
        mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  - Latest checkpoint: {latest}")
        print(f"  - Last updated: {mod_date}")

# Check for training log
log_path = 'ml_model/models/training_log.csv'
if os.path.exists(log_path):
    mod_time = os.path.getmtime(log_path)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n✓ Training log exists")
    print(f"  - Last updated: {mod_date}")
    
    # Read last few lines to show progress
    try:
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                print(f"\n📊 Latest Training Metrics:")
                if 'epoch' in last_row:
                    print(f"  - Epoch: {last_row['epoch']}")
                if 'accuracy' in last_row:
                    print(f"  - Training Accuracy: {float(last_row['accuracy'])*100:.2f}%")
                if 'val_accuracy' in last_row:
                    print(f"  - Validation Accuracy: {float(last_row['val_accuracy'])*100:.2f}%")
                if 'loss' in last_row:
                    print(f"  - Loss: {float(last_row['loss']):.4f}")
                if 'val_loss' in last_row:
                    print(f"  - Validation Loss: {float(last_row['val_loss']):.4f}")
                
                # Find max accuracy
                if 'val_accuracy' in last_row:
                    max_acc = max([float(r['val_accuracy']) for r in rows if 'val_accuracy' in r and r['val_accuracy']])
                    print(f"\n🏆 Maximum Validation Accuracy so far: {max_acc*100:.2f}%")
    except Exception as e:
        print(f"  - Could not read log: {str(e)}")

# Check for training history
history_path = 'ml_model/models/training_history.png'
if os.path.exists(history_path):
    mod_time = os.path.getmtime(history_path)
    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n✓ Training history graph exists")
    print(f"  - Last updated: {mod_date}")

print("\n" + "=" * 70)
print("Note: Training may take 2-4 hours depending on your hardware.")
print("The model will be saved automatically when training completes.")
print("Checkpoints are saved every 5 epochs.")
print("=" * 70)

