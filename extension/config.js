/**
 * JobShield Chrome Extension — API Configuration
 * 
 * Instructions to switch to Production (Render):
 * 1. Deploy the API to Render (see deployment guide).
 * 2. Copy your public HTTPS service URL (e.g. https://jobshield-api.onrender.com).
 * 3. Set ACTIVE_ENV to 'production'.
 * 4. Paste your URL into PRODUCTION_API_URL.
 */

const CONFIG = {
  // Toggle between 'development' (local) and 'production' (Render HTTPS)
  ACTIVE_ENV: 'development',

  // Local development backend endpoint
  DEVELOPMENT_API_URL: 'http://127.0.0.1:8000',

  // Production Render deployment URL (fill in after creating your Render Web Service)
  PRODUCTION_API_URL: 'https://YOUR-APP-NAME.onrender.com',

  // Timeout in milliseconds (45s handles Render free tier cold-start wakeups)
  TIMEOUT_MS: 45000,

  // Returns the active API base URL without trailing slash
  getBaseUrl() {
    const raw = this.ACTIVE_ENV === 'production' 
      ? this.PRODUCTION_API_URL 
      : this.DEVELOPMENT_API_URL;
    return (raw || '').replace(/\/+$/, '');
  },

  // Returns the predict endpoint URL
  getPredictUrl() {
    return `${this.getBaseUrl()}/predict`;
  },

  // Returns the health check endpoint URL
  getHealthUrl() {
    return `${this.getBaseUrl()}/health`;
  }
};

// Export for Node unit testing if in module environment
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
