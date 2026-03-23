"""
Script to start fresh training from scratch
"""
import os
import shutil
from datetime import datetime

print("=" * 70)
print("Starting Fresh Training from Scratch")
print("=" * 70)

# Backup old models if they exist
backup_dir = 'ml_model/models/backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs(backup_dir, exist_ok=True)

models_to_backup = [
    'ml_model/models/skin_disease_model.h5',
    'ml_model/models/best_model.h5',
    'ml_model/models/training_history.png',
    'ml_model/models/training_log.csv',
    'ml_model/models/class_indices.json'
]

print("\nBacking up old models...")
for model_file in models_to_backup:
    if os.path.exists(model_file):
        backup_path = os.path.join(backup_dir, os.path.basename(model_file))
        shutil.copy2(model_file, backup_path)
        print(f"  - Backed up: {os.path.basename(model_file)}")

# Backup checkpoints directory
checkpoint_dir = 'ml_model/models/checkpoints'
if os.path.exists(checkpoint_dir) and os.listdir(checkpoint_dir):
    backup_checkpoints = os.path.join(backup_dir, 'checkpoints')
    shutil.copytree(checkpoint_dir, backup_checkpoints)
    print(f"  - Backed up checkpoints directory")

print(f"\nOld models backed up to: {backup_dir}")

# Clear old training logs (optional - comment out if you want to keep them)
if os.path.exists('ml_model/models/training_log.csv'):
    os.remove('ml_model/models/training_log.csv')
    print("  - Cleared old training log")

print("\n" + "=" * 70)
print("Starting fresh training...")
print("=" * 70)

# Import and run training
import subprocess
import sys

# Run the training script
result = subprocess.run([sys.executable, 'ml_model/train_optimized.py'], 
                       capture_output=False, text=True)

print("\n" + "=" * 70)
print("Training process completed!")
print("=" * 70)

