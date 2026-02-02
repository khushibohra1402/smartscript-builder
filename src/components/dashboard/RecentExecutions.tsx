import { CheckCircle2, XCircle, AlertTriangle, Clock, ChevronRight, Loader2, AlertCircle } from 'lucide-react';
import { ExecutionResult, ExecutionStatus } from '@/types/automation';
import { useExecutionHistory } from '@/hooks/useApi';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

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
  const { data: executions, isLoading, error } = useExecutionHistory({ limit: 4 });

  if (isLoading) {
    return (
      <div className="glass-card animate-slide-up">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground">Recent Executions</h3>
        </div>
        <div className="p-8 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card animate-slide-up">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground">Recent Executions</h3>
        </div>
        <div className="p-6 flex flex-col items-center gap-2 text-center">
          <AlertCircle className="w-8 h-8 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load executions. Is the backend running?
          </p>
        </div>
      </div>
    );
  }

  if (!executions || executions.length === 0) {
    return (
      <div className="glass-card animate-slide-up">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground">Recent Executions</h3>
        </div>
        <div className="p-6 text-center">
          <p className="text-sm text-muted-foreground">
            No executions yet. Run a test to see results here.
          </p>
        </div>
      </div>
    );
  }

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
        {executions.map((execution) => {
          const status = statusConfig[execution.status];
          
          // Create a minimal ExecutionResult for the callback
          const handleClick = () => {
            const result: ExecutionResult = {
              execution_id: execution.execution_id,
              status: execution.status,
              testName: execution.test_name,
              projectName: execution.project_name,
              metrics: {
                total_duration: execution.total_duration || 0,
                avg_response_time: 0,
                step_success_rate: execution.step_success_rate || 0,
              },
              steps: [],
              artifacts: { video_path: '', screenshot_failure: null },
              ai_analysis: '',
              createdAt: execution.created_at,
            };
            onViewResult(result);
          };

          return (
            <button
              key={execution.execution_id}
              onClick={handleClick}
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
                  {execution.test_name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {execution.project_name} • {execution.total_duration?.toFixed(1) || '?'}s
                </p>
              </div>

              <div className="text-right">
                <p className="text-xs text-muted-foreground">
                  {new Date(execution.created_at).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </p>
                <p className={cn(
                  "text-xs font-medium",
                  execution.status === 'PASS' ? 'text-success' : 
                  execution.status === 'FAIL' ? 'text-destructive' : 'text-warning'
                )}>
                  {execution.step_success_rate?.toFixed(0) || '?'}%
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