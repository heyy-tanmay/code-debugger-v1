"""
═════════════════════════════════════════════════════════════════════════════
                       MODEL TRAINER MODULE
                         (The AI Brain)
═════════════════════════════════════════════════════════════════════════════

This module is responsible for:
1. Setting up the neural network model (RobertaForSequenceClassification)
2. Training the model on bug detection data
3. Evaluating performance with metrics (Accuracy, Precision, Recall)
4. Saving the trained model for later use

Libraries Used:
- transformers: Provides pre-trained CodeBERT and training utilities
- torch: PyTorch for neural network operations
- scikit-learn: For calculating evaluation metrics
- numpy: Numerical operations
═════════════════════════════════════════════════════════════════════════════
"""

import os
import torch
import numpy as np
from transformers import RobertaForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging
from tqdm import tqdm  # Progress bar

# Import our custom dataset loader
from dataset_loader import load_and_preprocess_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device selection (GPU if available, otherwise CPU)
# GPU training is MUCH faster, but CPU works fine for small projects
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Using device: {DEVICE}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: MODEL SETUP
# ─────────────────────────────────────────────────────────────────────────────

def create_model():
    """
    Creates a RobertaForSequenceClassification model.
    
    What is RobertaForSequenceClassification?
        - "Roberta" is a code-related BERT variant
        - "ForSequenceClassification" means it outputs 2 classes (buggy or not)
        - Pre-trained on code, so it understands code patterns
    
    Why this model?
        - Already trained on billions of code examples
        - We just "fine-tune" it on our bug detection task
        - Much better than training from scratch
        - Transfer learning: Use knowledge from large pretraining
    
    Returns:
        model: RobertaForSequenceClassification model with 2 output classes
    """
    
    logger.info("Loading pre-trained CodeBERT model...")
    
    # Load CodeBERT and add a classification head
    # The model has 2 output neurons (one for "bug", one for "not bug")
    model = RobertaForSequenceClassification.from_pretrained(
        'microsoft/codebert-base',
        num_labels=2  # Binary classification: 0 = clean, 1 = buggy
    )
    
    # Move model to device (GPU or CPU)
    model.to(DEVICE)
    
    # Show model structure
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"\n✓ Model loaded:")
    logger.info(f"  - Total parameters: {total_params:,.0f}")
    logger.info(f"  - Trainable parameters: {trainable_params:,.0f}")
    
    return model


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: TRAINING SETUP
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(eval_pred):
    """
    Calculate evaluation metrics during training.
    
    Metrics explained:
    - Accuracy: What % of predictions were correct?
    - Precision: Of cases predicted buggy, how many actually had bugs?
    - Recall: Of actual bugs, how many did we detect?
    - F1-Score: Balanced combination of Precision and Recall
    
    Args:
        eval_pred: Predictions and true labels from validation set
    
    Returns:
        Dictionary with all metrics
    """
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    return {
        'accuracy': accuracy_score(labels, predictions),
        'precision': precision_score(labels, predictions, average='weighted', zero_division=0),
        'recall': recall_score(labels, predictions, average='weighted', zero_division=0),
        'f1': f1_score(labels, predictions, average='weighted', zero_division=0),
    }


def train_model(epochs=3, batch_size=16, learning_rate=2e-5):
    """
    Main training function using Hugging Face Trainer API.
    
    Args:
        epochs: How many times to go through entire dataset (typically 3-5)
        batch_size: How many samples to process together
        learning_rate: How much to adjust weights (typical: 2e-5 for fine-tuning)
    
    Training process:
    1. Load and preprocess data
    2. Create model
    3. Set training parameters
    4. Train model
    5. Evaluate on validation set
    6. Save model
    """
    
    print("\n" + "="*80)
    print("TRAINING SEMANTIC BUG DETECTOR")
    print("="*80 + "\n")
    
    # Step 1: Load data
    logger.info("Step 1/5: Loading and preprocessing data...")
    train_loader, val_loader, tokenizer = load_and_preprocess_data(
        batch_size=batch_size
    )
    
    # Convert to HuggingFace datasets (Trainer API expects this format)
    # Extract the underlying dataset objects from DataLoaders
    train_dataset = train_loader.dataset
    val_dataset = val_loader.dataset
    
    # Step 2: Create model
    logger.info("\nStep 2/5: Creating model...")
    model = create_model()
    
    # Step 3: Define training arguments
    logger.info("\nStep 3/5: Setting up training configuration...")
    
    # Create output directory if it doesn't exist
    output_dir = 'training_outputs'
    os.makedirs(output_dir, exist_ok=True)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,                  # How many times through data
        per_device_train_batch_size=batch_size,   # Training batch size
        per_device_eval_batch_size=batch_size,    # Evaluation batch size
        warmup_steps=0,                           # Gradual warmup
        weight_decay=0.01,                        # L2 regularization (prevent overfitting)
        logging_dir='./logs',                     # Where to save logs
        logging_steps=10,                         # Log every N steps
        learning_rate=learning_rate,
        evaluation_strategy="epoch",              # Evaluate after each epoch
        save_strategy="epoch",                    # Save model after each epoch
        load_best_model_at_end=True,              # Load best model at the end
        metric_for_best_model="f1",               # Use F1-score to select best model
    )
    
    # Step 4: Create Trainer and train
    logger.info("\nStep 4/5: Training model...")
    print("\n🔄 Training in progress (this may take a few minutes)...\n")
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,  # Calculate metrics
    )
    
    # Actually train the model
    trainer.train()
    
    # Step 5: Evaluate on validation data
    logger.info("\nStep 5/5: Evaluating on validation set...")
    eval_results = trainer.evaluate()
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE - EVALUATION RESULTS")
    print("="*80)
    print(f"Accuracy:  {eval_results.get('eval_accuracy', 0):.4f}")
    print(f"Precision: {eval_results.get('eval_precision', 0):.4f}")
    print(f"Recall:    {eval_results.get('eval_recall', 0):.4f}")
    print(f"F1-Score:  {eval_results.get('eval_f1', 0):.4f}")
    print("="*80 + "\n")
    
    # Save the final model
    save_path = 'saved_bug_predictor_model'
    logger.info(f"\nSaving model to '{save_path}'...")
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)
    
    logger.info(f"✓ Model successfully saved to: {save_path}/")
    logger.info(f"✓ Files in {save_path}:")
    logger.info("  - pytorch_model.bin (model weights)")
    logger.info("  - config.json (model configuration)")
    logger.info("  - vocab.json (tokenizer)")
    logger.info("  - merges.txt (tokenizer)")
    
    return trainer, eval_results


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: EVALUATION FUNCTION (OPTIONAL DETAILED ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_predictions(trainer, dataset, num_samples=None):
    """
    Detailed evaluation on specific samples.
    
    Useful for:
    - Understanding which bugs the model detects well
    - Identifying failure cases
    - Manual inspection of predictions
    
    Args:
        trainer: Trainer object
        dataset: Dataset to evaluate on
        num_samples: How many samples to analyze (None = all)
    """
    
    # Get predictions
    predictions = trainer.predict(dataset)
    preds = np.argmax(predictions.predictions, axis=1)
    
    # Limit to num_samples if specified
    if num_samples is not None:
        preds = preds[:num_samples]
    
    print("\nDetailed Predictions:")
    print("─" * 80)
    
    correct = 0
    for i, (pred, label) in enumerate(zip(preds, dataset.labels[:len(preds)])):
        status = "✓ CORRECT" if pred == label else "✗ WRONG"
        pred_label = "BUGGY" if pred == 1 else "CLEAN"
        true_label = "BUGGY" if label == 1 else "CLEAN"
        
        print(f"Sample {i+1}: Predicted={pred_label}, Actual={true_label} {status}")
        
        if pred == label:
            correct += 1
    
    accuracy = correct / len(preds) if len(preds) > 0 else 0
    print("─" * 80)
    print(f"Sample Accuracy: {accuracy:.2%}\n")


# ─────────────────────────────────────────────────────────────────────────────
# TESTING (This runs if you execute this file directly)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Training Script Entry Point
    
    To train the model, simply run:
        python model_trainer.py
    
    ⚠️ First time: Will download CodeBERT (~500MB)
    ⏱️ Training time: ~2-5 minutes on CPU, ~30 seconds on GPU
    """
    
    # Train the model
    trainer, results = train_model(
        epochs=3,              # Train for 3 epochs
        batch_size=4,          # Small batch size (use 16 for better results)
        learning_rate=2e-5     # Standard learning rate for fine-tuning
    )
    
    # Optional: Detailed evaluation
    # Uncomment the line below to see detailed predictions on each sample
    # evaluate_predictions(trainer, trainer.eval_dataset, num_samples=5)
    
    print("✓ Training pipeline complete! Model saved to 'saved_bug_predictor_model/'")
    print("✓ Next step: Run 'api_server.py' to start the API server")
