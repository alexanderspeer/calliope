// Calliope Vocabulary App - Main Application Controller
import { showLoading, hideLoading, showToast, apiCall, getSentimentIcon } from './utils.js';

// Import all components
import { setupAddWordEventListeners } from './components/addWord.js';
import { setupDatabaseEventListeners } from './components/viewDatabase.js';
import { setupThesaurusEventListeners } from './components/thesaurus.js';
import { setupPredictionEventListeners } from './components/prediction.js';
import { setupFlashcardsEventListeners } from './components/flashcards.js';
import { setupParagraphAnalyzerEventListeners } from './components/paragraphAnalyzer.js';

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Calliope app initializing...');
    
    // Load initial content
    loadWordOfTheDay();
    loadPartsOfSpeech();
    
    // Setup all event listeners
    setupEventListeners();
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Make navigation functions global for onclick handlers
    setupGlobalNavigation();
    
    // Setup color picker
    setupColorPicker();
    
    // Load saved theme color
    loadThemeColor();
    
    // Setup signature feature
    setupSignatureFeature();
    
    // Load saved signatures
    loadSignatures();
});

// Page Navigation Functions
function openPage(pageName) {
    const overlay = document.getElementById('page-overlay');
    const content = document.getElementById('page-content');
    const pageContainer = document.querySelector('.page-container');
    
    // Remove any previous page-specific classes
    pageContainer.classList.remove('analyzer-container');
    
    // Show loading
    content.innerHTML = '<div class="loading">Loading...</div>';
    overlay.classList.add('active');
    
    // Load page content based on page name
    switch(pageName) {
        case 'add-word':
            loadAddWordPage();
            break;
        case 'database':
            loadDatabasePage();
            break;
        case 'thesaurus':
            loadThesaurusPage();
            break;
        case 'prediction':
            loadPredictionPage();
            break;
        case 'flashcards':
            loadFlashcardsPage();
            break;
        case 'analyzer':
            loadAnalyzerPage();
            break;
        case 'stats':
            loadStatsPage();
            break;
        default:
            content.innerHTML = '<div class="error-message">Page not found</div>';
    }
}

function closePage() {
    const overlay = document.getElementById('page-overlay');
    const pageContainer = document.querySelector('.page-container');
    
    // Remove any page-specific classes
    pageContainer.classList.remove('analyzer-container');
    
    overlay.classList.remove('active');
}

// Make navigation functions available globally
function setupGlobalNavigation() {
    window.openPage = openPage;
    window.closePage = closePage;
    window.downloadDatabaseCsv = downloadDatabaseCsv;
    window.openHelpModal = openHelpModal;
    window.closeHelpModal = closeHelpModal;
    window.openColorModal = openColorModal;
    window.closeColorModal = closeColorModal;
    window.openSignatureModal = openSignatureModal;
    window.closeSignatureModal = closeSignatureModal;
}

// Word of the Day
async function loadWordOfTheDay() {
    try {
        const data = await apiCall('/word-of-the-day');
        displayWordOfTheDay(data.word_data);
    } catch (error) {
        document.getElementById('wotd-card').innerHTML = `
            <div class="wotd-error">
                <p>Unable to load Word of the Day</p>
                <button onclick="loadWordOfTheDay()">Retry</button>
            </div>
        `;
    }
}

function displayWordOfTheDay(wordData) {
    const wotdCard = document.getElementById('wotd-card');
    
    // Add rarity class to the card element
    wotdCard.className = `wotd-card rarity-${wordData.rarity}`;
    
    wotdCard.innerHTML = `
        <div class="wotd-word">${wordData.word}</div>
        <div class="wotd-pos">${wordData.pos}</div>
        <div class="wotd-definition">${wordData.definition}</div>
        <div class="wotd-example">"${wordData.example_sentence}"</div>
        <div class="wotd-badges">
            <span class="badge rarity-${wordData.rarity}">${wordData.rarity.toUpperCase()}</span>
            <span class="badge">${getSentimentIcon(wordData.sentiment)} ${wordData.sentiment}</span>
        </div>
    `;
}

// Page Loading Functions
async function loadAddWordPage() {
    const content = document.getElementById('page-content');
    
    content.innerHTML = `
        <h1>Add New Word</h1>
        <input type="text" id="word-input" placeholder="Enter a word..." maxlength="100">
        <button id="add-word-btn">Add Word</button>
        <div id="add-word-result"></div>
    `;
    
    // Setup event listeners for this page
    setupAddWordEventListeners();
}

async function loadDatabasePage() {
    const content = document.getElementById('page-content');
    
    // Keep loading state while preparing the database interface
    content.innerHTML = '<div class="loading">Loading database...</div>';
    
    // Setup the database interface after a brief moment to allow loading to show
    await setupDatabaseInterface();
}

async function setupDatabaseInterface() {
    const content = document.getElementById('page-content');
    
    // Create the database HTML structure
    const databaseHTML = `
        <h1>Database</h1>
        <div class="database-controls">
            <div class="controls-row">
                <div class="search-container">
                    <input type="search" id="word-search" placeholder="Search words..." autocomplete="off">
                    <div id="autocomplete-results" class="autocomplete-results"></div>
                </div>
                <select id="pos-filter">
                    <option value="">All Parts of Speech</option>
                </select>
                <select id="rarity-filter">
                    <option value="">All Rarities</option>
                    <option value="notty">Common Advanced (Notty)</option>
                    <option value="luke">Less Common (Luke)</option>
                    <option value="alex">Rare/Archaic (Alex)</option>
                </select>
                <select id="sentiment-filter">
                    <option value="">All Sentiments</option>
                    <option value="positive">Positive</option>
                    <option value="negative">Negative</option>
                    <option value="formal">Formal</option>
                </select>
                <button id="reset-filters-btn">Reset</button>
            </div>
        </div>
        <div class="pagination">
            <div class="pagination-controls">
                <button id="prev-btn">Previous</button>
                <span id="page-info">Page 1 of 1</span>
                <button id="next-btn">Next</button>
            </div>
            <div class="pagination-settings">
                <label for="items-per-page">Show:</label>
                <select id="items-per-page">
                    <option value="10">10 per page</option>
                    <option value="20">20 per page</option>
                    <option value="40">40 per page</option>
                    <option value="50">50 per page</option>
                </select>
            </div>
        </div>
        <div id="words-grid"><div class="loading">Loading words...</div></div>
    `;
    
    // Replace loading with interface but keep words-grid in loading state
    content.innerHTML = databaseHTML;
    
    // Setup event listeners using the component (this will trigger the actual data load)
    await setupDatabaseEventListeners();
}

async function loadThesaurusPage() {
    const content = document.getElementById('page-content');
    
    content.innerHTML = `
        <h1>Thesaurus</h1>
        <input type="text" id="thesaurus-input" placeholder="Enter a word to find synonyms...">
        <button id="thesaurus-search-btn">Find Synonyms</button>
        <div id="thesaurus-results" style="display: none;"></div>
    `;
    
    setupThesaurusEventListeners();
}

async function loadPredictionPage() {
    const content = document.getElementById('page-content');
    
    content.innerHTML = `
        <h1>Word Prediction</h1>
        <textarea id="sentence-input" placeholder="Enter a sentence with an underscore (_) where you want word suggestions..."></textarea>
        <div class="prediction-controls">
            <select id="sentiment-filter">
                <option value="">All Sentiments (Optional)</option>
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="neutral">Neutral</option>
                <option value="formal">Formal</option>
            </select>
            <select id="pos-filter">
                <option value="">All Parts of Speech (Optional)</option>
            </select>
            <button id="predict-btn">Predict Words</button>
        </div>
        <div id="prediction-results" style="display: none;"></div>
    `;
    
    // Load POS options for the filter
    await loadPredictionPOSOptions();
    
    setupPredictionEventListeners();
}

async function loadFlashcardsPage() {
    const content = document.getElementById('page-content');
    
    content.innerHTML = `
        <h1>Flashcards</h1>
        <div class="database-controls">
            <div class="controls-row">
                <select id="flashcard-pos-filter">
                    <option value="">All Parts of Speech</option>
                </select>
                <select id="flashcard-rarity-filter">
                    <option value="">All Rarities</option>
                    <option value="notty">Common Advanced (Notty)</option>
                    <option value="luke">Less Common (Luke)</option>
                    <option value="alex">Rare/Archaic (Alex)</option>
                </select>
                <select id="flashcard-sentiment-filter">
                    <option value="">All Sentiments</option>
                    <option value="positive">Positive</option>
                    <option value="negative">Negative</option>
                    <option value="neutral">Neutral</option>
                    <option value="formal">Formal</option>
                </select>
                <select id="flashcard-count-filter">
                    <option value="">All Available</option>
                    <option value="10">Last 10</option>
                    <option value="20">Last 20</option>
                    <option value="30">Last 30</option>
                    <option value="40">Last 40</option>
                    <option value="50">Last 50</option>
                    <option value="100">Last 100</option>
                </select>
                <button id="load-flashcards-btn">Start Practice</button>
                <button id="shuffle-flashcards-btn">Shuffle</button>
            </div>
        </div>
        <div id="flashcard-container">
            <div class="loading">Click "Start Practice" to begin</div>
        </div>
    `;
    
    // Use setTimeout to ensure DOM is ready before attaching event listeners
    setTimeout(() => {
    setupFlashcardsEventListeners();
    }, 0);
}

async function loadAnalyzerPage() {
    const content = document.getElementById('page-content');
    const pageContainer = document.querySelector('.page-container');
    
    // Add analyzer-specific class to page container
    pageContainer.classList.add('analyzer-container');
    
    content.innerHTML = `
        <h1>Paragraph Analyzer</h1>
        <div id="paragraph-input" 
             contenteditable="true" 
             placeholder="Paste your paragraph here..." 
             data-placeholder="Enter your paragraph here to analyze and enhance vocabulary words. The analyzer will identify simple words that can be upgraded with more sophisticated alternatives from your vocabulary database. Click on highlighted words to see enhancement options."></div>
        <button id="analyze-btn">Analyze Paragraph</button>
        <div id="analysis-results" style="display: none;"></div>
    `;
    
    setupParagraphAnalyzerEventListeners();
}

async function loadStatsPage() {
    const content = document.getElementById('page-content');
    
    content.innerHTML = `
        <h1>Database Statistics</h1>
        <div id="stats-content">
            <div class="loading">Loading statistics...</div>
        </div>
    `;
    
    // Always fetch fresh statistics when the page is opened
    await loadStats();
}

// Statistics
async function loadStats() {
    try {
        const data = await apiCall('/stats');
        displayStats(data);
    } catch (error) {
        document.getElementById('stats-content').innerHTML = `
            <div class="error-message">
                <p>Failed to load statistics. Please try again.</p>
            </div>
        `;
    }
}

function displayStats(stats) {
    const statsContent = document.getElementById('stats-content');
    
    statsContent.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">${stats.total_words}</div>
                <div class="stat-label">Total Words</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.words_added_today}</div>
                <div class="stat-label">Added Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.current_streak}</div>
                <div class="stat-label">Current Streak</div>
            </div>
        </div>
        
        <div class="stats-section">
            <h3>Parts of Speech Distribution</h3>
            <div class="pos-stats">
                ${Object.entries(stats.pos_distribution).map(([pos, count]) => `
                    <div class="pos-stat">
                        <span class="pos-name">${pos}</span>
                        <span class="pos-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="stats-section">
            <h3>Rarity Distribution</h3>
            <div class="rarity-stats">
                ${Object.entries(stats.rarity_distribution).map(([rarity, count]) => `
                    <div class="rarity-stat">
                        <span class="rarity-badge rarity-${rarity}">${rarity}</span>
                        <span class="rarity-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="stats-section">
            <h3>Sentiment Distribution</h3>
            <div class="sentiment-stats">
                ${Object.entries(stats.sentiment_distribution).map(([sentiment, count]) => `
                    <div class="sentiment-stat">
                        <span class="sentiment-badge">${getSentimentIcon(sentiment)} ${sentiment}</span>
                        <span class="sentiment-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

async function downloadDatabaseCsv() {
    try {
        showLoading();

        const response = await fetch('/api/export/csv');
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `calliope_words_export_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast('CSV download started.', 'success');
    } catch (error) {
        console.error('CSV export failed:', error);
        showToast('Could not download CSV export. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Load Parts of Speech for filters
async function loadPartsOfSpeech() {
    try {
        const data = await apiCall('/parts-of-speech');
        populateSelectOptions('pos-filter', data.parts_of_speech);
    } catch (error) {
        console.warn('Failed to load parts of speech:', error);
    }
}

// Load Parts of Speech for prediction page
async function loadPredictionPOSOptions() {
    try {
        const data = await apiCall('/parts-of-speech');
        populateSelectOptions('pos-filter', data.parts_of_speech);
    } catch (error) {
        console.warn('Failed to load parts of speech for prediction:', error);
    }
}

function populateSelectOptions(selectId, options) {
    const select = document.getElementById(selectId);
    if (select) {
        select.innerHTML = '<option value="">All</option>';
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option.charAt(0).toUpperCase() + option.slice(1);
            select.appendChild(optionElement);
        });
    }
}

// Setup all event listeners
function setupEventListeners() {
    // Close page when clicking outside content
    document.getElementById('page-overlay').addEventListener('click', function(e) {
        if (e.target === this) {
            closePage();
        }
    });
    
    // Close page with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Check if signature modal is open first
            const signatureModal = document.getElementById('signature-modal');
            if (signatureModal && signatureModal.classList.contains('active')) {
                closeSignatureModal();
                return;
            }
            // Check if color modal is open
            const colorModal = document.getElementById('color-modal');
            if (colorModal && colorModal.classList.contains('active')) {
                closeColorModal();
                return;
            }
            // Check if help modal is open
            const helpModal = document.getElementById('help-modal');
            if (helpModal && helpModal.classList.contains('active')) {
                closeHelpModal();
                return;
            }
            closePage();
        }
    });
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only process shortcuts when not in an input field and no page is open
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || 
            document.getElementById('page-overlay').classList.contains('active')) {
            return;
        }
        
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'a':
                    e.preventDefault();
                    openPage('add-word');
                    break;
                case 'd':
                    e.preventDefault();
                    openPage('database');
                    break;
                case 't':
                    e.preventDefault();
                    openPage('thesaurus');
                    break;
                case 'p':
                    e.preventDefault();
                    openPage('prediction');
                    break;
                case 'f':
                    e.preventDefault();
                    openPage('flashcards');
                    break;
                case 'r':
                    e.preventDefault();
                    openPage('analyzer');
                    break;
                case 's':
                    e.preventDefault();
                    openPage('stats');
                    break;
            }
        }
    });
}

// Help Modal Functions
function openHelpModal() {
    const helpModal = document.getElementById('help-modal');
    if (helpModal) {
        helpModal.classList.add('active');
        // Prevent body scrolling when modal is open
        document.body.style.overflow = 'hidden';
    }
}

function closeHelpModal() {
    const helpModal = document.getElementById('help-modal');
    if (helpModal) {
        helpModal.classList.remove('active');
        // Restore body scrolling
        document.body.style.overflow = '';
    }
}

// Color Picker Modal Functions
function openColorModal() {
    const colorModal = document.getElementById('color-modal');
    if (colorModal) {
        colorModal.classList.add('active');
        // Prevent body scrolling when modal is open
        document.body.style.overflow = 'hidden';
    }
}

function closeColorModal() {
    const colorModal = document.getElementById('color-modal');
    if (colorModal) {
        colorModal.classList.remove('active');
        // Restore body scrolling
        document.body.style.overflow = '';
    }
}

// Color Theme Functions
function applyThemeColor(primaryColor) {
    // Store the selected color in localStorage
    localStorage.setItem('themeColor', primaryColor);
    
    // Generate gradient colors based on the primary color
    const rgb = hexToRgb(primaryColor);
    const colors = generateGradientColors(rgb);
    
    // Apply theme to body background
    const body = document.body;
    body.style.background = `linear-gradient(135deg, ${colors.dark} 0%, ${colors.mediumDark} 25%, ${colors.medium} 50%, ${colors.mediumLight} 75%, ${colors.light} 100%)`;
    
    // Apply accent colors throughout the site
    applyAccentColors(primaryColor, colors);
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(x => {
        const hex = x.toString(16);
        return hex.length === 1 ? "0" + hex : hex;
    }).join("");
}

function generateGradientColors(rgb) {
    if (!rgb) return null;
    
    // Create lighter variations
    const lighten = (r, g, b, factor) => {
        return {
            r: Math.min(255, Math.round(r + (255 - r) * factor)),
            g: Math.min(255, Math.round(g + (255 - g) * factor)),
            b: Math.min(255, Math.round(b + (255 - b) * factor))
        };
    };
    
    // Create darker variations
    const darken = (r, g, b, factor) => {
        return {
            r: Math.max(0, Math.round(r * (1 - factor))),
            g: Math.max(0, Math.round(g * (1 - factor))),
            b: Math.max(0, Math.round(b * (1 - factor)))
        };
    };
    
    const dark = darken(rgb.r, rgb.g, rgb.b, 0.2);
    const mediumDark = darken(rgb.r, rgb.g, rgb.b, 0.1);
    const medium = { r: rgb.r, g: rgb.g, b: rgb.b };
    const mediumLight = lighten(rgb.r, rgb.g, rgb.b, 0.3);
    const light = lighten(rgb.r, rgb.g, rgb.b, 0.5);
    
    return {
        dark: rgbToHex(dark.r, dark.g, dark.b),
        mediumDark: rgbToHex(mediumDark.r, mediumDark.g, mediumDark.b),
        medium: rgbToHex(medium.r, medium.g, medium.b),
        mediumLight: rgbToHex(mediumLight.r, mediumLight.g, mediumLight.b),
        light: rgbToHex(light.r, light.g, light.b)
    };
}

function applyAccentColors(primaryColor, gradientColors) {
    if (!gradientColors) return;
    
    // Create style element to override CSS
    let styleElement = document.getElementById('theme-color-styles');
    if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = 'theme-color-styles';
        document.head.appendChild(styleElement);
    }
    
    // Generate CSS rules to override accent colors
    const css = `
        .help-button,
        .color-button,
        .signature-button {
            background: linear-gradient(135deg, ${gradientColors.dark} 0%, ${gradientColors.mediumDark} 100%) !important;
        }
        
        .help-button:hover,
        .color-button:hover,
        .signature-button:hover {
            background: linear-gradient(135deg, ${gradientColors.mediumDark} 0%, ${gradientColors.medium} 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px ${primaryColor}33 !important;
        }
        
        /* Apply theme to buttons, but exclude color preset buttons and close modal buttons */
        button:not(.color-preset):not(.close-modal) {
            background: linear-gradient(135deg, ${gradientColors.dark} 0%, ${gradientColors.mediumDark} 100%) !important;
            box-shadow: 0 4px 15px ${primaryColor}33 !important;
        }
        
        button:not(.color-preset):not(.close-modal):hover {
            box-shadow: 0 8px 25px ${primaryColor}66 !important;
        }
        
        .wotd-card,
        .nav-card,
        .word-card,
        .page-container,
        .form-container,
        .pagination,
        .stats-grid .stat-card,
        .stats-section {
            border-color: ${gradientColors.dark} !important;
        }
        
        /* Preserve card background gradients - only change border and glow */
        .nav-card:hover,
        .word-card:hover {
            border-color: ${gradientColors.mediumDark} !important;
            background: linear-gradient(135deg, #FAF0E6 0%, #F5F5DC 100%) !important;
        }
        
        /* Ensure rarity card backgrounds maintain their gradients */
        .word-card.rarity-notty,
        .word-card.rarity-luke,
        .word-card.rarity-alex,
        .wotd-card.rarity-notty,
        .wotd-card.rarity-luke,
        .wotd-card.rarity-alex {
            background: linear-gradient(135deg, #F5F5DC 0%, #FAF0E6 100%) !important;
        }
        
        /* Preserve glow effects - they use box-shadow, not background */
        .word-card.rarity-notty:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.2), 0 0 30px rgba(76, 175, 80, 0.6) !important;
        }
        
        .word-card.rarity-luke:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.2), 0 0 30px rgba(33, 150, 243, 0.6) !important;
        }
        
        .word-card.rarity-alex:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.2), 0 0 30px rgba(156, 39, 176, 0.6) !important;
        }
        
        .wotd-card.rarity-notty:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.15), 0 0 30px rgba(76, 175, 80, 0.6) !important;
        }
        
        .wotd-card.rarity-luke:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.15), 0 0 30px rgba(33, 150, 243, 0.6) !important;
        }
        
        .wotd-card.rarity-alex:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.15), 0 0 30px rgba(156, 39, 176, 0.6) !important;
        }
        
        input[type="text"]:focus,
        input[type="search"]:focus,
        textarea:focus,
        select:focus {
            border-color: ${gradientColors.mediumDark} !important;
            box-shadow: 0 0 0 3px ${primaryColor}33 !important;
        }
        
        .word-pos {
            background: linear-gradient(135deg, ${gradientColors.dark} 0%, ${gradientColors.mediumDark} 100%) !important;
            border-color: ${gradientColors.dark} !important;
            box-shadow: 0 2px 8px ${primaryColor}33 !important;
        }
        
        .nav-icon {
            color: ${gradientColors.dark} !important;
            border-color: ${gradientColors.dark} !important;
        }
        
        .menu-btn,
        .close-btn {
            border-color: ${gradientColors.dark} !important;
            background: linear-gradient(135deg, ${gradientColors.dark} 0%, ${gradientColors.mediumDark} 100%) !important;
            color: white !important;
        }
        
        .menu-btn:hover,
        .close-btn:hover {
            background: linear-gradient(135deg, ${gradientColors.mediumDark} 0%, ${gradientColors.medium} 100%) !important;
            color: white !important;
        }
        
        /* Menu dropdown border */
        .menu-dropdown {
            border-color: ${gradientColors.dark} !important;
        }
        
        /* Menu items - gradient background with white text like ellipsis/POS tag */
        .menu-item:not(.delete) {
            background: linear-gradient(135deg, ${gradientColors.dark} 0%, ${gradientColors.mediumDark} 100%) !important;
            color: white !important;
        }
        
        .menu-item:not(.delete):hover {
            background: linear-gradient(135deg, ${gradientColors.mediumDark} 0%, ${gradientColors.medium} 100%) !important;
            color: white !important;
        }
        
        /* Delete menu items - red gradient with white text */
        .menu-item.delete {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
            color: white !important;
        }
        
        .menu-item.delete:hover {
            background: linear-gradient(135deg, #c82333 0%, #bd2130 100%) !important;
            color: white !important;
        }
        
        /* Context menu border */
        .context-menu {
            border-color: ${gradientColors.dark} !important;
        }
        
        /* Context menu items - same gradient background with white text */
        .context-menu-item:not(.delete) {
            background: linear-gradient(135deg, ${gradientColors.dark} 0%, ${gradientColors.mediumDark} 100%) !important;
            color: white !important;
        }
        
        .context-menu-item:not(.delete):hover {
            background: linear-gradient(135deg, ${gradientColors.mediumDark} 0%, ${gradientColors.medium} 100%) !important;
            color: white !important;
        }
        
        .context-menu-item.delete {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
            color: white !important;
        }
        
        .context-menu-item.delete:hover {
            background: linear-gradient(135deg, #c82333 0%, #bd2130 100%) !important;
            color: white !important;
        }
        
        .badge.rarity-notty,
        .rarity-notty {
            background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%) !important;
        }
        
        .badge.rarity-luke,
        .rarity-luke {
            background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%) !important;
        }
        
        .badge.rarity-alex,
        .rarity-alex {
            background: linear-gradient(135deg, #9C27B0 0%, #BA68C8 100%) !important;
        }
    `;
    
    styleElement.textContent = css;
}

// Load saved theme color on page load
function loadThemeColor() {
    const savedColor = localStorage.getItem('themeColor');
    if (savedColor) {
        applyThemeColor(savedColor);
    }
}

// Setup color picker event listeners
function setupColorPicker() {
    // Color preset buttons
    const colorPresets = document.querySelectorAll('.color-preset');
    colorPresets.forEach(preset => {
        preset.addEventListener('click', function() {
            const color = this.getAttribute('data-color');
            applyThemeColor(color);
            closeColorModal();
        });
    });
    
    // Custom color apply button
    const applyCustomBtn = document.getElementById('apply-custom-color');
    if (applyCustomBtn) {
        applyCustomBtn.addEventListener('click', function() {
            const customColorInput = document.getElementById('custom-color-input');
            if (customColorInput && customColorInput.value) {
                applyThemeColor(customColorInput.value);
                closeColorModal();
            }
        });
    }
    
    // Close modal when clicking outside
    const colorModal = document.getElementById('color-modal');
    if (colorModal) {
        colorModal.addEventListener('click', function(e) {
            if (e.target === colorModal) {
                closeColorModal();
            }
        });
    }
}

// Close help modal when clicking outside the modal content
document.addEventListener('DOMContentLoaded', function() {
    const helpModal = document.getElementById('help-modal');
    if (helpModal) {
        helpModal.addEventListener('click', function(e) {
            if (e.target === helpModal) {
                closeHelpModal();
            }
        });
    }
});

// Signature Feature Functions
function openSignatureModal() {
    window.editingSignatureId = null;
    const signatureModal = document.getElementById('signature-modal');
    const modalHeader = signatureModal.querySelector('.modal-header h2');
    const addBtn = document.getElementById('add-signature-btn');
    const updateBtn = document.getElementById('update-signature-btn');
    const deleteBtn = document.getElementById('delete-signature-btn');
    
    if (signatureModal) {
        // Reset to "add" mode
        if (modalHeader) modalHeader.textContent = 'Add Signature';
        if (addBtn) addBtn.style.display = 'block';
        if (updateBtn) updateBtn.style.display = 'none';
        if (deleteBtn) deleteBtn.style.display = 'none';
        
        signatureModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        // Focus on name input
        const nameInput = document.getElementById('signature-name');
        if (nameInput) {
            setTimeout(() => nameInput.focus(), 100);
        }
    }
}

function openEditSignatureModal(id) {
    const signatures = loadSignaturesFromStorage();
    const signature = signatures.find(s => s.id === id);
    if (!signature) return;
    
    window.editingSignatureId = id;
    const signatureModal = document.getElementById('signature-modal');
    const modalHeader = signatureModal.querySelector('.modal-header h2');
    const nameInput = document.getElementById('signature-name');
    const fontSelect = document.getElementById('signature-font');
    const colorInput = document.getElementById('signature-color');
    const colorValue = document.getElementById('signature-color-value');
    const addBtn = document.getElementById('add-signature-btn');
    const updateBtn = document.getElementById('update-signature-btn');
    const deleteBtn = document.getElementById('delete-signature-btn');
    
    if (signatureModal) {
        // Switch to "edit" mode
        if (modalHeader) modalHeader.textContent = 'Edit Signature';
        if (addBtn) addBtn.style.display = 'none';
        if (updateBtn) updateBtn.style.display = 'block';
        if (deleteBtn) deleteBtn.style.display = 'block';
        
        // Populate form with existing values
        if (nameInput) nameInput.value = signature.name;
        if (fontSelect) fontSelect.value = signature.font;
        if (colorInput) {
            colorInput.value = signature.color || '#2F1B14';
        }
        if (colorValue) {
            colorValue.textContent = (signature.color || '#2F1B14').toUpperCase();
        }
        
        updateSignaturePreview();
        
        signatureModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        // Focus on name input
        if (nameInput) {
            setTimeout(() => nameInput.focus(), 100);
        }
    }
}

function closeSignatureModal() {
    const signatureModal = document.getElementById('signature-modal');
    if (signatureModal) {
        signatureModal.classList.remove('active');
        document.body.style.overflow = '';
        // Clear form
        const nameInput = document.getElementById('signature-name');
        const fontSelect = document.getElementById('signature-font');
        const colorInput = document.getElementById('signature-color');
        if (nameInput) nameInput.value = '';
        if (fontSelect) fontSelect.value = 'Inter, sans-serif';
        if (colorInput) {
            colorInput.value = '#2F1B14';
            const colorValue = document.getElementById('signature-color-value');
            if (colorValue) colorValue.textContent = '#2F1B14';
        }
        window.editingSignatureId = null;
        updateSignaturePreview();
    }
}

function setupSignatureFeature() {
    const mainDashboard = document.getElementById('main-dashboard');
    if (!mainDashboard) return;
    
    // Right-click context menu for adding signature
    mainDashboard.addEventListener('contextmenu', function(e) {
        // Check if clicked on an existing signature - don't open modal
        if (e.target.classList.contains('signature-element')) {
            return; // Signatures handle their own clicks
        }
        
        // Check if clicked on interactive elements
        if (e.target.closest('button') || 
            e.target.closest('.nav-card') || 
            e.target.closest('.wotd-card') ||
            e.target.closest('.header')) {
            return; // Don't open signature modal on interactive elements
        }
        
        // Allow right-click on dashboard background
        e.preventDefault();
        const rect = mainDashboard.getBoundingClientRect();
        window.rightClickPosition = { 
            x: e.clientX, 
            y: e.clientY,
            relativeX: e.clientX - rect.left,
            relativeY: e.clientY - rect.top,
            rect: rect
        };
        openSignatureModal();
    });
    
    // Prevent default context menu on signatures (they handle their own clicks)
    document.addEventListener('contextmenu', function(e) {
        if (e.target.classList.contains('signature-element')) {
            e.preventDefault();
        }
    });
    
    // Setup signature form event listeners
    const nameInput = document.getElementById('signature-name');
    const fontSelect = document.getElementById('signature-font');
    const colorInput = document.getElementById('signature-color');
    const addSignatureBtn = document.getElementById('add-signature-btn');
    
    if (nameInput && fontSelect && colorInput) {
        nameInput.addEventListener('input', updateSignaturePreview);
        fontSelect.addEventListener('change', updateSignaturePreview);
        colorInput.addEventListener('input', updateSignaturePreview);
        
        // Update color value display
        colorInput.addEventListener('input', function() {
            const colorValue = document.getElementById('signature-color-value');
            if (colorValue) {
                colorValue.textContent = colorInput.value.toUpperCase();
            }
        });
    }
    
    if (addSignatureBtn) {
        addSignatureBtn.addEventListener('click', addSignature);
    }
    
    const updateSignatureBtn = document.getElementById('update-signature-btn');
    const deleteSignatureBtn = document.getElementById('delete-signature-btn');
    
    if (updateSignatureBtn) {
        updateSignatureBtn.addEventListener('click', updateSignature);
    }
    
    if (deleteSignatureBtn) {
        deleteSignatureBtn.addEventListener('click', function() {
            const editingId = window.editingSignatureId;
            if (editingId) {
                closeSignatureModal();
                promptDeleteSignature(editingId);
            }
        });
    }
    
    // Close signature modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const signatureModal = document.getElementById('signature-modal');
            if (signatureModal && signatureModal.classList.contains('active')) {
                closeSignatureModal();
            }
        }
    });
    
    // Close signature modal when clicking outside
    const signatureModal = document.getElementById('signature-modal');
    if (signatureModal) {
        signatureModal.addEventListener('click', function(e) {
            if (e.target === signatureModal) {
                closeSignatureModal();
            }
        });
    }
}

function updateSignaturePreview() {
    const nameInput = document.getElementById('signature-name');
    const fontSelect = document.getElementById('signature-font');
    const colorInput = document.getElementById('signature-color');
    const preview = document.getElementById('signature-preview-text');
    
    if (!nameInput || !fontSelect || !colorInput || !preview) return;
    
    const name = nameInput.value || 'Your Name';
    const font = fontSelect.value;
    const color = colorInput.value;
    
    preview.textContent = name;
    preview.style.fontFamily = font;
    preview.style.color = color;
}

function addSignature() {
    const nameInput = document.getElementById('signature-name');
    const fontSelect = document.getElementById('signature-font');
    const colorInput = document.getElementById('signature-color');
    
    if (!nameInput || !fontSelect || !colorInput) return;
    
    const name = nameInput.value.trim();
    if (!name) {
        alert('Please enter your name');
        return;
    }
    
    const font = fontSelect.value;
    const color = colorInput.value;
    
    // Get click position or position next to Word of the Day card
    let x = 50;
    let y = 50;
    
    // Try to get the right-click position from the context menu handler
    const signatures = loadSignaturesFromStorage();
    const newId = Date.now().toString();
    
    const mainDashboard = document.getElementById('main-dashboard');
    
    // If we have a recent right-click position, use it relative to the dashboard
    if (mainDashboard && window.rightClickPosition && window.rightClickPosition.relativeX !== undefined) {
        const rect = mainDashboard.getBoundingClientRect();
        x = (window.rightClickPosition.relativeX / rect.width) * 100;
        y = (window.rightClickPosition.relativeY / rect.height) * 100;
        // Clean up
        window.rightClickPosition = null;
    } else {
        // Default: spawn on either side of Word of the Day card
        const wotdCard = document.getElementById('wotd-card');
        if (wotdCard && mainDashboard) {
            const wotdRect = wotdCard.getBoundingClientRect();
            const dashboardRect = mainDashboard.getBoundingClientRect();
            
            // Calculate WotD card position relative to dashboard
            const wotdLeft = ((wotdRect.left - dashboardRect.left) / dashboardRect.width) * 100;
            const wotdRight = ((wotdRect.right - dashboardRect.left) / dashboardRect.width) * 100;
            const wotdTop = ((wotdRect.top - dashboardRect.top) / dashboardRect.height) * 100;
            const wotdCenterY = wotdTop + ((wotdRect.height / dashboardRect.height) * 50);
            
            // Alternate between left and right side
            const existingSignatures = loadSignaturesFromStorage();
            const shouldGoLeft = existingSignatures.length % 2 === 0;
            
            if (shouldGoLeft) {
                // Spawn on the left side of the card
                x = Math.max(5, wotdLeft - 10);
            } else {
                // Spawn on the right side of the card
                x = Math.min(95, wotdRight + 10);
            }
            y = wotdCenterY;
        } else {
            // Fallback to center
            x = 50;
            y = 50;
        }
    }
    
    const signature = {
        id: newId,
        name: name,
        font: font,
        color: color,
        x: Math.max(5, Math.min(95, x)), // Clamp between 5% and 95%
        y: Math.max(5, Math.min(95, y))  // Clamp between 5% and 95%
    };
    
    signatures.push(signature);
    saveSignaturesToStorage(signatures);
    
    renderSignature(signature, true); // Pass true to indicate it's a new signature
    closeSignatureModal();
    
    // Show toast notification
    if (typeof showToast === 'function') {
        showToast('Signature added! Drag to move, right-click to delete.', 'success');
    }
}

function saveSignaturesToStorage(signatures) {
    try {
        localStorage.setItem('calliopeSignatures', JSON.stringify(signatures));
    } catch (error) {
        console.warn('Failed to save signatures:', error);
    }
}

function loadSignaturesFromStorage() {
    try {
        const stored = localStorage.getItem('calliopeSignatures');
        return stored ? JSON.parse(stored) : [];
    } catch (error) {
        console.warn('Failed to load signatures:', error);
        return [];
    }
}

function loadSignatures() {
    const signatures = loadSignaturesFromStorage();
    // Ensure all signatures have a color (for backwards compatibility)
    const updatedSignatures = signatures.map(sig => {
        if (!sig.color) {
            sig.color = '#2F1B14'; // Default color
        }
        return sig;
    });
    
    // Save updated signatures if any were missing colors
    if (updatedSignatures.length !== signatures.length || 
        updatedSignatures.some((sig, idx) => sig.color !== signatures[idx]?.color)) {
        saveSignaturesToStorage(updatedSignatures);
    }
    
    updatedSignatures.forEach(signature => {
        renderSignature(signature);
    });
}

function renderSignature(signature, isNew = false) {
    const mainDashboard = document.getElementById('main-dashboard');
    if (!mainDashboard) return;
    
    // Check if signature already exists
    const existing = document.getElementById(`signature-${signature.id}`);
    if (existing) {
        existing.remove();
    }
    
    const signatureElement = document.createElement('div');
    signatureElement.id = `signature-${signature.id}`;
    signatureElement.className = 'signature-element';
    if (isNew) {
        signatureElement.classList.add('signature-new');
        // Remove the glow class after animation completes (1 second)
        setTimeout(() => {
            signatureElement.classList.remove('signature-new');
        }, 1000);
    }
    signatureElement.textContent = signature.name;
    signatureElement.style.position = 'absolute';
    signatureElement.style.left = `${signature.x}%`;
    signatureElement.style.top = `${signature.y}%`;
    signatureElement.style.fontFamily = signature.font;
    signatureElement.style.color = signature.color || '#2F1B14';
    signatureElement.style.cursor = 'grab';
    signatureElement.style.zIndex = '10';
    signatureElement.setAttribute('data-signature-id', signature.id);
    signatureElement.draggable = false; // We'll handle dragging manually
    
    // Setup drag functionality
    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;
    
    const handleMouseMove = function(e) {
        if (!isDragging) return;
        
        const parentRect = mainDashboard.getBoundingClientRect();
        
        // Calculate the mouse position relative to the parent dashboard
        const mouseX = e.clientX - parentRect.left;
        const mouseY = e.clientY - parentRect.top;
        
        // Subtract the offset to position the element correctly
        const elementX = mouseX - offsetX;
        const elementY = mouseY - offsetY;
        
        // Convert to percentage
        const newXPercent = (elementX / parentRect.width) * 100;
        const newYPercent = (elementY / parentRect.height) * 100;
        
        // Clamp to keep within bounds
        const clampedX = Math.max(0, Math.min(100, newXPercent));
        const clampedY = Math.max(0, Math.min(100, newYPercent));
        
        // Update position immediately using transform for smoother movement
        signatureElement.style.left = `${clampedX}%`;
        signatureElement.style.top = `${clampedY}%`;
    };
    
    const handleMouseUp = function(e) {
        if (!isDragging) return;
        
        isDragging = false;
        signatureElement.style.cursor = 'grab';
        
        // Update position in storage
        const currentLeft = parseFloat(signatureElement.style.left);
        const currentTop = parseFloat(signatureElement.style.top);
        
        const signatures = loadSignaturesFromStorage();
        const sigIndex = signatures.findIndex(s => s.id === signature.id);
        if (sigIndex !== -1) {
            signatures[sigIndex].x = currentLeft;
            signatures[sigIndex].y = currentTop;
            saveSignaturesToStorage(signatures);
        }
        
        // Remove event listeners
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    };
    
    signatureElement.addEventListener('mousedown', function(e) {
        // Right-click for editing
        if (e.button === 2) {
            e.preventDefault();
            e.stopPropagation();
            openEditSignatureModal(signature.id);
            return;
        }
        
        // Only start dragging on left mouse button
        if (e.button !== 0) return;
        
        isDragging = true;
        signatureElement.style.cursor = 'grabbing';
        
        // Get element and parent positions
        const rect = signatureElement.getBoundingClientRect();
        const parentRect = mainDashboard.getBoundingClientRect();
        
        // Calculate offset from click point to element's top-left, relative to parent
        const elementXInParent = rect.left - parentRect.left;
        const elementYInParent = rect.top - parentRect.top;
        const mouseXInParent = e.clientX - parentRect.left;
        const mouseYInParent = e.clientY - parentRect.top;
        
        offsetX = mouseXInParent - elementXInParent;
        offsetY = mouseYInParent - elementYInParent;
        
        // Add event listeners for dragging
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        e.preventDefault();
        e.stopPropagation();
    });
    
    // Prevent context menu on right-click
    signatureElement.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        e.stopPropagation();
    });
    
    mainDashboard.appendChild(signatureElement);
}

function updateSignature() {
    const editingId = window.editingSignatureId;
    if (!editingId) return;
    
    const nameInput = document.getElementById('signature-name');
    const fontSelect = document.getElementById('signature-font');
    const colorInput = document.getElementById('signature-color');
    
    if (!nameInput || !fontSelect || !colorInput) return;
    
    const name = nameInput.value.trim();
    if (!name) {
        alert('Please enter your name');
        return;
    }
    
    const font = fontSelect.value;
    const color = colorInput.value;
    
    const signatures = loadSignaturesFromStorage();
    const sigIndex = signatures.findIndex(s => s.id === editingId);
    
    if (sigIndex !== -1) {
        // Update existing signature
        signatures[sigIndex].name = name;
        signatures[sigIndex].font = font;
        signatures[sigIndex].color = color;
        
        saveSignaturesToStorage(signatures);
        
        // Re-render the signature
        renderSignature(signatures[sigIndex]);
        
        closeSignatureModal();
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast('Signature updated!', 'success');
        }
    }
}

function promptDeleteSignature(id) {
    const signatures = loadSignaturesFromStorage();
    const signature = signatures.find(s => s.id === id);
    if (!signature) return;
    
    const confirmed = confirm(`Delete signature "${signature.name}"?`);
    if (confirmed) {
        deleteSignature(id);
    }
}

function deleteSignature(id) {
    const signatures = loadSignaturesFromStorage();
    const filtered = signatures.filter(s => s.id !== id);
    saveSignaturesToStorage(filtered);
    
    const signatureElement = document.getElementById(`signature-${id}`);
    if (signatureElement) {
        signatureElement.remove();
    }
    
    // Show toast notification
    if (typeof showToast === 'function') {
        showToast('Signature deleted', 'success');
    }
}

// Store right-click position globally for signature placement
window.rightClickPosition = null; 