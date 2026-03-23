/**
 * ═════════════════════════════════════════════════════════════════════════════
 * BUGVORTEX AI - FRONTEND JAVASCRIPT
 * Handles UI interactions, API calls, and real-time code analysis
 * ═════════════════════════════════════════════════════════════════════════════
 */

// === Global Variables ===
const API_URL = 'http://localhost:8000';
let analysisHistory = [];

// ═════════════════════════════════════════════════════════════════════════════
// TAB SWITCHING
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Switch between different tabs
 * @param {string} tabName - The tab to switch to
 */
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.nav-item').classList.add('active');

    // Update page title
    const titles = {
        'dashboard': 'DASHBOARD',
        'predictor': 'PREDICTOR',
        'history': 'HISTORY',
        'models': 'MODELS',
        'docs': 'DOCS'
    };
    document.getElementById('page-title').textContent = titles[tabName];
}

// ═════════════════════════════════════════════════════════════════════════════
// CODE ANALYSIS / PREDICTION
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Analyze code for bugs
 */
async function analyzCode() {
    const codeSnippet = document.getElementById('code-input').value.trim();
    const language = document.getElementById('language-select').value;
    const filename = document.getElementById('filename-input').value || 'untitled.c';

    // Validation
    if (!codeSnippet) {
        showError('Please paste some code to analyze');
        return;
    }

    if (codeSnippet.length < 10) {
        showError('Code snippet is too short. Please provide more context.');
        return;
    }

    // Show loading spinner
    document.getElementById('loading-spinner').classList.remove('hidden');
    document.getElementById('prediction-results').classList.add('hidden');

    try {
        // Make API call
        const response = await fetch(`${API_URL}/predict_bug`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code_snippet: codeSnippet,
                language: language,
                filename: filename
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const prediction = await response.json();

        // Display results
        displayPredictionResults(prediction, language, filename);

        // Add to history
        addToHistory(prediction, language, filename);

        // Hide loading spinner
        document.getElementById('loading-spinner').classList.add('hidden');
        document.getElementById('prediction-results').classList.remove('hidden');

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading-spinner').classList.add('hidden');
        showError(`Failed to analyze code: ${error.message}`);
    }
}

/**
 * Display prediction results in the UI
 * @param {Object} prediction - Prediction response from API
 * @param {string} language - Programming language
 * @param {string} filename - Source filename
 */
function displayPredictionResults(prediction, language, filename) {
    const resultCard = document.getElementById('result-card');

    // Determine icon and styling based on bug detection
    const isBuggy = prediction.bug_detected;
    const icon = isBuggy ? '⚠️' : '✅';
    const statusText = isBuggy ? 'BUG DETECTED' : 'CODE APPEARS CLEAN';
    const statusClass = isBuggy ? 'buggy' : 'clean';

    // Format confidence percentage
    const confidencePercent = (prediction.confidence_score * 100).toFixed(1);

    // Create result HTML
    const resultHTML = `
        <div class="result-status">
            <div class="result-icon">${icon}</div>
            <div class="result-header">
                <h4>${statusText}</h4>
                <p class="result-message">
                    ${isBuggy ? 'Potential semantic bug detected in your code.' : 'No semantic bugs detected.'}
                </p>
            </div>
        </div>

        <div class="result-details">
            <div class="detail-item">
                <div class="detail-label">CONFIDENCE SCORE</div>
                <div class="detail-value">${confidencePercent}%</div>
                <div class="probability-bar">
                    <div class="probability-label">
                        <span>0%</span>
                        <span>100%</span>
                    </div>
                    <div class="probability-track">
                        <div class="probability-fill" style="width: ${confidencePercent}%"></div>
                    </div>
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">LIKELY ISSUE</div>
                <div class="detail-value" style="font-size: 14px; color: ${isBuggy ? '#ef4444' : '#10b981'};">
                    ${prediction.likely_issue}
                </div>
            </div>

            <div class="detail-item">
                <div class="detail-label">LANGUAGE</div>
                <div class="detail-value" style="font-size: 16px;">${language}</div>
            </div>

            <div class="detail-item">
                <div class="detail-label">FILENAME</div>
                <div class="detail-value" style="font-size: 14px; word-break: break-all;">${filename}</div>
            </div>
        </div>

        <div class="result-details" style="margin-top: 20px;">
            <div class="detail-item">
                <div class="detail-label">PROBABILITY DISTRIBUTION</div>
                <div style="margin-top: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Clean Code:</span>
                        <strong>${(prediction.probabilities.clean * 100).toFixed(1)}%</strong>
                    </div>
                    <div class="probability-track">
                        <div class="probability-fill" style="width: ${prediction.probabilities.clean * 100}%; background: linear-gradient(90deg, #10b981, #34d399)"></div>
                    </div>
                </div>
                <div style="margin-top: 16px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Buggy Code:</span>
                        <strong>${(prediction.probabilities.buggy * 100).toFixed(1)}%</strong>
                    </div>
                    <div class="probability-track">
                        <div class="probability-fill" style="width: ${prediction.probabilities.buggy * 100}%; background: linear-gradient(90deg, #ef4444, #f87171)"></div>
                    </div>
                </div>
            </div>
        </div>

        <div style="margin-top: 20px; padding: 15px; background-color: rgba(0, 217, 255, 0.1); border: 1px solid #1e3a4c; border-radius: 6px;">
            <p style="font-size: 12px; color: #a0aec0;">
                <strong>Note:</strong> This prediction is based on semantic analysis using CodeBERT. 
                For production code, always perform additional testing and code review.
            </p>
            ${prediction.bug_detected ? `<button onclick="loadLLMContent('${prediction.likely_issue}', document.getElementById('code-input').value)" style="margin-top: 10px; padding: 8px 16px; background: linear-gradient(135deg, #00d9ff, #00a8cc); border: none; border-radius: 4px; color: #0a1929; font-weight: 600; cursor: pointer; font-size: 12px;">🤖 Get AI-Powered Explanation</button>` : ''}
        </div>
    `;

    resultCard.innerHTML = resultHTML;
}

/**
 * Add analysis to history
 * @param {Object} prediction - Prediction response
 * @param {string} language - Programming language
 * @param {string} filename - Source filename
 */
function addToHistory(prediction, language, filename) {
    const historyItem = {
        filename: filename,
        language: language,
        bugDetected: prediction.bug_detected,
        confidence: prediction.confidence_score,
        issue: prediction.likely_issue,
        timestamp: new Date().toLocaleTimeString()
    };

    analysisHistory.unshift(historyItem);

    // Keep only last 20 items
    if (analysisHistory.length > 20) {
        analysisHistory.pop();
    }

    updateHistoryDisplay();
}

/**
 * Update history tab display
 */
function updateHistoryDisplay() {
    const historyList = document.getElementById('history-list');

    if (analysisHistory.length === 0) {
        historyList.innerHTML = '<p class="empty-message">No analyses performed yet.</p>';
        return;
    }

    const historyHTML = analysisHistory.map((item, index) => `
        <div class="history-item">
            <div class="history-info">
                <div class="history-filename">${item.filename}</div>
                <div class="history-timestamp">${item.timestamp} • ${item.language}</div>
            </div>
            <div class="history-result">
                <span class="history-badge ${item.bugDetected ? 'buggy' : 'clean'}">
                    ${item.bugDetected ? '🐛 BUG' : '✅ CLEAN'}
                </span>
                <span style="color: var(--text-secondary); font-size: 12px; margin-left: 10px;">
                    ${(item.confidence * 100).toFixed(0)}%
                </span>
            </div>
        </div>
    `).join('');

    historyList.innerHTML = historyHTML;
}

// ═════════════════════════════════════════════════════════════════════════════
// LLM INTEGRATION (Groq Llama)
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Request bug explanation from Groq LLM
 * @param {string} bugType - Type of bug detected
 * @param {string} codeSnippet - Code containing the bug
 * @returns {Promise<string>} Explanation from LLM
 */
async function getBugExplanation(bugType, codeSnippet) {
    try {
        const response = await fetch(`${API_URL}/explain_bug`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bug_type: bugType,
                code_snippet: codeSnippet,
                context: "Code analysis for bug explanation"
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        return data.explanation || "Could not generate explanation";
    } catch (error) {
        console.error('Error getting explanation:', error);
        return null;
    }
}

/**
 * Request code fix suggestion from Groq LLM
 * @param {string} bugType - Type of bug
 * @param {string} codeSnippet - Buggy code
 * @returns {Promise<string>} Fixed code suggestion
 */
async function getCodeFix(bugType, codeSnippet) {
    try {
        const response = await fetch(`${API_URL}/suggest_fix`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bug_type: bugType,
                code_snippet: codeSnippet
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        return data.suggested_fix || "Could not generate fix";
    } catch (error) {
        console.error('Error getting fix:', error);
        return null;
    }
}

/**
 * Request security analysis from Groq LLM
 * @param {string} codeSnippet - Code to analyze
 * @returns {Promise<string>} Security analysis report
 */
async function getSecurityAnalysis(codeSnippet) {
    try {
        const response = await fetch(`${API_URL}/security_analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code_snippet: codeSnippet,
                language: "C",
                filename: "security_check.c"
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        return data.security_analysis || "Could not perform analysis";
    } catch (error) {
        console.error('Error in security analysis:', error);
        return null;
    }
}

/**
 * Load and display LLM-generated content
 * @param {string} bugType - Bug type
 * @param {string} codeSnippet - Code snippet
 */
async function loadLLMContent(bugType, codeSnippet) {
    const resultCard = document.getElementById('result-card');
    
    // Create loading message
    const loadingMsg = document.createElement('div');
    loadingMsg.style.cssText = `
        margin-top: 20px;
        padding: 15px;
        background-color: rgba(0, 217, 255, 0.1);
        border: 1px solid #1e3a4c;
        border-radius: 6px;
        text-align: center;
        color: #a0aec0;
    `;
    loadingMsg.innerHTML = '<p>🔄 Loading AI-powered explanations...</p>';
    
    resultCard.appendChild(loadingMsg);
    
    try {
        // Get explanation and fix in parallel
        const [explanation, fix] = await Promise.all([
            getBugExplanation(bugType, codeSnippet),
            getCodeFix(bugType, codeSnippet)
        ]);
        
        // Remove loading message
        loadingMsg.remove();
        
        // Create AI content section
        const aiSection = document.createElement('div');
        aiSection.style.cssText = `
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.1), rgba(16, 185, 129, 0.1));
            border: 1px solid #1e3a4c;
            border-radius: 8px;
        `;
        
        let aiHTML = '<div style="margin-bottom: 20px;">';
        aiHTML += '<h5 style="color: #00d9ff; margin-bottom: 10px;">🤖 AI-Powered Analysis (Groq Llama)</h5>';
        
        if (explanation) {
            aiHTML += `
                <div style="margin-bottom: 15px;">
                    <p style="color: #a0aec0; line-height: 1.6; font-size: 13px;">${explanation}</p>
                </div>
            `;
        }
        
        if (fix) {
            aiHTML += `
                <div style="margin-top: 15px;">
                    <p style="color: #10b981; font-weight: 600; margin-bottom: 10px;">💡 Suggested Fix:</p>
                    <pre style="background: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; color: #00d9ff;">${fix}</pre>
                </div>
            `;
        }
        
        aiHTML += '</div>';
        aiSection.innerHTML = aiHTML;
        resultCard.appendChild(aiSection);
        
    } catch (error) {
        loadingMsg.innerHTML = `<p style="color: #ef4444;">Error loading AI analysis: ${error.message}</p>`;
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// ERROR HANDLING
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    // Create temporary error notification
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #ef4444;
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    errorDiv.textContent = '❌ ' + message;
    document.body.appendChild(errorDiv);

    // Remove after 5 seconds
    setTimeout(() => {
        errorDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
}

/**
 * Show success message
 * @param {string} message - Success message to display
 */
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #10b981;
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    successDiv.textContent = '✅ ' + message;
    document.body.appendChild(successDiv);

    setTimeout(() => {
        successDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => successDiv.remove(), 300);
    }, 5000);
}

// ═════════════════════════════════════════════════════════════════════════════
// MODAL FUNCTIONS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Open settings modal
 */
function openSettings() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

/**
 * Close modal
 * @param {string} modalId - ID of modal to close
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

/**
 * Open support
 */
function openSupport() {
    showSuccess('Support contact information will be here');
}

/**
 * Sign out
 */
function signOut() {
    if (confirm('Are you sure you want to sign out?')) {
        // In a real app, this would clear session/tokens
        showSuccess('Signed out successfully');
        // Redirect or refresh could happen here
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// ADD CSS ANIMATIONS
// ═════════════════════════════════════════════════════════════════════════════

// Add animation styles dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// ═════════════════════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═════════════════════════════════════════════════════════════════════════════

document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to analyze code
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const codeInput = document.getElementById('code-input');
        if (codeInput === document.activeElement) {
            analyzCode();
        }
    }

    // Escape to close modals
    if (event.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
    }
});

// ═════════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🐛 BugVortex AI Frontend Initialized');

    // Check API connection
    checkAPIConnection();

    // Add some example code to the textarea for demo
    const defaultCode = `#include <stdio.h>
#include <stdlib.h>

int main() {
    int *ptr = (int*)malloc(sizeof(int) * 10);
    
    // Write to array
    for(int i = 0; i < 100; i++) {
        ptr[i] = i;  // Potential buffer overflow!
    }
    
    free(ptr);
    printf("%d", ptr[0]);  // Use after free!
    
    return 0;
}`;

    document.getElementById('code-input').placeholder = defaultCode;
});

/**
 * Check API connection
 */
async function checkAPIConnection() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();
        console.log('✅ API Connection Successful:', data);
    } catch (error) {
        console.warn('⚠️ API Connection Failed. Make sure the server is running on port 8000');
        console.warn('Run: python api_server.py');
    }
}

// Export functions for global scope
window.switchTab = switchTab;
window.analyzCode = analyzCode;
window.openSettings = openSettings;
window.closeModal = closeModal;
window.openSupport = openSupport;
window.signOut = signOut;
