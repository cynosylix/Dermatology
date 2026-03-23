"""
Improved Training script for Skin Disease Classification Model
Uses EfficientNetB4 with better data augmentation and training strategies
"""
import os
import json
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB4
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from pathlib import Path
import time

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def load_dataset_optimized(dataset_path, img_size=(380, 380), max_samples_per_class=None):
    """
    Load images from dataset directory with optimization
    
    Args:
        dataset_path: Path to dataset directory
        img_size: Target image size (larger for better accuracy)
        max_samples_per_class: Limit samples per class for faster training (None = all)
    
    Returns:
        X: Image arrays
        y: Labels
        class_names: List of class names
    """
    X = []
    y = []
    
    # Get all class directories
    class_dirs = [d for d in os.listdir(dataset_path) 
                  if os.path.isdir(os.path.join(dataset_path, d))]
    class_dirs.sort()
    
    class_to_idx = {class_name: idx for idx, class_name in enumerate(class_dirs)}
    
    print(f"Found {len(class_dirs)} classes: {class_dirs}")
    print(f"Loading images with size {img_size}...")
    
    total_images = 0
    # Load images
    for class_name in class_dirs:
        class_path = os.path.join(dataset_path, class_name)
        image_files = [f for f in os.listdir(class_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Limit samples if specified
        if max_samples_per_class and len(image_files) > max_samples_per_class:
            import random
            random.shuffle(image_files)
            image_files = image_files[:max_samples_per_class]
        
        print(f"Loading {len(image_files)} images from {class_name}...")
        
        for img_file in image_files:
            try:
                img_path = os.path.join(class_path, img_file)
                img = Image.open(img_path)
                
                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize with high quality
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
    
    print(f"\nTotal images loaded: {total_images}")
    print(f"Image shape: {X[0].shape}")
    print(f"Number of classes: {len(class_dirs)}")
    
    # Save class indices
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    
    return X, y, class_dirs, class_to_idx, idx_to_class

def create_improved_model(num_classes, img_size=(380, 380)):
    """
    Create an improved model using EfficientNetB4 with better architecture
    
    Args:
        num_classes: Number of disease classes
        img_size: Input image size
    
    Returns:
        Compiled model
    """
    # Use EfficientNetB4 as base model (better than B3)
    base_model = EfficientNetB4(
        weights='imagenet',
        include_top=False,
        input_shape=(img_size[0], img_size[1], 3)
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Build improved model
    inputs = keras.Input(shape=(img_size[0], img_size[1], 3))
    
    # Data augmentation layers
    x = layers.RandomRotation(0.15)(inputs)
    x = layers.RandomFlip("horizontal")(x)
    x = layers.RandomZoom(0.1)(x)
    x = layers.RandomBrightness(0.1)(x)
    x = layers.RandomContrast(0.1)(x)
    
    # Preprocessing for EfficientNet
    x = keras.applications.efficientnet.preprocess_input(x)
    
    # Base model
    x = base_model(x, training=False)
    
    # Better feature extraction
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    
    # Dense layers with better regularization
    x = layers.Dense(1024, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    
    # Output layer
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = models.Model(inputs, outputs)
    
    # Compile model with better optimizer settings
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy', 'top_3_accuracy']
    )
    
    return model, base_model

def train_improved_model(dataset_path, epochs=50, batch_size=16, validation_split=0.2, 
                         fine_tune_epochs=15, max_samples_per_class=None):
    """
    Train the improved skin disease classification model
    
    Args:
        dataset_path: Path to dataset directory
        epochs: Number of training epochs
        batch_size: Batch size for training (smaller for larger images)
        validation_split: Fraction of data to use for validation
        fine_tune_epochs: Number of epochs for fine-tuning
        max_samples_per_class: Limit samples per class (None = all, use for faster training)
    """
    print("=" * 70)
    print("Improved Skin Disease Classification Model Training")
    print("=" * 70)
    
    start_time = time.time()
    
    # Load dataset with larger image size for better accuracy
    print("\n1. Loading dataset...")
    img_size = (380, 380)  # Larger size for better accuracy
    X, y, class_names, class_to_idx, idx_to_class = load_dataset_optimized(
        dataset_path, img_size=img_size, max_samples_per_class=max_samples_per_class
    )
    num_classes = len(class_names)
    
    # Split dataset
    print("\n2. Splitting dataset...")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=validation_split, random_state=42, stratify=y
    )
    
    print(f"  - Training samples: {len(X_train)}")
    print(f"  - Validation samples: {len(X_val)}")
    
    # Create model
    print("\n3. Creating improved model with EfficientNetB4...")
    model, base_model = create_improved_model(num_classes, img_size=img_size)
    
    print(f"  - Model created with {model.count_params():,} parameters")
    print(f"  - Using EfficientNetB4 transfer learning")
    
    # Enhanced data augmentation
    datagen = ImageDataGenerator(
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.3,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        fill_mode='nearest'
    )
    
    # Callbacks
    callbacks = [
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
            min_lr=1e-7,
            verbose=1,
            mode='min'
        ),
        keras.callbacks.ModelCheckpoint(
            'ml_model/models/best_model_improved.h5',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1,
            mode='max'
        )
    ]
    
    # Phase 1: Train with frozen base model
    print("\n4. Phase 1: Training with frozen base model...")
    print(f"  - Epochs: {epochs}")
    print(f"  - Batch size: {batch_size}")
    
    history1 = model.fit(
        datagen.flow(X_train, y_train, batch_size=batch_size),
        steps_per_epoch=len(X_train) // batch_size,
        epochs=epochs,
        validation_data=(X_val, y_val),
        callbacks=callbacks,
        verbose=1
    )
    
    # Phase 2: Fine-tuning
    if fine_tune_epochs > 0:
        print("\n5. Phase 2: Fine-tuning (unfreezing base model)...")
        base_model.trainable = True
        
        # Fine-tune from this layer onwards (unfreeze last 50 layers)
        fine_tune_at = len(base_model.layers) - 50
        
        for layer in base_model.layers[:fine_tune_at]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001, beta_1=0.9, beta_2=0.999),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy', 'top_3_accuracy']
        )
        
        print(f"  - Fine-tuning last {len(base_model.layers) - fine_tune_at} layers")
        print(f"  - Epochs: {fine_tune_epochs}")
        
        history2 = model.fit(
            datagen.flow(X_train, y_train, batch_size=batch_size),
            steps_per_epoch=len(X_train) // batch_size,
            epochs=fine_tune_epochs,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=1
        )
    else:
        history2 = None
    
    # Save model
    print("\n6. Saving model...")
    model_path = 'ml_model/models/skin_disease_model.h5'
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"  - Model saved to {model_path}")
    
    # Save class indices
    indices_path = 'ml_model/models/class_indices.json'
    with open(indices_path, 'w') as f:
        json.dump(class_to_idx, f, indent=2)
    print(f"  - Class indices saved to {indices_path}")
    
    # Evaluate model
    print("\n7. Evaluating model...")
    test_loss, test_accuracy, test_top3 = model.evaluate(X_val, y_val, verbose=0)
    print(f"  - Validation Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    if test_top3:
        print(f"  - Validation Top-3 Accuracy: {test_top3:.4f} ({test_top3*100:.2f}%)")
    
    # Plot training history
    print("\n8. Saving training history...")
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.plot(history1.history['accuracy'], label='Train Accuracy', linewidth=2)
    plt.plot(history1.history['val_accuracy'], label='Val Accuracy', linewidth=2)
    if history2:
        plt.plot([x + len(history1.history['accuracy']) for x in range(len(history2.history['accuracy']))], 
                 history2.history['accuracy'], label='Fine-tune Train Acc', linewidth=2, linestyle='--')
        plt.plot([x + len(history1.history['val_accuracy']) for x in range(len(history2.history['val_accuracy']))], 
                 history2.history['val_accuracy'], label='Fine-tune Val Acc', linewidth=2, linestyle='--')
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
    print(f"  - Training history saved to ml_model/models/training_history.png")
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal training time: {elapsed_time/60:.2f} minutes")
    
    print("\n" + "=" * 70)
    print("Training completed successfully!")
    print("=" * 70)
    
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
    
    # Train model with improved settings
    # Note: This will take longer but should give much better accuracy
    model, history = train_improved_model(
        dataset_path=dataset_path,
        epochs=40,  # Reduced for faster training, increase for better results
        batch_size=16,  # Smaller batch for larger images
        validation_split=0.2,
        use_transfer_learning=True,
        fine_tune_epochs=15,
        max_samples_per_class=None  # Set to a number (e.g., 1000) for faster training
    )

