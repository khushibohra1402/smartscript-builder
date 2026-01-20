import { CheckCircle2, XCircle, AlertTriangle, Clock, ChevronRight } from 'lucide-react';
import { ExecutionResult, ExecutionStatus } from '@/types/automation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

const mockExecutions: ExecutionResult[] = [
  {
    execution_id: 'exec-001',
    status: 'PASS',
    testName: 'Login Flow - Google OAuth',
    projectName: 'YouTube Automation',
    metrics: { total_duration: 12.4, avg_response_time: 0.3, step_success_rate: 100 },
    steps: [],
    artifacts: { video_path: '/videos/exec-001.mp4', screenshot_failure: null },
    ai_analysis: 'All steps completed successfully.',
    createdAt: '2024-01-20T10:30:00Z',
  },
  {
    execution_id: 'exec-002',
    status: 'FAIL',
    testName: 'Search Functionality Test',
    projectName: 'E-Commerce Portal',
    metrics: { total_duration: 8.2, avg_response_time: 0.45, step_success_rate: 67 },
    steps: [],
    artifacts: { video_path: '/videos/exec-002.mp4', screenshot_failure: '/screenshots/exec-002-fail.png' },
    ai_analysis: 'Search button not found after page load. Consider adding a wait condition.',
    createdAt: '2024-01-20T09:15:00Z',
  },
  {
    execution_id: 'exec-003',
    status: 'WARNING',
    testName: 'Checkout Process',
    projectName: 'E-Commerce Portal',
    metrics: { total_duration: 24.1, avg_response_time: 0.8, step_success_rate: 85 },
    steps: [],
    artifacts: { video_path: '/videos/exec-003.mp4', screenshot_failure: null },
    ai_analysis: 'Completed with warnings. Payment step slower than expected.',
    createdAt: '2024-01-20T08:45:00Z',
  },
  {
    execution_id: 'exec-004',
    status: 'PASS',
    testName: 'User Registration',
    projectName: 'Mobile Banking App',
    metrics: { total_duration: 18.7, avg_response_time: 0.5, step_success_rate: 100 },
    steps: [],
    artifacts: { video_path: '/videos/exec-004.mp4', screenshot_failure: null },
    ai_analysis: 'Registration flow completed successfully on Android device.',
    createdAt: '2024-01-19T16:20:00Z',
  },
];

const statusConfig: Record<ExecutionStatus, { icon: React.ReactNode; className: string }> = {
  PASS: { icon: <CheckCircle2 className="w-4 h-4" />, className: 'status-pass' },
  FAIL: { icon: <XCircle className="w-4 h-4" />, className: 'status-fail' },
  WARNING: { icon: <AlertTriangle className="w-4 h-4" />, className: 'status-warning' },
  RUNNING: { icon: <Clock className="w-4 h-4 animate-spin" />, className: 'status-running' },
  PENDING: { icon: <Clock className="w-4 h-4" />, className: 'text-muted-foreground' },
};

interface RecentExecutionsProps {
  onViewResult: (result: ExecutionResult) => void;
}

export function RecentExecutions({ onViewResult }: RecentExecutionsProps) {
  return (
    <div className="glass-card animate-slide-up">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold text-foreground">Recent Executions</h3>
        <Button variant="ghost" size="sm" className="text-primary text-xs">
          View All
          <ChevronRight className="w-3 h-3 ml-1" />
        </Button>
      </div>
      
      <div className="divide-y divide-border">
        {mockExecutions.map((execution) => {
          const status = statusConfig[execution.status];
          return (
            <button
              key={execution.execution_id}
              onClick={() => onViewResult(execution)}
              className="w-full p-4 flex items-center gap-4 hover:bg-muted/50 transition-colors text-left"
            >
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center border",
                status.className
              )}>
                {status.icon}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-foreground truncate">
                  {execution.testName}
                </p>
                <p className="text-xs text-muted-foreground">
                  {execution.projectName} • {execution.metrics.total_duration}s
                </p>
              </div>

              <div className="text-right">
                <p className="text-xs text-muted-foreground">
                  {new Date(execution.createdAt).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </p>
                <p className={cn(
                  "text-xs font-medium",
                  execution.status === 'PASS' ? 'text-success' : 
                  execution.status === 'FAIL' ? 'text-destructive' : 'text-warning'
                )}>
                  {execution.metrics.step_success_rate}%
                </p>
              </div>

              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </button>
          );
        })}
      </div>
    </div>
  );
}
