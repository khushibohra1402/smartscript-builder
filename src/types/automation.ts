export type ExecutionStatus = 'PASS' | 'FAIL' | 'WARNING' | 'RUNNING' | 'PENDING';

export type DeviceType = 'web' | 'mobile';
export type Platform = 'chrome' | 'firefox' | 'safari' | 'android' | 'ios';
export type TestType = 'functional' | 'regression' | 'smoke' | 'integration';

export interface Project {
  id: string;
  name: string;
  description: string;
  libraryPath: string;
  createdAt: string;
}

export interface TestStep {
  id: string;
  action: string;
  result: boolean;
  latency: number;
  error: string | null;
  timestamp: string;
}

export interface ExecutionResult {
  execution_id: string;
  status: ExecutionStatus;
  testName: string;
  projectName: string;
  metrics: {
    total_duration: number;
    avg_response_time: number;
    step_success_rate: number;
  };
  steps: TestStep[];
  artifacts: {
    video_path: string;
    screenshot_failure: string | null;
  };
  ai_analysis: string;
  createdAt: string;
}

export interface TestConfiguration {
  project: Project | null;
  deviceType: DeviceType;
  platform: Platform;
  testType: TestType;
  testCaseName: string;
  description: string;
}

export interface DeviceStatus {
  id: string;
  name: string;
  type: DeviceType;
  platform: Platform;
  status: 'ready' | 'busy' | 'offline';
  lastSeen: string;
}
