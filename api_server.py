"""
═════════════════════════════════════════════════════════════════════════════
                       API SERVER MODULE
                      (The VS Code Bridge)
═════════════════════════════════════════════════════════════════════════════

This module provides:
1. FastAPI REST API server
2. /predict_bug endpoint for bug detection
3. Real-time inference on C/Java code snippets

Libraries Used:
- fastapi: Framework for building web APIs
- uvicorn: ASGI server to run the API
- pydantic: Data validation for request/response
- transformers & torch: For model inference
- python-dotenv: Load environment variables from .env file
═════════════════════════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import numpy as np
import os
from dotenv import load_dotenv
import logging
from typing import Optional
import json
from datetime import datetime

# Import LLM integration
from llm_integration import GroqLLMManager, get_bug_explanation, get_code_fix

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: CONFIGURATION & SETUP
# ─────────────────────────────────────────────────────────────────────────────

# Device selection (GPU if available, CPU otherwise)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Using device: {DEVICE}")

# Model paths
MODEL_PATH = 'saved_bug_predictor_model'

# API Configuration from .env
API_KEY = os.getenv('API_KEY', 'default-api-key')
API_PORT = int(os.getenv('API_PORT', 8000))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

logger.info(f"API Configuration loaded from .env")
logger.info(f"  - API_KEY: {'✓ Set' if os.getenv('API_KEY') else '✗ Using default'}")
logger.info(f"  - API_PORT: {API_PORT}")
logger.info(f"  - DEBUG_MODE: {DEBUG_MODE}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: MODEL LOADING
# ─────────────────────────────────────────────────────────────────────────────

class ModelManager:
    """
    Singleton class to manage model loading and inference.
    
    Why a class?
    - Load model once, use many times (efficient)
    - Avoid reloading model for every request (slow!)
    - Encapsulates model logic
    """
    
    _instance = None
    model = None
    tokenizer = None
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance
    
    def _load_model(self):
        """Load tokenizer and model from disk"""
        try:
            logger.info(f"\nLoading model from '{MODEL_PATH}'...")
            
            # Check if model exists
            if not os.path.exists(MODEL_PATH):
                logger.warning(f"⚠️  Model not found at '{MODEL_PATH}'")
                logger.warning("SOLUTION: Run 'python model_trainer.py' first")
                raise FileNotFoundError(f"Model directory not found: {MODEL_PATH}")
            
            # Load tokenizer
            self.tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
            logger.info("✓ Tokenizer loaded")
            
            # Load model
            self.model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
            self.model.to(DEVICE)
            self.model.eval()  # Set to evaluation mode (no dropout, etc.)
            logger.info("✓ Model loaded and set to evaluation mode")
            
            # Freeze model weights (no training, only inference)
            for param in self.model.parameters():
                param.requires_grad = False
            logger.info("✓ Model ready for inference\n")
            
        except Exception as e:
            logger.error(f"✗ Error loading model: {e}")
            raise
    
    def predict(self, code_snippet: str) -> dict:
        """
        Run inference on a code snippet.
        
        Args:
            code_snippet: Raw C or Java code as string
        
        Returns:
            Dictionary with prediction, confidence, and bug type
        """
        try:
            # Tokenize the code
            # The tokenizer converts code text into token IDs and attention masks
            inputs = self.tokenizer(
                code_snippet,
                return_tensors='pt',
                max_length=512,
                padding='max_length',
                truncation=True
            )
            
            # Move to device (GPU or CPU)
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            
            # Run model inference (no gradients needed)
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Convert logits to probabilities using softmax
            # This gives us confidence scores between 0 and 1
            probabilities = torch.nn.functional.softmax(logits, dim=1)
            pred_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][pred_class].item()
            
            # Determine bug type based on code patterns
            bug_type = self._identify_bug_type(code_snippet)
            
            return {
                'bug_detected': bool(pred_class),      # True if class 1 (buggy)
                'confidence_score': float(confidence),  # Confidence 0-1
                'likely_issue': bug_type,               # Detected bug type
                'raw_prediction': int(pred_class),
                'probabilities': {
                    'clean': float(probabilities[0][0].item()),
                    'buggy': float(probabilities[0][1].item())
                }
            }
        
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise
    
    def _identify_bug_type(self, code_snippet: str) -> str:
        """
        Identify likely bug type based on code patterns.
        
        This is a simple heuristic analysis. A real system would use
        static analysis tools, symbolic execution, or semantic analysis.
        
        Args:
            code_snippet: Code to analyze
        
        Returns:
            String describing likely bug type
        """
        
        # Normalize code
        code_lower = code_snippet.lower()
        
        # Check for common bug patterns
        bug_patterns = {
            'Null Pointer Exception': ['null', '.', 'npe', 'nullpointerexception'],
            'Buffer Overflow / Segmentation Fault': ['arr[', 'buffer', 'overflow', 'segfault', 'malloc', 'free', 'bounds'],
            'Out of Bounds': ['out of bounds', 'index', 'length'],
            'Use After Free': ['free(', 'malloc', 'dangling'],
            'Memory Leak': ['malloc', 'new', 'free()', 'delete'],
            'Race Condition': ['thread', 'mutex', 'lock', 'synchronized'],
            'SQL Injection': ['sql', 'query', 'execute', 'statement'],
            'Command Injection': ['exec', 'system', 'shell', 'cmd'],
        }
        
        # Check which patterns match
        matched_bugs = []
        for bug_name, patterns in bug_patterns.items():
            if any(pattern in code_lower for pattern in patterns):
                matched_bugs.append(bug_name)
        
        # Return the most likely bug or generic message
        if matched_bugs:
            return matched_bugs[0]  # Return first match
        else:
            return 'Potential semantic issue (Unknown type)'


# Initialize model manager
try:
    model_manager = ModelManager()
except Exception as e:
    logger.warning(f"Model loading failed: {e}")
    model_manager = None


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: PYDANTIC MODELS (Request/Response Schemas)
# ─────────────────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    """
    Request body for /predict_bug endpoint.
    
    Example JSON:
    {
        "code_snippet": "int *ptr = malloc(...); free(ptr); ptr[0] = 5;",
        "language": "C",
        "filename": "main.c"
    }
    """
    code_snippet: str       # The actual code to analyze
    language: Optional[str] = "C"  # Programming language (C, Java, etc)
    filename: Optional[str] = "code.c"  # Source filename (for logging)


class PredictResponse(BaseModel):
    """
    Response body from /predict_bug endpoint.
    
    Example JSON:
    {
        "bug_detected": true,
        "confidence_score": 0.92,
        "likely_issue": "Use After Free",
        "probabilities": {
            "clean": 0.08,
            "buggy": 0.92
        },
        "timestamp": "2024-03-23T10:30:45.123Z"
    }
    """
    bug_detected: bool
    confidence_score: float
    likely_issue: str
    probabilities: dict
    timestamp: str
    language: str
    filename: str


class BugExplanationRequest(BaseModel):
    """Request for bug explanation"""
    bug_type: str
    code_snippet: str
    context: Optional[str] = ""


class BugExplanationResponse(BaseModel):
    """Response with detailed bug explanation"""
    bug_type: str
    explanation: str
    code_fix_suggestion: Optional[str] = None
    timestamp: str


class CodeFixRequest(BaseModel):
    """Request for code fix suggestion"""
    bug_type: str
    code_snippet: str


class AnalysisEnhancedResponse(BaseModel):
    """Enhanced prediction response with LLM explanations"""
    bug_detected: bool
    confidence_score: float
    likely_issue: str
    probabilities: dict
    llm_explanation: Optional[str] = None
    suggested_fix: Optional[str] = None
    security_analysis: Optional[str] = None
    timestamp: str
    language: str
    filename: str


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: FASTAPI APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

# Create FastAPI app
app = FastAPI(
    title="Semantic Bug & Exception Predictor API",
    description="AI-powered bug detection for C and Java code",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows the frontend to make requests from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS)
try:
    if os.path.exists('static'):
        app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    """Serve the main dashboard HTML"""
    try:
        return FileResponse('static/index.html')
    except:
        return {
            "message": "Semantic Bug & Exception Predictor API",
            "version": "1.0.0",
            "endpoints": {
                "POST /predict_bug": "Analyze code for bugs",
                "GET /status": "Check API health",
                "GET /dashboard": "Open web dashboard"
            }
        }


@app.get("/status")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status of API and model
    """
    return {
        "status": "healthy",
        "model_loaded": model_manager is not None,
        "device": str(DEVICE),
        "debug_mode": DEBUG_MODE
    }


@app.post("/predict_bug", response_model=Optional[dict])
async def predict_bug(request: PredictRequest):
    """
    Main endpoint: Predict if code contains bugs.
    
    This endpoint:
    1. Accepts a code snippet
    2. Tokenizes and runs it through CodeBERT
    3. Returns prediction with confidence score and likely bug type
    
    Args:
        request: PredictRequest object with code_snippet
    
    Returns:
        PredictResponse with bug prediction and confidence
    
    Example:
        POST /predict_bug
        {
            "code_snippet": "int *ptr = malloc(...); free(ptr); ptr[0] = 5;"
        }
        
        Response:
        {
            "bug_detected": true,
            "confidence_score": 0.92,
            "likely_issue": "Use After Free"
        }
    """
    
    try:
        # Validate input
        if not request.code_snippet or len(request.code_snippet.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="code_snippet cannot be empty"
            )
        
        # Check if model is loaded
        if model_manager is None:
            raise HTTPException(
                status_code=503,
                detail="Model not available. Please train the model first."
            )
        
        # Log request
        logger.info(f"Prediction request:")
        logger.info(f"  - Language: {request.language}")
        logger.info(f"  - File: {request.filename}")
        logger.info(f"  - Code length: {len(request.code_snippet)} chars")
        
        # Run prediction
        prediction = model_manager.predict(request.code_snippet)
        
        # Log result
        logger.info(f"Prediction complete:")
        logger.info(f"  - Bug detected: {prediction['bug_detected']}")
        logger.info(f"  - Confidence: {prediction['confidence_score']:.2%}")
        logger.info(f"  - Likely issue: {prediction['likely_issue']}")
        
        # Add metadata
        prediction['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        prediction['language'] = request.language
        prediction['filename'] = request.filename
        
        return prediction
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during prediction: {str(e)}"
        )


@app.get("/metrics")
def get_metrics():
    """
    Get statistical metrics about the model and predictions.
    
    Returns:
        Dictionary with model statistics
    """
    return {
        "model": "CodeBERT-base",
        "num_labels": 2,
        "supported_languages": ["C", "Java"],
        "max_code_length": 512,
        "description": "Semantic bug detector for C and Java code",
        "llm_enabled": GroqLLMManager().client is not None,
        "llm_model": "llama-3.3-70b-versatile"
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5B: LLM INTEGRATION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/explain_bug")
async def explain_bug(request: BugExplanationRequest):
    """
    Get detailed explanation of a detected bug using Groq Llama LLM.
    
    Args:
        request: BugExplanationRequest with bug_type and code_snippet
    
    Returns:
        BugExplanationResponse with explanation and fix suggestions
    
    Example:
        POST /explain_bug
        {
            "bug_type": "Buffer Overflow",
            "code_snippet": "int arr[5]; arr[100] = 0;",
            "context": "User trying to write beyond array bounds"
        }
    """
    
    try:
        if not request.bug_type or not request.code_snippet:
            raise HTTPException(
                status_code=400,
                detail="bug_type and code_snippet are required"
            )
        
        # Get explanation from Groq Llama
        llm_manager = GroqLLMManager()
        
        if not llm_manager.client:
            raise HTTPException(
                status_code=503,
                detail="LLM service not available. Check GROQ_API_KEY in .env"
            )
        
        logger.info(f"Requesting explanation for: {request.bug_type}")
        
        explanation = llm_manager.explain_bug(
            request.bug_type,
            request.code_snippet,
            request.context
        )
        
        logger.info("✓ Explanation generated")
        
        return {
            "bug_type": request.bug_type,
            "explanation": explanation,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining bug: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/suggest_fix")
async def suggest_fix(request: CodeFixRequest):
    """
    Get code fix suggestion using Groq Llama LLM.
    
    Args:
        request: CodeFixRequest with bug_type and code_snippet
    
    Returns:
        Suggested fix code
    """
    
    try:
        if not request.bug_type or not request.code_snippet:
            raise HTTPException(
                status_code=400,
                detail="bug_type and code_snippet are required"
            )
        
        llm_manager = GroqLLMManager()
        
        if not llm_manager.client:
            raise HTTPException(
                status_code=503,
                detail="LLM service not available"
            )
        
        logger.info(f"Requesting fix for: {request.bug_type}")
        
        fix_suggestion = llm_manager.suggest_fix(
            request.bug_type,
            request.code_snippet
        )
        
        logger.info("✓ Fix suggestion generated")
        
        return {
            "bug_type": request.bug_type,
            "suggested_fix": fix_suggestion,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting fix: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/security_analysis")
async def security_analysis(request: PredictRequest):
    """
    Perform security analysis on code using Groq Llama.
    
    Args:
        request: Code snippet to analyze
    
    Returns:
        Security analysis report
    """
    
    try:
        if not request.code_snippet:
            raise HTTPException(
                status_code=400,
                detail="code_snippet is required"
            )
        
        llm_manager = GroqLLMManager()
        
        if not llm_manager.client:
            raise HTTPException(
                status_code=503,
                detail="LLM service not available"
            )
        
        logger.info("Performing security analysis...")
        
        analysis = llm_manager.analyze_security(request.code_snippet)
        
        logger.info("✓ Security analysis complete")
        
        return {
            "language": request.language,
            "filename": request.filename,
            "security_analysis": analysis,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in security analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: STARTUP & SHUTDOWN EVENTS
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Run on API server startup"""
    logger.info("\n" + "="*80)
    logger.info("STARTING SEMANTIC BUG DETECTOR API")
    logger.info("="*80)
    logger.info(f"✓ Server running on http://localhost:{API_PORT}")
    logger.info(f"✓ Dashboard: http://localhost:{API_PORT}")
    logger.info("="*80 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on API server shutdown"""
    logger.info("\n✓ API server shutting down...")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: TESTING (Run with uvicorn)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run the API server.
    
    Command:
        python api_server.py
    
    Access:
        - API: http://localhost:8000
        - Dashboard: http://localhost:8000
        - Docs (Swagger): http://localhost:8000/docs
    """
    
    import uvicorn
    
    print("\n" + "="*80)
    print("STARTING SEMANTIC BUG DETECTOR API SERVER")
    print("="*80)
    print(f"Environment: {'DEBUG' if DEBUG_MODE else 'PRODUCTION'}")
    print(f"Port: {API_PORT}")
    print(f"Device: {DEVICE}")
    print("\nAccess points:")
    print(f"  - Dashboard: http://localhost:{API_PORT}")
    print(f"  - API Docs: http://localhost:{API_PORT}/docs")
    print("="*80 + "\n")
    
    # Run server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=DEBUG_MODE,
        log_level="info"
    )
