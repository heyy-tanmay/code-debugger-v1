"""
═════════════════════════════════════════════════════════════════════════════
                        DATASET LOADER MODULE
                      (Data Handling & Preprocessing)
═════════════════════════════════════════════════════════════════════════════

This module is responsible for:
1. Creating/Loading a dummy dataset of C and Java code snippets
2. Tokenizing the code using Microsoft's CodeBERT tokenizer
3. Preparing data for model training

Libraries Used:
- pandas: For data manipulation (creating tables with code snippets)
- transformers: For CodeBERT tokenizer (converts text to numbers)
- torch: PyTorch for creating tensor objects (matrices for neural networks)
═════════════════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
from transformers import RobertaTokenizer
import torch
from torch.utils.data import Dataset, DataLoader
import logging

# Set up logging for debugging and tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: DUMMY DATASET CREATION
# ─────────────────────────────────────────────────────────────────────────────

def create_dummy_dataset():
    """
    Creates a dummy dataset of C and Java code snippets.
    
    Returns:
        pd.DataFrame: DataFrame with columns ['code_snippet', 'is_buggy']
                      - code_snippet: String containing C or Java code
                      - is_buggy: Binary label (0 = clean, 1 = buggy)
    
    Why dummy data?
        During college project development, we don't have access to large bug datasets,
        so we create synthetic examples to demonstrate the model's learning capability.
    """
    
    # ╔═ Clean Code Snippets (is_buggy = 0) ═╗
    clean_code_snippets = [
        # C - Safe array access
        """
        #include <stdio.h>
        int main() {
            int arr[10];
            for(int i = 0; i < 10; i++) {
                arr[i] = i * 2;
            }
            printf("Array value: %d", arr[5]);
            return 0;
        }
        """,
        
        # Java - Proper null checking
        """
        public class SafeCode {
            public void process(Object obj) {
                if (obj != null) {
                    System.out.println(obj.toString());
                }
            }
        }
        """,
        
        # C - Proper memory allocation
        """
        #include <stdlib.h>
        int main() {
            int *ptr = (int*)malloc(sizeof(int) * 10);
            if (ptr != NULL) {
                ptr[0] = 42;
                free(ptr);
            }
            return 0;
        }
        """,
        
        # Java - Safe string handling
        """
        public class StringHandler {
            public int getLength(String s) {
                return s != null ? s.length() : 0;
            }
        }
        """,
        
        # C - Bounds checking
        """
        void copyArray(int *src, int *dst, int size) {
            for(int i = 0; i < size && i < 10; i++) {
                dst[i] = src[i];
            }
        }
        """,
    ]
    
    # ╔═ Buggy Code Snippets (is_buggy = 1) ═╗
    buggy_code_snippets = [
        # C - Buffer overflow / Segmentation Fault
        """
        #include <stdio.h>
        int main() {
            int arr[5];
            for(int i = 0; i < 100; i++) {
                arr[i] = i;
            }
            return 0;
        }
        """,
        
        # Java - Null Pointer Exception
        """
        public class UnsafeCode {
            public void process(String str) {
                int len = str.length();
            }
        }
        """,
        
        # C - Dangling pointer (Use After Free)
        """
        #include <stdlib.h>
        int main() {
            int *ptr = (int*)malloc(sizeof(int));
            free(ptr);
            ptr[0] = 42;
            return 0;
        }
        """,
        
        # Java - Potential NullPointerException
        """
        public class RiskyCode {
            public String getName(User user) {
                return user.getProfile().getName();
            }
        }
        """,
        
        # C - Out of bounds access
        """
        int main() {
            int arr[5] = {1,2,3,4,5};
            printf("%d", arr[10]);
            return 0;
        }
        """,
    ]
    
    # Combine clean and buggy examples
    data = {
        'code_snippet': clean_code_snippets + buggy_code_snippets,
        'is_buggy': [0] * len(clean_code_snippets) + [1] * len(buggy_code_snippets)
    }
    
    # Create DataFrame (think of it as a table with rows and columns)
    df = pd.DataFrame(data)
    logger.info(f"✓ Created dummy dataset with {len(df)} samples")
    logger.info(f"  - Clean samples: {(df['is_buggy'] == 0).sum()}")
    logger.info(f"  - Buggy samples: {(df['is_buggy'] == 1).sum()}")
    
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: CUSTOM PYTORCH DATASET CLASS
# ─────────────────────────────────────────────────────────────────────────────

class CodeBugDataset(Dataset):
    """
    Custom PyTorch Dataset class that converts code snippets → tensors.
    
    What it does:
        - Takes raw code snippets and tokenizes them into numbers
        - Creates attention masks (tells model which tokens are real vs padding)
        - Converts everything into PyTorch tensors (numerical tensors for GPU)
    
    Why we need this:
        Neural networks only understand numbers, not text. CodeBERT tokenizer
        converts code text into numerical IDs that the model can process.
    """
    
    def __init__(self, code_snippets, labels, tokenizer, max_length=512):
        """
        Initialize the dataset.
        
        Args:
            code_snippets: List of code strings
            labels: List of binary labels (0 or 1)
            tokenizer: CodeBERT tokenizer object
            max_length: Maximum sequence length (CodeBERT uses 512)
        """
        self.code_snippets = code_snippets
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        """Returns total number of samples in dataset"""
        return len(self.code_snippets)
    
    def __getitem__(self, idx):
        """
        Get a single sample at index idx.
        
        Process:
        1. Get the code snippet and label
        2. Tokenize the code (convert text to token IDs)
        3. Add attention masks
        4. Pad/truncate to max_length
        5. Return as PyTorch tensors
        """
        code = self.code_snippets[idx]
        label = self.labels[idx]
        
        # Tokenize: Convert text to token IDs
        # The tokenizer splits code into subwords and converts each to a number
        encoding = self.tokenizer(
            code,
            max_length=self.max_length,
            padding='max_length',      # Pad sequences to max_length with zeros
            truncation=True,           # Cut sequences longer than max_length
            return_tensors='pt'        # Return PyTorch tensors
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),           # Token IDs
            'attention_mask': encoding['attention_mask'].squeeze(), # Attention mask
            'label': torch.tensor(label, dtype=torch.long)          # Bug label
        }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: DATA LOADING FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def load_and_preprocess_data(batch_size=16, test_split=0.2):
    """
    Main function to load dummy dataset and create DataLoaders.
    
    Args:
        batch_size: Number of samples to process together (16 is typical)
        test_split: Fraction of data to use for testing (20% = 0.2)
    
    Returns:
        Tuple of (train_loader, val_loader, tokenizer)
        - train_loader: DataLoader for training data
        - val_loader: DataLoader for validation data
        - tokenizer: CodeBERT tokenizer (needed for inference too)
    
    Steps:
    1. Create dummy dataset
    2. Split into train/validation
    3. Tokenize all snippets
    4. Create DataLoaders (batch the data)
    """
    
    # Step 1: Create dataset
    df = create_dummy_dataset()
    
    # Step 2: Split data into training (80%) and validation (20%)
    split_idx = int(len(df) * (1 - test_split))
    train_df = df[:split_idx]
    val_df = df[split_idx:]
    
    logger.info(f"✓ Data split: {len(train_df)} train, {len(val_df)} validation")
    
    # Step 3: Load CodeBERT tokenizer
    # Why CodeBERT? It's specifically trained on code, understands code syntax
    logger.info("Loading CodeBERT tokenizer...")
    tokenizer = RobertaTokenizer.from_pretrained('microsoft/codebert-base')
    
    # Step 4: Create PyTorch datasets
    train_dataset = CodeBugDataset(
        code_snippets=train_df['code_snippet'].tolist(),
        labels=train_df['is_buggy'].tolist(),
        tokenizer=tokenizer
    )
    
    val_dataset = CodeBugDataset(
        code_snippets=val_df['code_snippet'].tolist(),
        labels=val_df['is_buggy'].tolist(),
        tokenizer=tokenizer
    )
    
    # Step 5: Create DataLoaders (wraps datasets for efficient batch processing)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,           # Shuffle training data for better learning
        num_workers=0           # Windows compatibility (set to 0 on Windows)
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,          # Don't shuffle validation data
        num_workers=0
    )
    
    logger.info(f"✓ DataLoaders created (batch_size={batch_size})")
    
    return train_loader, val_loader, tokenizer


# ─────────────────────────────────────────────────────────────────────────────
# TESTING (This runs if you execute this file directly)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING DATASET LOADER")
    print("="*80 + "\n")
    
    # Test the data loading pipeline
    train_loader, val_loader, tokenizer = load_and_preprocess_data(batch_size=4)
    
    print("\n✓ Testing a batch from training data:")
    for batch in train_loader:
        print(f"  - input_ids shape: {batch['input_ids'].shape}")
        print(f"  - attention_mask shape: {batch['attention_mask'].shape}")
        print(f"  - labels shape: {batch['label'].shape}")
        print(f"  - Sample label (bug annotation): {batch['label']}")
        break
    
    print("\n✓ Tokenizer info:")
    print(f"  - Vocab size: {tokenizer.vocab_size}")
    print(f"  - Model max length: {tokenizer.model_max_length}")
