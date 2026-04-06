import { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TerminalLogProps {
  logs: string[];
  className?: string;
  maxHeight?: string;
}

export function TerminalLog({ logs, className, maxHeight = '300px' }: TerminalLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLineColor = (line: string) => {
    const upper = line.toUpperCase();
    if (upper.includes('ERROR') || upper.includes('FAIL') || upper.includes('EXCEPTION'))
      return 'text-red-400';
    if (upper.includes('PASS') || upper.includes('SUCCESS'))
      return 'text-green-400';
    if (upper.includes('WARN'))
      return 'text-yellow-400';
    if (upper.startsWith('STEP:'))
      return 'text-cyan-400';
    return 'text-muted-foreground';
  };

  return (
    <div className={cn("glass-card overflow-hidden", className)}>
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-muted/50">
        <Terminal className="w-4 h-4 text-primary" />
        <span className="text-sm font-medium text-foreground">Live Execution Logs</span>
        <span className="text-xs text-muted-foreground ml-auto">{logs.length} lines</span>
      </div>
      <div
        ref={scrollRef}
        className="overflow-y-auto p-4 font-mono text-xs leading-relaxed bg-background/80"
        style={{ maxHeight }}
      >
        {logs.length === 0 ? (
          <span className="text-muted-foreground italic">Waiting for execution output...</span>
        ) : (
          logs.map((line, i) => (
            <div key={i} className={cn("whitespace-pre-wrap", getLineColor(line))}>
              <span className="text-muted-foreground/50 select-none mr-3">{String(i + 1).padStart(3, ' ')}</span>
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
