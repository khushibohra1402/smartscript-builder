import { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Play,
  ArrowLeft,
  Download,
  Share2,
  Sparkles,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { ExecutionResult, TestStep, ExecutionStatus } from '@/types/automation';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

const mockSteps: TestStep[] = [
  { id: 's1', action: 'Navigate to youtube.com', result: true, latency: 850, error: null, timestamp: '00:00.85' },
  { id: 's2', action: 'Click Sign In button', result: true, latency: 120, error: null, timestamp: '00:01.00' },
  { id: 's3', action: 'Enter email address', result: true, latency: 340, error: null, timestamp: '00:01.35' },
  { id: 's4', action: 'Click Next button', result: true, latency: 95, error: null, timestamp: '00:01.45' },
  { id: 's5', action: 'Enter password', result: true, latency: 280, error: null, timestamp: '00:01.75' },
  { id: 's6', action: 'Click Sign In', result: true, latency: 1200, error: null, timestamp: '00:02.95' },
  { id: 's7', action: 'Wait for home page', result: true, latency: 2100, error: null, timestamp: '00:05.05' },
  { id: 's8', action: 'Click search bar', result: true, latency: 80, error: null, timestamp: '00:05.15' },
  { id: 's9', action: 'Type "React tutorials"', result: true, latency: 450, error: null, timestamp: '00:05.60' },
  { id: 's10', action: 'Press Enter', result: true, latency: 65, error: null, timestamp: '00:05.70' },
  { id: 's11', action: 'Wait for search results', result: true, latency: 1800, error: null, timestamp: '00:07.50' },
  { id: 's12', action: 'Click first video', result: true, latency: 150, error: null, timestamp: '00:07.65' },
];

const statusConfig: Record<ExecutionStatus, { 
  icon: React.ReactNode; 
  label: string;
  bgClass: string;
  textClass: string;
  glowClass: string;
}> = {
  PASS: { 
    icon: <CheckCircle2 className="w-8 h-8" />, 
    label: 'PASSED',
    bgClass: 'bg-success/20',
    textClass: 'text-success',
    glowClass: 'glow-success'
  },
  FAIL: { 
    icon: <XCircle className="w-8 h-8" />, 
    label: 'FAILED',
    bgClass: 'bg-destructive/20',
    textClass: 'text-destructive',
    glowClass: 'glow-destructive'
  },
  WARNING: { 
    icon: <AlertTriangle className="w-8 h-8" />, 
    label: 'WARNING',
    bgClass: 'bg-warning/20',
    textClass: 'text-warning',
    glowClass: ''
  },
  RUNNING: { 
    icon: <Clock className="w-8 h-8 animate-spin" />, 
    label: 'RUNNING',
    bgClass: 'bg-primary/20',
    textClass: 'text-primary',
    glowClass: 'animate-pulse-glow'
  },
  PENDING: { 
    icon: <Clock className="w-8 h-8" />, 
    label: 'PENDING',
    bgClass: 'bg-muted',
    textClass: 'text-muted-foreground',
    glowClass: ''
  },
};

interface ResultsViewerProps {
  result: ExecutionResult;
  onBack: () => void;
}

export function ResultsViewer({ result, onBack }: ResultsViewerProps) {
  const [expandedSteps, setExpandedSteps] = useState(true);
  const status = statusConfig[result.status];
  const stepsWithDetails = mockSteps;

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onBack} className="text-muted-foreground">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Executions
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Executive Header */}
      <div className={cn(
        "glass-card p-6 border-l-4",
        result.status === 'PASS' ? 'border-l-success' :
        result.status === 'FAIL' ? 'border-l-destructive' : 'border-l-warning'
      )}>
        <div className="flex items-start gap-6">
          <div className={cn(
            "w-16 h-16 rounded-2xl flex items-center justify-center",
            status.bgClass,
            status.glowClass
          )}>
            <span className={status.textClass}>{status.icon}</span>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-xl font-bold text-foreground">{result.testName}</h2>
              <span className={cn(
                "px-3 py-1 rounded-full text-xs font-bold",
                status.bgClass,
                status.textClass
              )}>
                {status.label}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              {result.projectName} • Executed on {new Date(result.createdAt).toLocaleString()}
            </p>

            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Duration</p>
                <p className="text-2xl font-bold text-foreground">
                  {result.metrics.total_duration}
                  <span className="text-sm text-muted-foreground ml-1">sec</span>
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Avg Response</p>
                <p className="text-2xl font-bold text-foreground">
                  {(result.metrics.avg_response_time * 1000).toFixed(0)}
                  <span className="text-sm text-muted-foreground ml-1">ms</span>
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Confidence Score</p>
                <div className="flex items-center gap-3">
                  <p className={cn(
                    "text-2xl font-bold",
                    result.metrics.step_success_rate === 100 ? 'text-success' :
                    result.metrics.step_success_rate >= 80 ? 'text-warning' : 'text-destructive'
                  )}>
                    {result.metrics.step_success_rate}%
                  </p>
                  <Progress 
                    value={result.metrics.step_success_rate} 
                    className="flex-1 h-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Video Player */}
        <div className="col-span-2 glass-card overflow-hidden">
          <div className="aspect-video bg-[#0d1117] flex items-center justify-center relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5" />
            <div className="text-center z-10">
              <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4 cursor-pointer hover:bg-primary/30 transition-colors">
                <Play className="w-8 h-8 text-primary ml-1" />
              </div>
              <p className="text-sm text-muted-foreground">Recording Available</p>
              <p className="text-xs text-muted-foreground/70 mt-1">{result.artifacts.video_path}</p>
            </div>
          </div>
          <div className="p-4 border-t border-border">
            <h4 className="font-medium text-foreground mb-2">Session Recording</h4>
            <p className="text-sm text-muted-foreground">
              Full browser/device recording with {stepsWithDetails.length} captured actions
            </p>
          </div>
        </div>

        {/* AI Analysis */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-accent" />
            </div>
            <h4 className="font-semibold text-foreground">AI Analysis</h4>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {result.ai_analysis}
          </p>
          {result.status === 'FAIL' && (
            <div className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-xs font-medium text-destructive mb-1">Recommendation</p>
              <p className="text-sm text-destructive/80">
                Add an explicit wait condition for the element to be clickable before interaction.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Step Timeline */}
      <div className="glass-card">
        <button
          onClick={() => setExpandedSteps(!expandedSteps)}
          className="w-full p-4 flex items-center justify-between hover:bg-muted/30 transition-colors"
        >
          <h4 className="font-semibold text-foreground">Step Timeline ({stepsWithDetails.length} steps)</h4>
          {expandedSteps ? (
            <ChevronDown className="w-5 h-5 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-5 h-5 text-muted-foreground" />
          )}
        </button>

        {expandedSteps && (
          <div className="border-t border-border">
            <div className="divide-y divide-border max-h-[400px] overflow-y-auto scrollbar-thin">
              {stepsWithDetails.map((step, index) => (
                <div key={step.id} className="flex items-center gap-4 p-4 hover:bg-muted/30 transition-colors">
                  <div className="w-8 text-center">
                    <span className="text-xs text-muted-foreground font-mono">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                  </div>
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center",
                    step.result ? "bg-success/20" : "bg-destructive/20"
                  )}>
                    {step.result ? (
                      <CheckCircle2 className="w-4 h-4 text-success" />
                    ) : (
                      <XCircle className="w-4 h-4 text-destructive" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{step.action}</p>
                    {step.error && (
                      <p className="text-xs text-destructive mt-1">{step.error}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-mono text-muted-foreground">{step.timestamp}</p>
                    <p className={cn(
                      "text-xs",
                      step.latency < 500 ? "text-success" :
                      step.latency < 1000 ? "text-warning" : "text-destructive"
                    )}>
                      {step.latency}ms
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
