"""
ML Model Prediction Utility for Skin Disease Classification
"""
import os
import json
import numpy as np
from PIL import Image, ImageOps
from django.conf import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load model and class indices once when first used (TensorFlow loads only then)
_model = None
_class_indices = None
_tf = None


def _ensure_tf():
    """Import TensorFlow on first use so Django management commands avoid loading it."""
    global _tf
    if _tf is None:
        import tensorflow as tf

        _tf = tf
    return _tf


def load_model():
    """Load the trained model and class indices"""
    global _model, _class_indices

    tf_mod = _ensure_tf()
    keras = tf_mod.keras

    if _model is None:
        model_path = os.path.join(settings.BASE_DIR, 'ml_model', 'models', 'skin_disease_model.h5')
        if os.path.exists(model_path):
            try:
                # Try loading with compile first (for newer models)
                try:
                    _model = keras.models.load_model(model_path)
                    logger.info(f"Model loaded successfully with compilation from {model_path}")
                except Exception:
                    # If that fails, load without compilation
                    _model = keras.models.load_model(model_path, compile=False)
                    logger.info(f"Model loaded successfully without compilation from {model_path}")
                
                # Get model summary for debugging
                logger.info(f"Model input shape: {_model.input_shape}")
                logger.info(f"Model output shape: {_model.output_shape}")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise FileNotFoundError(f"Error loading model: {str(e)}")
        else:
            raise FileNotFoundError(f"Model file not found at {model_path}")
    
    if _class_indices is None:
        indices_path = os.path.join(settings.BASE_DIR, 'ml_model', 'models', 'class_indices.json')
        if os.path.exists(indices_path):
            with open(indices_path, 'r') as f:
                _class_indices = json.load(f)
            # Reverse the dictionary to get index -> class name mapping
            _class_indices = {v: k for k, v in _class_indices.items()}
            logger.info(f"Class indices loaded: {len(_class_indices)} classes")
        else:
            raise FileNotFoundError(f"Class indices file not found at {indices_path}")
    
    return _model, _class_indices

def preprocess_image(image_path, target_size=(224, 224), use_imagenet_norm=False, augment=False):
    """
    Preprocess image for model prediction with improved preprocessing
    
    Args:
        image_path: Path to the image file
        target_size: Target size for resizing (default: 224x224)
        use_imagenet_norm: Whether to use ImageNet normalization (default: False)
        augment: Whether to apply test-time augmentation (default: False)
    
    Returns:
        Preprocessed image array ready for model prediction
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Auto-orient image based on EXIF data
        img = ImageOps.exif_transpose(img)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Apply augmentation if requested (for test-time augmentation)
        if augment:
            # Random horizontal flip (50% chance)
            import random
            if random.random() > 0.5:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
        
        # Resize image with high-quality resampling
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to array
        img_array = np.array(img, dtype=np.float32)
        
        # Normalize based on method
        if use_imagenet_norm:
            # ImageNet normalization (for models trained on ImageNet)
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img_array = img_array / 255.0
            img_array = (img_array - mean) / std
        else:
            # Simple normalization to [0, 1]
            img_array = img_array / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        raise ValueError(f"Error preprocessing image: {str(e)}")

def predict_skin_disease(image_path, top_n=3, use_imagenet_norm=False, try_both_norms=False, use_tta=True):
    """
    Predict skin disease from an image with improved prediction logic and test-time augmentation
    
    Args:
        image_path: Path to the image file
        top_n: Number of top predictions to return (default: 3)
        use_imagenet_norm: Whether to use ImageNet normalization (default: False)
        try_both_norms: If True, try both normalization methods and return best result
        use_tta: If True, use test-time augmentation for more robust predictions (default: True)
    
    Returns:
        Dictionary with predictions and confidence scores
    """
    try:
        # Load model and class indices
        model, class_indices = load_model()
        
        all_predictions = []
        
        # Try both normalization methods if requested
        if try_both_norms:
            norm_methods = [False, True]
        else:
            norm_methods = [use_imagenet_norm]
        
        # Collect predictions from different preprocessing methods
        for use_imagenet in norm_methods:
            try:
                # Test-time augmentation: make multiple predictions with different augmentations
                if use_tta:
                    tta_predictions = []
                    # Original image
                    processed_image = preprocess_image(image_path, use_imagenet_norm=use_imagenet, augment=False)
                    pred = model.predict(processed_image, verbose=0)
                    tta_predictions.append(pred)
                    
                    # Horizontally flipped
                    processed_image = preprocess_image(image_path, use_imagenet_norm=use_imagenet, augment=True)
                    pred = model.predict(processed_image, verbose=0)
                    tta_predictions.append(pred)
                    
                    # Average the predictions for robustness
                    predictions = np.mean(tta_predictions, axis=0)
                    logger.info("Using test-time augmentation for more robust predictions")
                else:
                    processed_image = preprocess_image(image_path, use_imagenet_norm=use_imagenet)
                    predictions = model.predict(processed_image, verbose=0)
                
                # Apply softmax if needed
                pred_sum = np.sum(predictions[0])
                if pred_sum < 0.99 or pred_sum > 1.01:
                    predictions = _ensure_tf().nn.softmax(predictions, axis=-1).numpy()
                
                all_predictions.append(predictions)
            except Exception as e:
                logger.warning(f"Error with normalization method (ImageNet={use_imagenet}): {str(e)}")
                continue
        
        # Use the best prediction (highest max confidence)
        if all_predictions:
            best_pred = None
            best_confidence = 0
            for pred in all_predictions:
                max_conf = float(np.max(pred[0])) * 100
                if max_conf > best_confidence:
                    best_confidence = max_conf
                    best_pred = pred
            
            # If multiple predictions, average them for ensemble effect
            if len(all_predictions) > 1:
                predictions = np.mean(all_predictions, axis=0)
                logger.info(f"Ensembled {len(all_predictions)} predictions")
            else:
                predictions = best_pred if best_pred is not None else all_predictions[0]
        else:
            # Fallback to default
            processed_image = preprocess_image(image_path, use_imagenet_norm=use_imagenet_norm)
            predictions = model.predict(processed_image, verbose=0)
            pred_sum = np.sum(predictions[0])
            if pred_sum < 0.99 or pred_sum > 1.01:
                predictions = _ensure_tf().nn.softmax(predictions, axis=-1).numpy()
        
        # Get top N predictions
        top_indices = np.argsort(predictions[0])[-top_n:][::-1]
        
        results = []
        for idx in top_indices:
            disease_name = class_indices.get(int(idx), f"Class {idx}")
            confidence = float(predictions[0][idx]) * 100
            
            # Only include predictions with confidence > 1%
            if confidence > 1.0:
                results.append({
                    'disease': disease_name,
                    'confidence': round(confidence, 2)
                })
        
        # If no results with >1% confidence, still return top prediction
        if not results and len(top_indices) > 0:
            idx = top_indices[0]
            disease_name = class_indices.get(int(idx), f"Class {idx}")
            confidence = float(predictions[0][idx]) * 100
            results.append({
                'disease': disease_name,
                'confidence': round(confidence, 2)
            })
        
        # Sort results by confidence (descending)
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'success': True,
            'predictions': results[:top_n],
            'top_prediction': results[0] if results else None
        }
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'predictions': []
        }






 