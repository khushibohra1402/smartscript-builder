/**
 * API Configuration
 *
 * The backend URL can be overridden at runtime via localStorage so that users
 * can point the app at their local FastAPI server when running the Lovable
 * cloud preview (which is HTTPS and therefore cannot reach http://localhost
 * due to browser mixed-content security restrictions).
 */

const STORAGE_KEY = 'BACKEND_URL';
const DEFAULT_BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function getBackendUrl(): string {
  return localStorage.getItem(STORAGE_KEY) || DEFAULT_BACKEND_URL;
}

export function setBackendUrl(url: string): void {
  localStorage.setItem(STORAGE_KEY, url.replace(/\/$/, '')); // strip trailing slash
}

export function resetBackendUrl(): void {
  localStorage.removeItem(STORAGE_KEY);
}

/** Whether the page is on HTTPS but the configured backend is plain HTTP */
export function isMixedContentBlocked(): boolean {
  const isHttps = window.location.protocol === 'https:';
  const backendIsHttp = getBackendUrl().startsWith('http://');
  return isHttps && backendIsHttp;
}

export const API_CONFIG = {
  get BASE_URL() { return getBackendUrl(); },
  get WS_URL() { return getBackendUrl().replace(/^http/, 'ws'); },

  // Request timeout in milliseconds (default for most requests)
  TIMEOUT: 30000,

  // Extended timeout for LLM generation requests (matches backend 300s)
  LLM_TIMEOUT: 310000,

  // Retry configuration
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

export const API_ENDPOINTS = {
  // System
  HEALTH: '/system/health',
  OLLAMA_STATUS: '/system/status',
  
  // Projects
  PROJECTS: '/projects',
  PROJECT: (id: string) => `/projects/${id}`,
  PROJECT_INDEX: (id: string) => `/projects/${id}/index`,
  
  // Devices
  DEVICES: '/devices',
  DEVICE_VALIDATE: '/devices/validate',
  
  // Scripts
  SCRIPT_GENERATE: '/scripts/generate',
  SCRIPT_VALIDATE: '/scripts/validate',
  SCRIPT_SAVE: '/scripts/save',
  TEST_CASES: '/scripts/test-cases',
  TEST_CASE: (id: string) => `/scripts/test-cases/${id}`,
  
  // Executions
  EXECUTIONS: '/executions',
  EXECUTION: (id: string) => `/executions/${id}`,
  EXECUTION_WS: (id: string) => `/ws/execution/${id}`,
   
   // Dashboard
   DASHBOARD_STATS: '/dashboard/stats',
} as const;
