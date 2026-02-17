/**
 * API Types - Mirrors backend Pydantic schemas
 * Keep in sync with backend/app/models/schemas.py
 */

// Enums
export type ExecutionStatus = 'PENDING' | 'RUNNING' | 'PASS' | 'FAIL' | 'WARNING';
export type DeviceType = 'web' | 'mobile';
export type Platform = 'chrome' | 'firefox' | 'safari' | 'android' | 'ios';
export type TestType = 'functional' | 'regression' | 'smoke' | 'integration';
export type DeviceStatusType = 'ready' | 'busy' | 'offline';

// Project
export interface ProjectCreate {
  name: string;
  description?: string;
  library_path: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  library_path?: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  description?: string;
  library_path: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  last_indexed_at?: string;
}

// Device Validation
export interface DeviceValidationRequest {
  device_type: DeviceType;
  platform: Platform;
  device_id?: string;
}

export interface DeviceValidationResponse {
  is_valid: boolean;
  device_type: DeviceType;
  platform: Platform;
  device_id?: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface DeviceResponse {
  id: string;
  name: string;
  device_type: DeviceType;
  platform: Platform;
  status: DeviceStatusType;
  last_seen?: string;
}

// Script Generation
export interface ScriptGenerationRequest {
  project_id: string;
  description: string;
  device_type: DeviceType;
  platform: Platform;
  test_type: TestType;
}

export interface ScriptGenerationResponse {
  script_code: string;
  is_valid: boolean;
  validation_errors?: string[];
  rag_context_used: string[];
  generation_time_ms: number;
}

// Test Case
export interface TestCaseCreate {
  project_id: string;
  name: string;
  description: string;
  device_type: DeviceType;
  platform: Platform;
  test_type: TestType;
  script_code: string;
}

export interface TestCaseResponse {
  id: string;
  project_id: string;
  name: string;
  description: string;
  device_type: DeviceType;
  platform: Platform;
  test_type: TestType;
  script_code?: string;
  script_validated: boolean;
  validation_errors?: string[];
  created_at: string;
}

// Execution
export interface ExecutionStep {
  action: string;
  result: boolean;
  latency: number;
  error?: string;
}

export interface ExecutionMetrics {
  total_duration: number;
  avg_response_time: number;
  step_success_rate: number;
}

export interface ExecutionArtifacts {
  video_path: string;
  screenshot_failure?: string;
}

export interface ExecutionResult {
  execution_id: string;
  status: ExecutionStatus;
  test_name: string;
  project_name: string;
  metrics: ExecutionMetrics;
  steps: ExecutionStep[];
  artifacts: ExecutionArtifacts;
  ai_analysis: string;
  created_at: string;
}

export interface ExecutionRequest {
  test_case_id: string;
  device_id?: string;
}

export interface ExecutionListItem {
  execution_id: string;
  test_name: string;
  project_name: string;
  status: ExecutionStatus;
  total_duration?: number;
  step_success_rate?: number;
  created_at: string;
}

// WebSocket Messages
export interface WebSocketMessage {
  type: 'step_complete' | 'execution_complete' | 'error';
  execution_id: string;
  data: Record<string, unknown>;
}

export interface StepUpdateMessage {
  step_number: number;
  action: string;
  result: boolean;
  latency: number;
  error?: string;
}

// System
export interface HealthResponse {
  status: string;
  timestamp?: string;
  version?: string;
  ollama_status?: string;
  database_status?: string;
}

export interface OllamaStatus {
  // Supports backend's actual response shape
  app?: Record<string, unknown>;
  ollama?: {
    healthy: boolean;
    host: string;
    configured_model: string;
    available_models: string[];
  };
  // Legacy fields for compatibility
  is_available?: boolean;
  host?: string;
  models?: string[];
  active_model?: string;
  timestamp?: string;
}

// Error
export interface ApiError {
  error: string;
  detail?: string;
  code?: string;
}
 
 // Dashboard
 export interface DashboardStats {
   total_executions: number;
   pass_rate: number;
   failed_tests: number;
   avg_duration: number;
   executions_trend: number;
   pass_rate_trend: number;
   failed_tests_trend: number;
   duration_trend: number;
 }
