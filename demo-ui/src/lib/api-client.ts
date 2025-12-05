/**
 * API Client for Julee Example UI
 * Provides centralized HTTP client configuration and error handling utilities
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";

// Get base URL from environment or fallback to localhost
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Create axios instance with default configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

/**
 * Request interceptor to add common headers or auth tokens
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add any common request modifications here
    // For example, adding auth tokens:
    // const token = localStorage.getItem('authToken');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

/**
 * Response interceptor for common error handling
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Log errors in development
    if (import.meta.env.DEV) {
      console.error("API Error:", error);
    }

    // Handle common HTTP errors
    if (error.response) {
      // Server responded with error status
      const { status } = error.response;

      switch (status) {
        case 401:
          // Handle unauthorized - could redirect to login
          console.warn("Unauthorized request");
          break;
        case 403:
          // Handle forbidden
          console.warn("Forbidden request");
          break;
        case 404:
          // Handle not found
          console.warn("Resource not found");
          break;
        case 500:
          // Handle server error
          console.error("Internal server error");
          break;
        default:
          console.error(`HTTP Error ${status}`);
      }
    } else if (error.request) {
      // Network error
      console.error("Network error:", error.message);
    } else {
      // Something else happened
      console.error("Request error:", error.message);
    }

    return Promise.reject(error);
  },
);

/**
 * Extract error message from API error response
 * @param error - The error object from a failed API request
 * @returns A user-friendly error message string
 */
export function getApiErrorMessage(error: unknown): string {
  if (!error) {
    return "An unknown error occurred";
  }

  // Handle AxiosError specifically
  if (axios.isAxiosError(error)) {
    // Check if there's a response with error details
    if (error.response?.data) {
      const { data } = error.response;

      // Handle FastAPI validation errors
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          // Validation errors are usually arrays
          return data.detail
            .map((item: any) => {
              if (typeof item === "string") return item;
              if (item.msg)
                return `${item.loc?.join(".") || "Field"}: ${item.msg}`;
              return JSON.stringify(item);
            })
            .join(", ");
        } else if (typeof data.detail === "string") {
          return data.detail;
        }
      }

      // Handle other error formats
      if (data.message) {
        return data.message;
      }

      if (data.error) {
        return data.error;
      }
    }

    // Handle HTTP status errors
    if (error.response?.status) {
      const status = error.response.status;
      switch (status) {
        case 400:
          return "Bad request - please check your input";
        case 401:
          return "Unauthorized - please log in again";
        case 403:
          return "Forbidden - you do not have permission to perform this action";
        case 404:
          return "Resource not found";
        case 422:
          return "Validation error - please check your input";
        case 429:
          return "Too many requests - please try again later";
        case 500:
          return "Internal server error - please try again later";
        case 502:
          return "Bad gateway - service temporarily unavailable";
        case 503:
          return "Service unavailable - please try again later";
        default:
          return `HTTP Error ${status}: ${error.response.statusText || "Unknown error"}`;
      }
    }

    // Network or request setup errors
    if (error.code === "ECONNREFUSED") {
      return "Cannot connect to server - please check your connection";
    }

    if (error.code === "ETIMEDOUT") {
      return "Request timed out - please try again";
    }

    if (error.message) {
      return error.message;
    }
  }

  // Handle other error types
  if (error instanceof Error) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === "string") {
    return error;
  }

  // Fallback for unknown error types
  try {
    return JSON.stringify(error);
  } catch {
    return "An unexpected error occurred";
  }
}

/**
 * Type-safe API response wrapper
 */
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
}

/**
 * Utility function to make GET requests with proper typing
 */
export async function get<T = any>(url: string): Promise<ApiResponse<T>> {
  const response = await apiClient.get<T>(url);
  return {
    data: response.data,
    status: response.status,
    statusText: response.statusText,
  };
}

/**
 * Utility function to make POST requests with proper typing
 */
export async function post<T = any, D = any>(
  url: string,
  data?: D,
): Promise<ApiResponse<T>> {
  const response = await apiClient.post<T>(url, data);
  return {
    data: response.data,
    status: response.status,
    statusText: response.statusText,
  };
}

/**
 * Utility function to make PUT requests with proper typing
 */
export async function put<T = any, D = any>(
  url: string,
  data?: D,
): Promise<ApiResponse<T>> {
  const response = await apiClient.put<T>(url, data);
  return {
    data: response.data,
    status: response.status,
    statusText: response.statusText,
  };
}

/**
 * Utility function to make DELETE requests with proper typing
 */
export async function del<T = any>(url: string): Promise<ApiResponse<T>> {
  const response = await apiClient.delete<T>(url);
  return {
    data: response.data,
    status: response.status,
    statusText: response.statusText,
  };
}

// Export default
export default apiClient;
