import { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock,
  Search,
  Filter,
  Calendar,
  ChevronRight
} from 'lucide-react';
import { ExecutionResult, ExecutionStatus } from '@/types/automation';
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

const mockHistory: ExecutionResult[] = [
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
    ai_analysis: 'Search button not found after page load.',
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
    ai_analysis: 'Registration flow completed successfully.',
    createdAt: '2024-01-19T16:20:00Z',
  },
  {
    execution_id: 'exec-005',
    status: 'PASS',
    testName: 'Video Playback Test',
    projectName: 'YouTube Automation',
    metrics: { total_duration: 22.1, avg_response_time: 0.4, step_success_rate: 100 },
    steps: [],
    artifacts: { video_path: '/videos/exec-005.mp4', screenshot_failure: null },
    ai_analysis: 'Video playback verified across quality settings.',
    createdAt: '2024-01-19T14:00:00Z',
  },
  {
    execution_id: 'exec-006',
    status: 'FAIL',
    testName: 'Password Reset Flow',
    projectName: 'Mobile Banking App',
    metrics: { total_duration: 15.3, avg_response_time: 0.6, step_success_rate: 50 },
    steps: [],
    artifacts: { video_path: '/videos/exec-006.mp4', screenshot_failure: '/screenshots/exec-006-fail.png' },
    ai_analysis: 'Email verification link timeout.',
    createdAt: '2024-01-19T11:30:00Z',
  },
];

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

  const filteredHistory = mockHistory.filter(item => {
    const matchesSearch = item.testName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.projectName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    const matchesProject = projectFilter === 'all' || item.projectName === projectFilter;
    return matchesSearch && matchesStatus && matchesProject;
  });

  const projects = [...new Set(mockHistory.map(h => h.projectName))];

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
              {projects.map(project => (
                <SelectItem key={project} value={project}>{project}</SelectItem>
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
              return (
                <tr 
                  key={execution.execution_id}
                  className="hover:bg-muted/30 transition-colors cursor-pointer"
                  onClick={() => onViewResult(execution)}
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
                    <p className="font-medium text-foreground">{execution.testName}</p>
                    <p className="text-xs text-muted-foreground">{execution.execution_id}</p>
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">
                    {execution.projectName}
                  </td>
                  <td className="p-4 text-sm text-foreground font-mono">
                    {execution.metrics.total_duration}s
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "text-sm font-medium",
                      execution.metrics.step_success_rate === 100 ? 'text-success' :
                      execution.metrics.step_success_rate >= 80 ? 'text-warning' : 'text-destructive'
                    )}>
                      {execution.metrics.step_success_rate}%
                    </span>
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">
                    {new Date(execution.createdAt).toLocaleDateString()}
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
            <p className="text-muted-foreground">No executions match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
