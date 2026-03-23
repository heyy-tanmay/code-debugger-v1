# 📁 Project Structure & File Guide

## Complete Project Layout

```
code-debugger-v1/
│
├── 📄 README.md                          # Full documentation (30+ pages)
├── 📄 QUICK_START.md                    # 5-minute quickstart guide
├── 📄 PROJECT_STRUCTURE.md              # This file
├── 📄 requirements.txt                  # Python dependencies
│
├── 🔧 Core Python Files
│   ├── dataset_loader.py                # Data handling & preprocessing (~200 lines)
│   ├── model_trainer.py                 # Model training & evaluation (~300 lines)
│   └── api_server.py                    # REST API server (~350 lines)
│
├── ⚙️ Configuration Files
│   ├── .env                             # Environment variables
│   └── .gitignore                       # Git ignore rules
│
├── 🚀 Startup Scripts
│   ├── run.bat                          # Windows quick start
│   └── run.sh                           # Linux/Mac quick start
│
├── 🌐 Frontend (Web Dashboard)
│   └── static/
│       ├── index.html                   # Main UI (~400 lines, 5 tabs)
│       ├── style.css                    # Dark theme styling (~1000 lines)
│       └── script.js                    # Interactive logic (~400 lines)
│
└── 🤖 Generated Folders (Auto-created)
    ├── venv/                            # Virtual environment
    └── saved_bug_predictor_model/       # Trained model
        ├── pytorch_model.bin            # Model weights (~500MB)
        ├── config.json                  # Model configuration
        ├── vocab.json                   # Tokenizer vocabulary
        └── merges.txt                   # Tokenizer merges
```

---

## 📋 File Details

### Core Python Files (Backend)

#### 1. `dataset_loader.py` (~200 lines)
**Purpose:** Data handling and preprocessing

**Key Components:**
```python
create_dummy_dataset()           # Create 10 sample C/Java snippets with labels
CodeBugDataset(Dataset)          # PyTorch dataset class for tokenization
load_and_preprocess_data()       # Main function: create DataLoaders
```

**Dependencies:**
- `pandas` - Data manipulation
- `transformers` - CodeBERT tokenizer
- `torch` - PyTorch tensors

**Output:**
- DataLoaders for training/validation
- CodeBERT tokenizer reference

---

#### 2. `model_trainer.py` (~300 lines)
**Purpose:** AI model training and evaluation

**Key Components:**
```python
create_model()                   # Load CodeBERT + classification head
compute_metrics()                # Calculate Accuracy/Precision/Recall/F1
train_model()                    # Main training loop (3 epochs)
evaluate_predictions()           # Detailed analysis (optional)
```

**Dependencies:**
- `transformers.Trainer` - Training API
- `torch` - Neural network ops
- `scikit-learn` - Metrics calculation

**Output:**
- Trained model → `saved_bug_predictor_model/`
- Model evaluation metrics
- Performance plots (to console)

---

#### 3. `api_server.py` (~350 lines)
**Purpose:** REST API server with inference endpoint

**Key Components:**
```python
ModelManager                     # Singleton for efficient model loading
PredictRequest                   # Request schema (Pydantic)
PredictResponse                  # Response schema (Pydantic)
app = FastAPI()                  # Main application

Endpoints:
  GET  /                         # Serve dashboard HTML
  GET  /status                   # Health check
  POST /predict_bug              # Main inference endpoint
  GET  /metrics                  # Model metadata
```

**Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-dotenv` - Config loading

**Startup:**
```bash
python api_server.py
# Server runs on http://localhost:8000
```

---

### Configuration Files

#### `.env`
**Purpose:** Environment variables (never commit with real secrets)

**Key Variables:**
```
API_PORT=8000                    # Server port
API_KEY=bugvortex-ai-secret-key-2026
MODEL_PATH=saved_bug_predictor_model
DEBUG_MODE=False
```

**Read by:** `api_server.py` (via python-dotenv)

---

#### `.gitignore`
**Purpose:** Prevent committing large/sensitive files

**Ignored:**
```
venv/                            # Virtual environment (~300MB)
saved_bug_predictor_model/       # Model weights (~500MB)
*.log                            # Log files
__pycache__/                     # Python cache
.env                             # Secrets
```

---

### Frontend Files (Web UI)

#### `static/index.html` (~400 lines)
**Purpose:** Main HTML structure - 5 tabs dashboard

**Structure:**
```html
<sidebar>
  - Logo and navigation
  - 5 nav items (Dashboard, Predictor, History, Models, Docs)
  - Support and sign-out buttons
</sidebar>

<main>
  <header>
    - Page title
    - Notifications and settings
  </header>
  
  <tab id="dashboard-tab">
    - System status banner
    - Terminal preview
    - Metrics cards
    - Active deployments
  </tab>
  
  <tab id="predictor-tab">
    - Code language selector
    - Filename input
    - Code textarea (300px height)
    - Analyze button
    - Results display area
  </tab>
  
  <tab id="history-tab">
    - History list (max 20 items)
    - Timestamp and confidence
  </tab>
  
  <tab id="models-tab">
    - Model info card
    - Training config card
    - Performance metrics
  </tab>
  
  <tab id="docs-tab">
    - Usage guide
    - Supported bug types
    - API documentation
    - Resources and links
  </tab>
</main>
```

---

#### `static/style.css` (~1000 lines)
**Purpose:** Dark theme styling (matching BugVortex design)

**Design Elements:**
- **Color Palette:** Deep navy (#0a1929) with cyan accents (#00d9ff)
- **Components:** Cards, buttons, modals, progress bars
- **Responsive:** Mobile-friendly (breakpoints at 1200px, 768px, 480px)
- **Animations:** Pulse animations, slide transitions

**Key Classes:**
```css
/* Sidebar */
.sidebar, .nav-item, .logo-text

/* Dashboard */
.dashboard-hero, .metric-card, .terminal-section
.deployment-card, .status-indicator

/* Predictor */
.code-textarea, .btn-analyze, .result-card
.probability-bar, .loading-spinner

/* General */
.modal, .hidden, .btn-*
```

---

#### `static/script.js` (~400 lines)
**Purpose:** Client-side logic and API interactions

**Key Functions:**
```javascript
switchTab(tabName)               // Switch between 5 tabs
analyzCode()                     # Send code to API
displayPredictionResults()       # Show results in UI
addToHistory()                   # Add to analysis history
updateHistoryDisplay()           # Refresh history view
showError(message)               # Error notifications
showSuccess(message)             # Success notifications
openSettings()                   # Open settings modal
```

**API Calls:**
```javascript
POST /predict_bug
  → Analyze code
  → Get bug prediction
  → Display results

GET /status
  → Check if API is alive
```

**Event Listeners:**
```javascript
switchTab()           - Tab navigation
analyzCode()          - Code analysis
Ctrl+Enter            - Quick analyze
Escape                - Close modals
```

---

### Startup Scripts

#### `run.bat` (Windows)
**Purpose:** Automated setup and launch

**Steps:**
1. Check Python installed
2. Create venv
3. Activate venv
4. Install dependencies
5. Train model (if needed)
6. Start API server

**Usage:**
```bash
Double-click run.bat
```

---

#### `run.sh` (Linux/Mac)
**Purpose:** Automated setup and launch (Unix)

**Steps:** Same as `run.bat`

**Usage:**
```bash
chmod +x run.sh
./run.sh
```

---

### Documentation Files

#### `README.md` (~500 lines)
**Purpose:** Comprehensive documentation

**Sections:**
1. Project overview
2. Architecture diagram
3. Installation & setup
4. How to use (UI + API)
5. Model details & metrics
6. File descriptions
7. Key concepts explained
8. Example predictions
9. Troubleshooting
10. Learning resources
11. Future improvements

**Target:** College students, technical audience

---

#### `QUICK_START.md` (~200 lines)
**Purpose:** Get running in 5 minutes

**Sections:**
1. Super quick start (1 step!)
2. Manual setup (5 step)
3. How to use with screenshots
4. Example code to try
5. Tab explanations
6. Troubleshooting quick tips
7. Presentation guide
8. Checklist

**Target:** Beginners, impatient users

---

#### `requirements.txt`
**Purpose:** Python dependency management

**Groups:**
- Machine Learning (torch, transformers)
- Data (pandas, numpy, scikit-learn)
- Web (fastapi, uvicorn, pydantic)
- Utilities (python-dotenv, tqdm)

**Install:**
```bash
pip install -r requirements.txt
```

---

## 🔄 Data Flow

### Training Data Flow
```
code snippets (clean/buggy)
         ↓
[Tokenizer] → token IDs
         ↓
[PyTorch Dataset] → batches
         ↓
[DataLoader] → epochs
         ↓
[Model] → fine-tuning
         ↓
[Trainer] → evaluation
         ↓
saved_bug_predictor_model/
```

### Inference Data Flow
```
User inputs code in UI
         ↓
[JavaScript] → POST /predict_bug
         ↓
[FastAPI] → parse request
         ↓
[ModelManager] → load model
         ↓
[Tokenizer] → convert to tokens
         ↓
[Model] → forward pass
         ↓
[Softmax] → probabilities
         ↓
[Response] → JSON response
         ↓
[JavaScript] → display results
```

---

## 📦 Dependencies Tree

```
torch (PyTorch)
├── torchvision (optional)
└── torchaudio (optional)

transformers
├── tokenizers
├── safetensors
├── huggingface-hub
└── numpy

fastapi
├── uvicorn
├── pydantic
└── starlette

scikit-learn
├── numpy
└── scipy

pandas
├── numpy
└── python-dateutil

python-dotenv
tqdm
```

---

## 🎯 File Purposes at a Glance

| File | Purpose | Lines | Language |
|------|---------|-------|----------|
| dataset_loader.py | Data handling | 200 | Python |
| model_trainer.py | Model training | 300 | Python |
| api_server.py | REST API | 350 | Python |
| index.html | UI structure | 400 | HTML |
| style.css | Styling | 1000 | CSS |
| script.js | Interactions | 400 | JavaScript |
| requirements.txt | Dependencies | 50+ | Text |
| README.md | Full docs | 500+ | Markdown |
| QUICK_START.md | Quickstart | 200 | Markdown |
| .env | Config | 30 | Text |
| run.bat | Windows startup | 50 | Batch |
| run.sh | Unix startup | 50 | Shell |

---

## 💾 File Size Estimates

| Item | Size | Notes |
|------|------|-------|
| Source code | ~100 KB | All .py, .html, .css, .js |
| Dependencies | ~1.5 GB | Installed via pip |
| CodeBERT model | ~500 MB | Downloaded first time |
| Virtual env | ~500 MB | Python packages |
| Training data | ~1 MB | Dummy dataset (10 samples) |
| **TOTAL** | **~2.5 GB** | First time only |

---

## 🔐 Sensitive Files

**Never commit:**
- `.env` (contains API keys)
- `saved_bug_predictor_model/` (50+ files)
- `venv/` (dependencies)
- `__pycache__/` (Python cache)

**These are in `.gitignore` ✓**

---

## ✅ Setup Checklist

- [ ] All Python files present?
- [ ] All HTML/CSS/JS files present?
- [ ] README.md & QUICK_START.md present?
- [ ] requirements.txt complete?
- [ ] .env template provided?
- [ ] run.bat and run.sh present?
- [ ] .gitignore configured?

**If all ✓, you're ready to run!**

---

## 🚀 Quick Commands Reference

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt

# Training
python dataset_loader.py       # Test data loading
python model_trainer.py        # Train model

# Running
python api_server.py           # Start server

# Testing
curl http://localhost:8000/status
# Opens: http://localhost:8000
```

---

**Total Lines of Code: ~2500+**
**Lines of Comments: ~1500+**
**Documentation: ~100+ pages**

**You're ready to present! 🎉**
