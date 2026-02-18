/**
 * HTTP API Client - Typed requests to Python backend
 */

import { API_CONFIG, API_ENDPOINTS } from './config';
import type {
  ProjectCreate,
  ProjectUpdate,
  ProjectResponse,
  DeviceValidationRequest,
  DeviceValidationResponse,
  DeviceResponse,
  ScriptGenerationRequest,
  ScriptGenerationResponse,
  TestCaseCreate,
  TestCaseResponse,
  ExecutionRequest,
  ExecutionResult,
  ExecutionListItem,
  HealthResponse,
  OllamaStatus,
  ApiError,
   DashboardStats,
} from './types';

class ApiClient {
  private timeout: number;

  constructor() {
    this.timeout = API_CONFIG.TIMEOUT;
  }

  // Always read the URL dynamically so changes via setBackendUrl() take effect
  private get baseUrl(): string {
    return API_CONFIG.BASE_URL;
  }

  // Generic request method with error handling
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    customTimeout?: number
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), customTimeout || this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          error: 'Request failed',
          detail: response.statusText,
        }));
        throw new ApiRequestError(
          errorData.error || 'Request failed',
          response.status,
          errorData
        );
      }

      // Handle empty responses
      const text = await response.text();
      if (!text) return {} as T;
      
      return JSON.parse(text) as T;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiRequestError) {
        throw error;
      }
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiRequestError('Request timeout', 408);
      }
      
      throw new ApiRequestError(
        error instanceof Error ? error.message : 'Network error',
        0
      );
    }
  }

  private get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  private post<T>(endpoint: string, data?: unknown, customTimeout?: number): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }, customTimeout);
  }

  private put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  private delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // ============================================================================
  // System Endpoints
  // ============================================================================

  async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>(API_ENDPOINTS.HEALTH);
  }

  async getOllamaStatus(): Promise<OllamaStatus> {
    return this.get<OllamaStatus>(API_ENDPOINTS.OLLAMA_STATUS);
  }

  // ============================================================================
  // Project Endpoints
  // ============================================================================

  async getProjects(): Promise<ProjectResponse[]> {
    return this.get<ProjectResponse[]>(API_ENDPOINTS.PROJECTS);
  }

  async getProject(id: string): Promise<ProjectResponse> {
    return this.get<ProjectResponse>(API_ENDPOINTS.PROJECT(id));
  }

  async createProject(data: ProjectCreate): Promise<ProjectResponse> {
    return this.post<ProjectResponse>(API_ENDPOINTS.PROJECTS, data);
  }

  async updateProject(id: string, data: ProjectUpdate): Promise<ProjectResponse> {
    return this.put<ProjectResponse>(API_ENDPOINTS.PROJECT(id), data);
  }

  async deleteProject(id: string): Promise<void> {
    return this.delete<void>(API_ENDPOINTS.PROJECT(id));
  }

  async indexProjectLibrary(id: string): Promise<{ message: string; methods_indexed: number }> {
    return this.post<{ message: string; methods_indexed: number }>(
      API_ENDPOINTS.PROJECT_INDEX(id)
    );
  }

  // ============================================================================
  // Device Endpoints
  // ============================================================================

  async validateDevice(data: DeviceValidationRequest): Promise<DeviceValidationResponse> {
    return this.post<DeviceValidationResponse>(API_ENDPOINTS.DEVICE_VALIDATE, data);
  }

  async getConnectedDevices(): Promise<DeviceResponse[]> {
    return this.get<DeviceResponse[]>(API_ENDPOINTS.DEVICES);
  }

  // ============================================================================
  // Script Endpoints
  // ============================================================================

  async generateScript(data: ScriptGenerationRequest): Promise<ScriptGenerationResponse> {
    return this.post<ScriptGenerationResponse>(
      API_ENDPOINTS.SCRIPT_GENERATE, data, API_CONFIG.LLM_TIMEOUT
    );
  }

  async validateScript(scriptCode: string): Promise<{ is_valid: boolean; errors: string[] }> {
    return this.post<{ is_valid: boolean; errors: string[] }>(
      API_ENDPOINTS.SCRIPT_VALIDATE,
      { script_code: scriptCode }
    );
  }

  async saveTestCase(data: TestCaseCreate): Promise<TestCaseResponse> {
    return this.post<TestCaseResponse>(API_ENDPOINTS.SCRIPT_SAVE, data);
  }

  async getTestCases(projectId?: string): Promise<TestCaseResponse[]> {
    const endpoint = projectId
      ? `${API_ENDPOINTS.TEST_CASES}?project_id=${projectId}`
      : API_ENDPOINTS.TEST_CASES;
    return this.get<TestCaseResponse[]>(endpoint);
  }

  async getTestCase(id: string): Promise<TestCaseResponse> {
    return this.get<TestCaseResponse>(API_ENDPOINTS.TEST_CASE(id));
  }

  // ============================================================================
  // Execution Endpoints
  // ============================================================================

  async executeTest(data: ExecutionRequest): Promise<ExecutionResult> {
    return this.post<ExecutionResult>(API_ENDPOINTS.EXECUTIONS, data);
  }

  async getExecution(id: string): Promise<ExecutionResult> {
    return this.get<ExecutionResult>(API_ENDPOINTS.EXECUTION(id));
  }

  async getExecutionHistory(params?: {
    project_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ExecutionListItem[]> {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set('project_id', params.project_id);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    
    const query = searchParams.toString();
    const endpoint = query ? `${API_ENDPOINTS.EXECUTIONS}?${query}` : API_ENDPOINTS.EXECUTIONS;
    return this.get<ExecutionListItem[]>(endpoint);
  }
   
   // ============================================================================
   // Dashboard Endpoints
   // ============================================================================
 
   async getDashboardStats(days: number = 30): Promise<DashboardStats> {
     return this.get<DashboardStats>(`${API_ENDPOINTS.DASHBOARD_STATS}?days=${days}`);
   }
}

// Custom error class for API errors
export class ApiRequestError extends Error {
  public status: number;
  public data?: ApiError;

  constructor(message: string, status: number, data?: ApiError) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.data = data;
  }

  get isNetworkError(): boolean {
    return this.status === 0;
  }

  get isTimeout(): boolean {
    return this.status === 408;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
