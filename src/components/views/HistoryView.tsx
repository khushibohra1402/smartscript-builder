import { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock,
  Search,
  Filter,
  Calendar,
  ChevronRight,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { ExecutionResult, ExecutionStatus } from '@/types/automation';
import { useExecutionHistory, useProjects } from '@/hooks/useApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

const statusConfig: Record<ExecutionStatus, { icon: React.ReactNode; className: string }> = {
  PASS: { icon: <CheckCircle2 className="w-4 h-4" />, className: 'status-pass' },
  FAIL: { icon: <XCircle className="w-4 h-4" />, className: 'status-fail' },
  WARNING: { icon: <AlertTriangle className="w-4 h-4" />, className: 'status-warning' },
  RUNNING: { icon: <Clock className="w-4 h-4 animate-spin" />, className: 'status-running' },
  PENDING: { icon: <Clock className="w-4 h-4" />, className: 'text-muted-foreground' },
};

interface HistoryViewProps {
  onViewResult: (result: ExecutionResult) => void;
}

export function HistoryView({ onViewResult }: HistoryViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [projectFilter, setProjectFilter] = useState<string>('all');

  // Fetch data from API
  const { 
    data: executions, 
    isLoading: isLoadingExecutions, 
    error: executionsError 
  } = useExecutionHistory({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    project_id: projectFilter !== 'all' ? projectFilter : undefined,
  });

  const { data: projects } = useProjects();

  // Client-side search filter (API doesn't support search by name)
  const filteredHistory = executions?.filter(item => {
    if (!searchQuery) return true;
    return item.test_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
           item.project_name.toLowerCase().includes(searchQuery.toLowerCase());
  }) || [];

  if (isLoadingExecutions) {
    return (
      <div className="p-6">
        <div className="glass-card p-8 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (executionsError) {
    return (
      <div className="p-6">
        <div className="glass-card p-8 flex flex-col items-center gap-4 text-center">
          <AlertCircle className="w-12 h-12 text-destructive" />
          <div>
            <h3 className="font-semibold text-foreground mb-1">Failed to Load History</h3>
            <p className="text-sm text-muted-foreground">
              Could not connect to the backend. Make sure the server is running on port 8000.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by test name or project..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-secondary border-border"
            />
          </div>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40 bg-secondary border-border">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="PASS">Passed</SelectItem>
              <SelectItem value="FAIL">Failed</SelectItem>
              <SelectItem value="WARNING">Warning</SelectItem>
            </SelectContent>
          </Select>

          <Select value={projectFilter} onValueChange={setProjectFilter}>
            <SelectTrigger className="w-48 bg-secondary border-border">
              <SelectValue placeholder="Project" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Projects</SelectItem>
              {projects?.map(project => (
                <SelectItem key={project.id} value={project.id}>{project.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="outline" className="border-border">
            <Calendar className="w-4 h-4 mr-2" />
            Date Range
          </Button>
        </div>
      </div>

      {/* Results Table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="text-left p-4 text-sm font-medium text-muted-foreground">Status</th>
              <th className="text-left p-4 text-sm font-medium text-muted-foreground">Test Name</th>
              <th className="text-left p-4 text-sm font-medium text-muted-foreground">Project</th>
              <th className="text-left p-4 text-sm font-medium text-muted-foreground">Duration</th>
              <th className="text-left p-4 text-sm font-medium text-muted-foreground">Pass Rate</th>
              <th className="text-left p-4 text-sm font-medium text-muted-foreground">Date</th>
              <th className="w-12"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredHistory.map((execution) => {
              const status = statusConfig[execution.status];
              
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
                <tr 
                  key={execution.execution_id}
                  className="hover:bg-muted/30 transition-colors cursor-pointer"
                  onClick={handleClick}
                >
                  <td className="p-4">
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center border",
                      status.className
                    )}>
                      {status.icon}
                    </div>
                  </td>
                  <td className="p-4">
                    <p className="font-medium text-foreground">{execution.test_name}</p>
                    <p className="text-xs text-muted-foreground">{execution.execution_id}</p>
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">
                    {execution.project_name}
                  </td>
                  <td className="p-4 text-sm text-foreground font-mono">
                    {execution.total_duration?.toFixed(1) || '?'}s
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "text-sm font-medium",
                      (execution.step_success_rate || 0) === 100 ? 'text-success' :
                      (execution.step_success_rate || 0) >= 80 ? 'text-warning' : 'text-destructive'
                    )}>
                      {execution.step_success_rate?.toFixed(0) || '?'}%
                    </span>
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">
                    {new Date(execution.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4">
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredHistory.length === 0 && (
          <div className="p-12 text-center">
            <p className="text-muted-foreground">
              {executions?.length === 0 
                ? "No executions yet. Run a test to see history here."
                : "No executions match your filters"
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
}