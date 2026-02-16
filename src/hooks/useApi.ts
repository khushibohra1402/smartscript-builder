/**
 * React Hooks for API Client
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type {
  ProjectCreate,
  ProjectUpdate,
  ProjectResponse,
  DeviceValidationRequest,
  ScriptGenerationRequest,
  TestCaseCreate,
  ExecutionRequest,
} from '@/services/api';

 import type { DashboardStats } from '@/services/api/types';
 
// Query Keys
export const queryKeys = {
  health: ['health'] as const,
  ollamaStatus: ['ollama-status'] as const,
  projects: ['projects'] as const,
  project: (id: string) => ['projects', id] as const,
  devices: ['devices'] as const,
  testCases: (projectId?: string) => ['test-cases', projectId] as const,
  testCase: (id: string) => ['test-cases', 'detail', id] as const,
  executions: (filters?: Record<string, unknown>) => ['executions', filters] as const,
  execution: (id: string) => ['executions', 'detail', id] as const,
   dashboardStats: (days: number) => ['dashboard-stats', days] as const,
};

// ============================================================================
// System Hooks
// ============================================================================

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Check every 30s
    retry: 1,
  });
}

export function useOllamaStatus() {
  return useQuery({
    queryKey: queryKeys.ollamaStatus,
    queryFn: () => apiClient.getOllamaStatus(),
    refetchInterval: 60000,
    retry: 1,
    // The /system/status endpoint returns a broader object; 
    // we just need a successful response to know the backend is reachable
  });
}

// ============================================================================
// Project Hooks
// ============================================================================

export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => apiClient.getProjects(),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: () => apiClient.getProject(id),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ProjectCreate) => apiClient.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProjectUpdate }) =>
      apiClient.updateProject(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.project(id) });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => apiClient.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
}

export function useIndexProjectLibrary() {
  return useMutation({
    mutationFn: (id: string) => apiClient.indexProjectLibrary(id),
  });
}

// ============================================================================
// Device Hooks
// ============================================================================

export function useConnectedDevices() {
  return useQuery({
    queryKey: queryKeys.devices,
    queryFn: () => apiClient.getConnectedDevices(),
    refetchInterval: 10000, // Refresh every 10s
  });
}

export function useValidateDevice() {
  return useMutation({
    mutationFn: (data: DeviceValidationRequest) => apiClient.validateDevice(data),
  });
}

// ============================================================================
// Script Hooks
// ============================================================================

export function useGenerateScript() {
  return useMutation({
    mutationFn: (data: ScriptGenerationRequest) => apiClient.generateScript(data),
  });
}

export function useValidateScript() {
  return useMutation({
    mutationFn: (scriptCode: string) => apiClient.validateScript(scriptCode),
  });
}

export function useSaveTestCase() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TestCaseCreate) => apiClient.saveTestCase(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.testCases(result.project_id) });
    },
  });
}

export function useTestCases(projectId?: string) {
  return useQuery({
    queryKey: queryKeys.testCases(projectId),
    queryFn: () => apiClient.getTestCases(projectId),
  });
}

export function useTestCase(id: string) {
  return useQuery({
    queryKey: queryKeys.testCase(id),
    queryFn: () => apiClient.getTestCase(id),
    enabled: !!id,
  });
}

// ============================================================================
// Execution Hooks
// ============================================================================

export function useExecuteTest() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ExecutionRequest) => apiClient.executeTest(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
    },
  });
}

export function useExecution(id: string) {
  return useQuery({
    queryKey: queryKeys.execution(id),
    queryFn: () => apiClient.getExecution(id),
    enabled: !!id,
  });
}

export function useExecutionHistory(filters?: {
  project_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: queryKeys.executions(filters),
    queryFn: () => apiClient.getExecutionHistory(filters),
  });
}
 
 // ============================================================================
 // Dashboard Hooks
 // ============================================================================
 
 export function useDashboardStats(days: number = 30) {
   return useQuery({
     queryKey: queryKeys.dashboardStats(days),
     queryFn: () => apiClient.getDashboardStats(days),
     refetchInterval: 60000, // Refresh every minute
   });
 }
