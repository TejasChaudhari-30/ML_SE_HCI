/**
 * JobShield Chrome Extension — Popup Script
 * Integrates webpage job extraction with FastAPI prediction backend.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- Configuration ---
  const getPredictUrl = () => (typeof CONFIG !== 'undefined' ? CONFIG.getPredictUrl() : 'http://127.0.0.1:8000/predict');
  const getBaseUrl = () => (typeof CONFIG !== 'undefined' ? CONFIG.getBaseUrl() : 'http://127.0.0.1:8000');
  const getTimeoutMs = () => (typeof CONFIG !== 'undefined' ? CONFIG.TIMEOUT_MS : 45000);

  // --- State ---
  let isAnalyzing = false;

  // --- DOM Elements ---
  const themeToggleBtn = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const toggleManualBtn = document.getElementById('toggle-manual');
  const manualSection = document.getElementById('manual-section');
  const jobTextArea = document.getElementById('job-text');
  const charCountSpan = document.getElementById('char-count');
  const btnAnalyzeCurrent = document.getElementById('btn-analyze-current');
  const btnAnalyzeText = document.getElementById('btn-analyze-text') || document.getElementById('btn-prepare-manual');
  const statusCard = document.getElementById('status-card');
  const statusIcon = document.getElementById('status-icon');
  const statusMessage = document.getElementById('status-message');

  // Metadata Display Elements
  const detectedMeta = document.getElementById('detected-meta');
  const detectedTitle = document.getElementById('detected-title');
  const detectedCompany = document.getElementById('detected-company');
  const detectedLocation = document.getElementById('detected-location');
  const rowTitle = document.getElementById('meta-title-row');
  const rowCompany = document.getElementById('meta-company-row');
  const rowLocation = document.getElementById('meta-location-row');

  // Result Elements
  const resultCard = document.getElementById('result-card');
  const resultLabelBadge = document.getElementById('result-label-badge');
  const resultRiskBadge = document.getElementById('result-risk-badge');
  const resultConfScore = document.getElementById('result-conf-score');
  const resultMeterText = document.getElementById('result-meter-text');
  const resultMeterFill = document.getElementById('result-meter-fill');
  const resultExplanationText = document.getElementById('result-explanation-text');
  const resultIndicators = document.getElementById('result-indicators');

  // --- Theme Management ---
  const THEME_STORAGE_KEY = 'jobshield_theme';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'light') {
      themeIcon.textContent = '🌙';
      themeToggleBtn.setAttribute('title', 'Switch to dark mode');
      themeToggleBtn.setAttribute('aria-label', 'Switch to dark mode');
    } else {
      themeIcon.textContent = '☀️';
      themeToggleBtn.setAttribute('title', 'Switch to light mode');
      themeToggleBtn.setAttribute('aria-label', 'Switch to light mode');
    }
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Storage unavailable in restricted context
    }
  }

  let currentTheme = 'dark';
  try {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === 'light' || savedTheme === 'dark') {
      currentTheme = savedTheme;
    }
  } catch {
    currentTheme = 'dark';
  }
  applyTheme(currentTheme);

  themeToggleBtn.addEventListener('click', () => {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(currentTheme);
  });

  // --- Accordion Toggle ---
  function expandManualSection() {
    manualSection.classList.remove('hidden');
    toggleManualBtn.setAttribute('aria-expanded', 'true');
  }

  function toggleManualSection() {
    const isExpanded = toggleManualBtn.getAttribute('aria-expanded') === 'true';
    toggleManualBtn.setAttribute('aria-expanded', String(!isExpanded));
    manualSection.classList.toggle('hidden', isExpanded);
    if (!isExpanded) {
      jobTextArea.focus();
    }
  }

  toggleManualBtn.addEventListener('click', toggleManualSection);

  // --- Character Count ---
  function updateCharCount() {
    const textLength = jobTextArea.value.length;
    charCountSpan.textContent = textLength.toLocaleString();
  }

  jobTextArea.addEventListener('input', updateCharCount);

  // --- Status Card Helper ---
  function updateStatus(type, icon, message, isSpinning = false) {
    statusCard.className = `status-card status-${type}`;
    statusIcon.textContent = icon;
    statusIcon.className = isSpinning ? 'status-icon spin' : 'status-icon';
    statusMessage.textContent = message;
  }

  // --- Clear Stale Results ---
  function clearPreviousResult() {
    if (resultCard) {
      resultCard.classList.add('hidden');
      resultCard.className = 'card result-card hidden';
    }
    if (resultIndicators) {
      resultIndicators.innerHTML = '';
    }
  }

  // --- Check if URL is restricted by Chrome ---
  function isRestrictedUrl(url) {
    if (!url) return true;
    const lower = url.toLowerCase();
    return (
      lower.startsWith('chrome://') ||
      lower.startsWith('chrome-extension://') ||
      lower.startsWith('edge://') ||
      lower.startsWith('about:') ||
      lower.startsWith('view-source:') ||
      lower.includes('chrome.google.com/webstore') ||
      lower.includes('chromewebstore.google.com')
    );
  }

  // --- Format Extraction Method for Display ---
  function formatMethodName(method) {
    switch (method) {
      case 'schema-ldjson':
        return 'Schema.org JobPosting structured data';
      case 'site-greenhouse':
      case 'site-lever':
      case 'site-linkedin':
      case 'site-indeed':
      case 'site-workday':
      case 'site-ashby':
      case 'site-glassdoor':
      case 'site-ziprecruiter':
        return `ATS/Job Board parser (${method.replace('site-', '')})`;
      case 'semantic-markup':
        return 'Semantic HTML / OpenGraph';
      case 'heuristic-fallback':
        return 'Content-density heuristics';
      default:
        return 'Webpage parser';
    }
  }

  // --- Display Real Prediction Results from API ---
  function displayPredictionResult(data) {
    if (!resultCard) return;

    const label = data.label || 'UNCERTAIN';
    const riskLevel = data.risk_level || 'Unknown Risk';
    const confidence = typeof data.confidence === 'number' ? data.confidence : 0;
    const explanation = data.explanation || 'Prediction completed based on text feature weights.';

    // 1. Label and Risk Badges
    resultLabelBadge.textContent = label;
    resultRiskBadge.textContent = riskLevel;

    if (label === 'LIKELY FRAUDULENT') {
      resultLabelBadge.className = 'result-badge badge-fraud';
      resultCard.className = 'card result-card result-fraud';
      resultMeterFill.className = 'conf-meter-fill fill-fraud';
      resultMeterText.textContent = `${confidence.toFixed(1)}% Fraud Risk`;
    } else if (label === 'LIKELY GENUINE') {
      resultLabelBadge.className = 'result-badge badge-genuine';
      resultCard.className = 'card result-card result-genuine';
      resultMeterFill.className = 'conf-meter-fill fill-genuine';
      resultMeterText.textContent = `${confidence.toFixed(1)}% Genuine Signal`;
    } else {
      resultLabelBadge.textContent = 'UNCERTAIN';
      resultLabelBadge.className = 'result-badge badge-uncertain';
      resultCard.className = 'card result-card result-uncertain';
      resultMeterFill.className = 'conf-meter-fill fill-uncertain';
      resultMeterText.textContent = `${confidence.toFixed(1)}% Confidence`;
    }

    // 2. Confidence Score & Meter Fill
    resultConfScore.textContent = `${confidence.toFixed(1)}%`;
    const clampedConf = Math.min(100, Math.max(0, confidence));
    resultMeterFill.style.width = `${clampedConf}%`;

    // 3. Explanation Text
    resultExplanationText.textContent = explanation;

    // 4. Indicator Signals (Keywords)
    resultIndicators.innerHTML = '';

    // Suspicious / Warning indicators
    if (data.warning_indicators && data.warning_indicators.length > 0) {
      const warnGroup = document.createElement('div');
      warnGroup.className = 'indicator-group warning-group';

      const warnHeader = document.createElement('div');
      warnHeader.className = 'indicator-header';
      warnHeader.textContent = '⚠️ Risk Indicator Keywords:';
      warnGroup.appendChild(warnHeader);

      const warnTags = document.createElement('div');
      warnTags.className = 'indicator-tags';
      data.warning_indicators.forEach(item => {
        const tag = document.createElement('span');
        tag.className = 'indicator-tag tag-warning';
        tag.textContent = `${item.word} (${item.strength})`;
        warnTags.appendChild(tag);
      });
      warnGroup.appendChild(warnTags);
      resultIndicators.appendChild(warnGroup);
    }

    // Reassuring indicators
    if (data.reassuring_indicators && data.reassuring_indicators.length > 0) {
      const reassGroup = document.createElement('div');
      reassGroup.className = 'indicator-group reassuring-group';

      const reassHeader = document.createElement('div');
      reassHeader.className = 'indicator-header';
      reassHeader.textContent = '✓ Reassuring Keywords:';
      reassGroup.appendChild(reassHeader);

      const reassTags = document.createElement('div');
      reassTags.className = 'indicator-tags';
      data.reassuring_indicators.forEach(item => {
        const tag = document.createElement('span');
        tag.className = 'indicator-tag tag-reassuring';
        tag.textContent = `${item.word} (${item.strength})`;
        reassTags.appendChild(tag);
      });
      reassGroup.appendChild(reassTags);
      resultIndicators.appendChild(reassGroup);
    }

    // Show result card
    resultCard.classList.remove('hidden');
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Update status card
    updateStatus('success', '🛡️', `Analysis complete: ${label} (${riskLevel}).`);
  }

  // --- Send Prediction Request to FastAPI Backend ---
  async function sendPredictionRequest(text) {
    if (isAnalyzing) return;

    // 1. Client-Side Input Validation
    const cleanInput = (text || '').trim();

    if (cleanInput.length === 0) {
      clearPreviousResult();
      updateStatus('warning', '⚠️', 'Please enter or extract job text before analyzing.');
      expandManualSection();
      jobTextArea.focus();
      return;
    }

    if (cleanInput.length < 30) {
      clearPreviousResult();
      updateStatus(
        'warning',
        '⚠️',
        `Job posting text is too short (${cleanInput.length} chars). Minimum 30 characters required for analysis.`
      );
      expandManualSection();
      jobTextArea.focus();
      return;
    }

    if (cleanInput.length > 50000) {
      clearPreviousResult();
      updateStatus(
        'warning',
        '⚠️',
        'Job posting text exceeds maximum allowed length of 50,000 characters.'
      );
      return;
    }

    // 2. Set Loading State & Clear Previous Result
    const activePredictUrl = getPredictUrl();
    const activeBaseUrl = getBaseUrl();
    const isProd = typeof CONFIG !== 'undefined' && CONFIG.ACTIVE_ENV === 'production';
    const timeoutMs = getTimeoutMs();

    isAnalyzing = true;
    btnAnalyzeCurrent.disabled = true;
    if (btnAnalyzeText) btnAnalyzeText.disabled = true;
    clearPreviousResult();
    updateStatus('info', '🔄', 'Analyzing job posting with JobShield ML model...', true);

    // Warm-up timer for cold-starts on sleeping instances (Render free tier)
    const coldStartTimer = setTimeout(() => {
      if (isAnalyzing) {
        updateStatus(
          'info',
          '🔄',
          'Connecting to JobShield service (cold start on free hosting can take up to 45s)...',
          true
        );
      }
    }, 6000);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(activePredictUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          text: cleanInput,
          telecommuting: 0,
          has_company_logo: 0,
          has_questions: 0,
          has_salary_range: 0
        }),
        signal: controller.signal
      });

      clearTimeout(coldStartTimer);
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errMessage = '';
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            if (Array.isArray(errData.detail)) {
              errMessage = errData.detail.map(e => e.msg || e).join(', ');
            } else {
              errMessage = String(errData.detail);
            }
          }
        } catch {
          // Non-JSON response
        }

        if (response.status === 503) {
          throw new Error('JobShield model is not ready. Please verify server logs.');
        } else if (response.status === 400 || response.status === 422) {
          throw new Error(errMessage || `Validation error (${response.status})`);
        } else {
          throw new Error(errMessage || `Server error (${response.status})`);
        }
      }

      const result = await response.json();
      displayPredictionResult(result);
    } catch (err) {
      clearTimeout(coldStartTimer);
      clearTimeout(timeoutId);
      clearPreviousResult();

      if (err.name === 'AbortError') {
        updateStatus(
          'warning',
          '⚠️',
          `Request timed out after ${Math.round(timeoutMs / 1000)}s. If the service was sleeping, it may still be waking up — please click Analyze once more.`
        );
      } else if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
        const helpText = isProd
          ? `Cannot connect to JobShield API at ${activeBaseUrl}. Please verify the Render service is active and healthy.`
          : `Cannot connect to JobShield API at ${activeBaseUrl}. Please ensure the local server is running (uvicorn api.main:app --port 8000).`;
        updateStatus('warning', '⚠️', helpText);
      } else {
        updateStatus('warning', '⚠️', err.message || 'An error occurred during job analysis.');
      }
    } finally {
      clearTimeout(coldStartTimer);
      clearTimeout(timeoutId);
      isAnalyzing = false;
      btnAnalyzeCurrent.disabled = false;
      if (btnAnalyzeText) btnAnalyzeText.disabled = false;
    }
  }

  // --- Action 1: Extract and Analyze Current Job Webpage ---
  btnAnalyzeCurrent.addEventListener('click', async () => {
    if (isAnalyzing) return;

    btnAnalyzeCurrent.disabled = true;
    clearPreviousResult();
    updateStatus('info', '🔄', 'Reading job posting from current webpage...', true);

    try {
      if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.scripting) {
        throw new Error('Chrome extension APIs not available in this environment.');
      }

      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const activeTab = tabs && tabs[0];

      if (!activeTab || !activeTab.id) {
        throw new Error('Unable to identify active browser tab.');
      }

      if (isRestrictedUrl(activeTab.url)) {
        detectedMeta.classList.add('hidden');
        updateStatus(
          'warning',
          '⚠️',
          'Cannot extract from browser internal or extension pages. Navigate to a job listing webpage or paste the text manually below.'
        );
        expandManualSection();
        btnAnalyzeCurrent.disabled = false;
        return;
      }

      // Inject extraction script
      const injectionResults = await chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        files: ['content.js']
      });

      const extraction = injectionResults && injectionResults[0] && injectionResults[0].result;

      if (!extraction || !extraction.success) {
        detectedMeta.classList.add('hidden');
        updateStatus(
          'warning',
          '⚠️',
          "We couldn't automatically find a job description on this page. Try selecting a supported job listing or paste the job text manually."
        );
        expandManualSection();
        jobTextArea.focus();
        btnAnalyzeCurrent.disabled = false;
        return;
      }

      // Populate metadata
      let hasMeta = false;
      if (extraction.jobTitle) {
        detectedTitle.textContent = extraction.jobTitle;
        rowTitle.classList.remove('hidden');
        hasMeta = true;
      } else {
        rowTitle.classList.add('hidden');
      }

      if (extraction.company) {
        detectedCompany.textContent = extraction.company;
        rowCompany.classList.remove('hidden');
        hasMeta = true;
      } else {
        rowCompany.classList.add('hidden');
      }

      if (extraction.location) {
        detectedLocation.textContent = extraction.location;
        rowLocation.classList.remove('hidden');
        hasMeta = true;
      } else {
        rowLocation.classList.add('hidden');
      }

      if (hasMeta) {
        detectedMeta.classList.remove('hidden');
      } else {
        detectedMeta.classList.add('hidden');
      }

      // Populate textarea and update counter
      const extractedText = extraction.fullText || extraction.description;
      jobTextArea.value = extractedText;
      updateCharCount();

      // Expand review section so user can review the text
      expandManualSection();

      // Run prediction through local API with the extracted text
      btnAnalyzeCurrent.disabled = false; // Re-enabled so sendPredictionRequest can handle lock
      await sendPredictionRequest(extractedText);
    } catch (err) {
      detectedMeta.classList.add('hidden');
      updateStatus(
        'warning',
        '⚠️',
        err.message || "We couldn't automatically find a job description on this page. Try pasting the text manually."
      );
      expandManualSection();
      btnAnalyzeCurrent.disabled = false;
    }
  });

  // --- Action 2: Analyze Text Currently in Review Textarea ---
  if (btnAnalyzeText) {
    btnAnalyzeText.addEventListener('click', () => {
      if (isAnalyzing) return;
      const currentText = jobTextArea.value;
      sendPredictionRequest(currentText);
    });
  }
});
