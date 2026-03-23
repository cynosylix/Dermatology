"""
Optimized Training script for Skin Disease Classification Model
Uses EfficientNetB3 with maximum accuracy settings, checkpointing, and imbalanced data handling
"""
import os
import json
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB3
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt
import time
from collections import Counter

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class MaxAccuracyCallback(keras.callbacks.Callback):
    """Callback to track and display maximum accuracy"""
    def __init__(self):
        super().__init__()
        self.max_val_accuracy = 0.0
        self.max_train_accuracy = 0.0
        self.best_epoch = 0
        
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        val_acc = logs.get('val_accuracy', 0)
        train_acc = logs.get('accuracy', 0)
        
        if val_acc > self.max_val_accuracy:
            self.max_val_accuracy = val_acc
            self.best_epoch = epoch + 1
            print(f"\n🎯 NEW MAX VALIDATION ACCURACY: {val_acc:.4f} ({val_acc*100:.2f}%) at epoch {epoch + 1}")
        
        if train_acc > self.max_train_accuracy:
            self.max_train_accuracy = train_acc
            
        print(f"   Current Max Val Accuracy: {self.max_val_accuracy:.4f} ({self.max_val_accuracy*100:.2f}%)")
        print(f"   Current Max Train Accuracy: {self.max_train_accuracy:.4f} ({self.max_train_accuracy*100:.2f}%)")

def load_dataset_optimized(dataset_path, img_size=(224, 224), balance_classes=True):
    """
    Load images from dataset directory with class balancing
    
    Args:
        dataset_path: Path to dataset directory
        img_size: Target image size
        balance_classes: If True, balance classes by limiting to min class size
    
    Returns:
        X: Image arrays
        y: Labels
        class_names: List of class names
        class_weights: Dictionary of class weights for imbalanced data
    """
    X = []
    y = []
    
    # Get all class directories
    class_dirs = [d for d in os.listdir(dataset_path) 
                  if os.path.isdir(os.path.join(dataset_path, d))]
    class_dirs.sort()
    
    class_to_idx = {class_name: idx for idx, class_name in enumerate(class_dirs)}
    
    print(f"Found {len(class_dirs)} classes: {class_dirs}")
    
    # First pass: count images per class
    class_counts = {}
    for class_name in class_dirs:
        class_path = os.path.join(dataset_path, class_name)
        image_files = [f for f in os.listdir(class_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        class_counts[class_name] = len(image_files)
        print(f"  {class_name}: {class_counts[class_name]} images")
    
    # Determine max samples per class (use minimum if balancing)
    if balance_classes:
        min_count = min(class_counts.values())
        max_samples = min_count
        print(f"\n📊 Balancing classes: Using {max_samples} samples per class (minimum)")
    else:
        max_samples = max(class_counts.values())
        print(f"\n📊 Using all available images (up to {max_samples} per class)")
    
    # Load images
    total_images = 0
    for class_name in class_dirs:
        class_path = os.path.join(dataset_path, class_name)
        image_files = [f for f in os.listdir(class_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Limit samples if balancing
        if len(image_files) > max_samples:
            import random
            random.seed(42)  # For reproducibility
            random.shuffle(image_files)
            image_files = image_files[:max_samples]
        
        print(f"Loading {len(image_files)} images from {class_name}...")
        
        for img_file in image_files:
            try:
                img_path = os.path.join(class_path, img_file)
                img = Image.open(img_path)
                
                # Auto-orient
                img = ImageOps.exif_transpose(img)
                
                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize
                img = img.resize(img_size, Image.Resampling.LANCZOS)
                
                # Convert to array and normalize
                img_array = np.array(img, dtype=np.float32) / 255.0
                
                X.append(img_array)
                y.append(class_to_idx[class_name])
                total_images += 1
            except Exception as e:
                print(f"Error loading {img_path}: {str(e)}")
                continue
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"\n✅ Total images loaded: {total_images}")
    print(f"   Image shape: {X[0].shape}")
    print(f"   Number of classes: {len(class_dirs)}")
    
    # Calculate class weights for imbalanced data
    class_weights_dict = {}
    unique_classes = np.unique(y)
    class_weights = compute_class_weight('balanced', classes=unique_classes, y=y)
    
    for idx, class_idx in enumerate(unique_classes):
        class_weights_dict[int(class_idx)] = float(class_weights[idx])
    
    print(f"\n📈 Class distribution:")
    class_dist = Counter(y)
    for class_idx, count in sorted(class_dist.items()):
        class_name = class_dirs[class_idx]
        weight = class_weights_dict[class_idx]
        print(f"   {class_name}: {count} samples (weight: {weight:.3f})")
    
    # Save class indices
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    
    return X, y, class_dirs, class_to_idx, idx_to_class, class_weights_dict

def create_optimized_model(num_classes, img_size=(224, 224)):
    """
    Create an optimized model for maximum accuracy
    
    Args:
        num_classes: Number of disease classes
        img_size: Input image size
    
    Returns:
        Compiled model
    """
    # Use EfficientNetB3 as base model
    base_model = EfficientNetB3(
        weights='imagenet',
        include_top=False,
        input_shape=(img_size[0], img_size[1], 3)
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Build optimized model
    inputs = keras.Input(shape=(img_size[0], img_size[1], 3))
    
    # Enhanced data augmentation
    x = layers.RandomRotation(0.2)(inputs)
    x = layers.RandomFlip("horizontal")(x)
    x = layers.RandomFlip("vertical")(x)
    x = layers.RandomZoom(0.15)(x)
    x = layers.RandomBrightness(0.15)(x)
    x = layers.RandomContrast(0.15)(x)
    
    # Preprocessing for EfficientNet
    x = keras.applications.efficientnet.preprocess_input(x)
    
    # Base model
    x = base_model(x, training=False)
    
    # Enhanced feature extraction
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    
    # Dense layers with regularization
    x = layers.Dense(1024, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    
    x = layers.Dense(256, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    
    # Output layer
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = models.Model(inputs, outputs)
    
    # Compile model with optimized settings
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy', 'top_3_accuracy']
    )
    
    return model, base_model

def train_optimized_model(dataset_path, epochs=50, batch_size=32, validation_split=0.2, 
                          fine_tune_epochs=20, balance_classes=True):
    """
    Train the optimized skin disease classification model with maximum accuracy
    
    Args:
        dataset_path: Path to dataset directory
        epochs: Number of training epochs
        batch_size: Batch size for training
        validation_split: Fraction of data to use for validation
        fine_tune_epochs: Number of epochs for fine-tuning
        balance_classes: If True, balance classes by limiting to min class size
    """
    print("=" * 80)
    print("OPTIMIZED SKIN DISEASE CLASSIFICATION MODEL TRAINING")
    print("Maximum Accuracy Configuration")
    print("=" * 80)
    
    start_time = time.time()
    
    # Load dataset
    print("\n1. Loading and balancing dataset...")
    img_size = (224, 224)
    X, y, class_names, class_to_idx, idx_to_class, class_weights = load_dataset_optimized(
        dataset_path, img_size=img_size, balance_classes=balance_classes
    )
    num_classes = len(class_names)
    
    # Split dataset
    print("\n2. Splitting dataset...")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=validation_split, random_state=42, stratify=y
    )
    
    print(f"   ✅ Training samples: {len(X_train)}")
    print(f"   ✅ Validation samples: {len(X_val)}")
    
    # Create model
    print("\n3. Creating optimized model with EfficientNetB3...")
    model, base_model = create_optimized_model(num_classes, img_size=img_size)
    
    print(f"   ✅ Model created with {model.count_params():,} parameters")
    
    # Enhanced data augmentation
    datagen = ImageDataGenerator(
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.3,
        horizontal_flip=True,
        vertical_flip=True,
        brightness_range=[0.7, 1.3],
        fill_mode='nearest'
    )
    
    # Create checkpoint directory
    checkpoint_dir = 'ml_model/models/checkpoints'
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Enhanced callbacks with checkpointing
    max_acc_callback = MaxAccuracyCallback()
    
    callbacks = [
        max_acc_callback,
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            patience=15,
            restore_best_weights=True,
            verbose=1,
            mode='max'
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.3,
            patience=7,
            min_lr=1e-8,
            verbose=1,
            mode='min'
        ),
        # Save best model
        keras.callbacks.ModelCheckpoint(
            'ml_model/models/best_model.h5',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1,
            mode='max',
            save_weights_only=False
        ),
        # Save checkpoint every 5 epochs
        keras.callbacks.ModelCheckpoint(
            os.path.join(checkpoint_dir, 'checkpoint_epoch_{epoch:02d}_val_acc_{val_accuracy:.4f}.h5'),
            monitor='val_accuracy',
            save_best_only=False,
            save_freq='epoch',
            period=5,
            verbose=1
        ),
        # CSV logger
        keras.callbacks.CSVLogger('ml_model/models/training_log.csv', append=False)
    ]
    
    # Phase 1: Train with frozen base model
    print("\n4. Phase 1: Training with frozen base model...")
    print(f"   📊 Epochs: {epochs}")
    print(f"   📊 Batch size: {batch_size}")
    print(f"   📊 Using class weights for imbalanced data")
    
    history1 = model.fit(
        datagen.flow(X_train, y_train, batch_size=batch_size),
        steps_per_epoch=len(X_train) // batch_size,
        epochs=epochs,
        validation_data=(X_val, y_val),
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1
    )
    
    # Phase 2: Fine-tuning
    if fine_tune_epochs > 0:
        print("\n5. Phase 2: Fine-tuning (unfreezing base model)...")
        base_model.trainable = True
        
        # Fine-tune from this layer onwards (unfreeze last 40 layers)
        fine_tune_at = len(base_model.layers) - 40
        
        for layer in base_model.layers[:fine_tune_at]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001, beta_1=0.9, beta_2=0.999),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy', 'top_3_accuracy']
        )
        
        print(f"   📊 Fine-tuning last {len(base_model.layers) - fine_tune_at} layers")
        print(f"   📊 Epochs: {fine_tune_epochs}")
        
        # Reset max accuracy callback for fine-tuning phase
        max_acc_callback_ft = MaxAccuracyCallback()
        callbacks_ft = [
            max_acc_callback_ft,
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=12,
                restore_best_weights=True,
                verbose=1,
                mode='max'
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.3,
                patience=6,
                min_lr=1e-8,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                'ml_model/models/best_model.h5',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1,
                mode='max'
            ),
            keras.callbacks.CSVLogger('ml_model/models/training_log.csv', append=True)
        ]
        
        history2 = model.fit(
            datagen.flow(X_train, y_train, batch_size=batch_size),
            steps_per_epoch=len(X_train) // batch_size,
            epochs=fine_tune_epochs,
            validation_data=(X_val, y_val),
            class_weight=class_weights,
            callbacks=callbacks_ft,
            verbose=1
        )
    else:
        history2 = None
    
    # Save final model
    print("\n6. Saving final model...")
    model_path = 'ml_model/models/skin_disease_model.h5'
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"   ✅ Model saved to {model_path}")
    
    # Save class indices
    indices_path = 'ml_model/models/class_indices.json'
    with open(indices_path, 'w') as f:
        json.dump(class_to_idx, f, indent=2)
    print(f"   ✅ Class indices saved to {indices_path}")
    
    # Evaluate model
    print("\n7. Final Model Evaluation...")
    test_loss, test_accuracy, test_top3 = model.evaluate(X_val, y_val, verbose=0)
    print(f"   🎯 Final Validation Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    if test_top3:
        print(f"   🎯 Final Top-3 Accuracy: {test_top3:.4f} ({test_top3*100:.2f}%)")
    
    # Print maximum accuracies
    print("\n8. Maximum Accuracies Achieved:")
    print(f"   🏆 Maximum Validation Accuracy: {max_acc_callback.max_val_accuracy:.4f} ({max_acc_callback.max_val_accuracy*100:.2f}%)")
    print(f"   🏆 Maximum Training Accuracy: {max_acc_callback.max_train_accuracy:.4f} ({max_acc_callback.max_train_accuracy*100:.2f}%)")
    if history2:
        print(f"   🏆 Fine-tuning Max Val Accuracy: {max_acc_callback_ft.max_val_accuracy:.4f} ({max_acc_callback_ft.max_val_accuracy*100:.2f}%)")
    
    # Plot training history
    print("\n9. Saving training history...")
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.plot(history1.history['accuracy'], label='Train Accuracy', linewidth=2)
    plt.plot(history1.history['val_accuracy'], label='Val Accuracy', linewidth=2)
    if history2:
        plt.plot([x + len(history1.history['accuracy']) for x in range(len(history2.history['accuracy']))], 
                 history2.history['accuracy'], label='Fine-tune Train Acc', linewidth=2, linestyle='--')
        plt.plot([x + len(history1.history['val_accuracy']) for x in range(len(history2.history['val_accuracy']))], 
                 history2.history['val_accuracy'], label='Fine-tune Val Acc', linewidth=2, linestyle='--')
    plt.axhline(y=max_acc_callback.max_val_accuracy, color='r', linestyle=':', label=f'Max Val Acc: {max_acc_callback.max_val_accuracy:.4f}')
    plt.title('Model Accuracy', fontsize=14, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 2)
    plt.plot(history1.history['loss'], label='Train Loss', linewidth=2)
    plt.plot(history1.history['val_loss'], label='Val Loss', linewidth=2)
    if history2:
        plt.plot([x + len(history1.history['loss']) for x in range(len(history2.history['loss']))], 
                 history2.history['loss'], label='Fine-tune Train Loss', linewidth=2, linestyle='--')
        plt.plot([x + len(history1.history['val_loss']) for x in range(len(history2.history['val_loss']))], 
                 history2.history['val_loss'], label='Fine-tune Val Loss', linewidth=2, linestyle='--')
    plt.title('Model Loss', fontsize=14, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 3)
    if 'top_3_accuracy' in history1.history:
        plt.plot(history1.history['top_3_accuracy'], label='Train Top-3', linewidth=2)
        plt.plot(history1.history['val_top_3_accuracy'], label='Val Top-3', linewidth=2)
        if history2 and 'top_3_accuracy' in history2.history:
            plt.plot([x + len(history1.history['top_3_accuracy']) for x in range(len(history2.history['top_3_accuracy']))], 
                     history2.history['top_3_accuracy'], label='Fine-tune Train Top-3', linewidth=2, linestyle='--')
            plt.plot([x + len(history1.history['val_top_3_accuracy']) for x in range(len(history2.history['val_top_3_accuracy']))], 
                     history2.history['val_top_3_accuracy'], label='Fine-tune Val Top-3', linewidth=2, linestyle='--')
        plt.title('Top-3 Accuracy', fontsize=14, fontweight='bold')
        plt.xlabel('Epoch')
        plt.ylabel('Top-3 Accuracy')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('ml_model/models/training_history.png', dpi=150, bbox_inches='tight')
    print(f"   ✅ Training history saved to ml_model/models/training_history.png")
    
    elapsed_time = time.time() - start_time
    print(f"\n⏱️  Total training time: {elapsed_time/60:.2f} minutes ({elapsed_time/3600:.2f} hours)")
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    return model, history1

if __name__ == "__main__":
    import sys
    
    # Default dataset path
    dataset_path = "dataset"
    
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset path '{dataset_path}' not found!")
        sys.exit(1)
    
    print("\n🚀 Starting optimized training for maximum accuracy...")
    print("This will take some time. Please be patient.\n")
    
    # Train model with optimized settings
    model, history = train_optimized_model(
        dataset_path=dataset_path,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
        fine_tune_epochs=20,
        balance_classes=True  # Balance classes for better accuracy
    )

