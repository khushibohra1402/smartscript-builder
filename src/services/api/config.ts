/**
 * API Configuration
 */

export const API_CONFIG = {
  // Base URL for the Python backend
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  
  // WebSocket URL
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  
  // Request timeout in milliseconds (default for most requests)
  TIMEOUT: 30000,
  
  // Extended timeout for LLM generation requests (matches backend 300s)
  LLM_TIMEOUT: 310000,
  
  // Retry configuration
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

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
