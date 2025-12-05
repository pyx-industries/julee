/**
 * Configuration helpers for the Julee Example UI
 * Provides centralized URL generation for API endpoints and external services
 */

// Environment variables with fallback defaults
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TEMPORAL_WEB_URL =
  import.meta.env.VITE_TEMPORAL_WEB_URL || "http://localhost:8001";

export const configHelpers = {
  /**
   * Get the API documentation URL
   * @returns {string} The URL to the API documentation
   */
  getApiDocsUrl(): string {
    return `${API_BASE_URL}/docs`;
  },

  /**
   * Get the API health check URL
   * @returns {string} The URL to the health endpoint
   */
  getHealthUrl(): string {
    return `${API_BASE_URL}/health`;
  },

  /**
   * Get the Temporal Web UI URL
   * @returns {string} The URL to the Temporal Web UI
   */
  getTemporalWebUrl(): string {
    return TEMPORAL_WEB_URL;
  },

  /**
   * Get the base API URL
   * @returns {string} The base URL for API requests
   */
  getApiBaseUrl(): string {
    return API_BASE_URL;
  },

  /**
   * Get a full API endpoint URL
   * @param {string} endpoint - The endpoint path (with or without leading slash)
   * @returns {string} The full URL to the API endpoint
   */
  getApiUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    return `${API_BASE_URL}${cleanEndpoint}`;
  },
};

// Export individual functions for convenience
export const {
  getApiDocsUrl,
  getHealthUrl,
  getTemporalWebUrl,
  getApiBaseUrl,
  getApiUrl,
} = configHelpers;

// Export configuration constants
export const config = {
  API_BASE_URL,
  TEMPORAL_WEB_URL,
} as const;

export default configHelpers;
