import { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw, Server, Sparkles, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useHealth, useOllamaStatus } from '@/hooks/useApi';
import { cn } from '@/lib/utils';

export function ConnectionStatusOverlay() {
  const [dismissed, setDismissed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  
  const { 
    data: health, 
    isLoading: healthLoading, 
    error: healthError,
    refetch: refetchHealth,
    isRefetching: isRefetchingHealth
  } = useHealth();
  
  const { 
    data: ollamaStatus, 
    isLoading: ollamaLoading, 
    error: ollamaError,
    refetch: refetchOllama,
    isRefetching: isRefetchingOllama
  } = useOllamaStatus();

  // Check connection status
  const backendOnline = !healthError && health?.status === 'ok';
  const ollamaOnline = !ollamaError && ollamaStatus?.is_available;
  const isLoading = healthLoading || ollamaLoading;
  const isRefetching = isRefetchingHealth || isRefetchingOllama;
  
  // Both services must be online to hide the overlay
  const allOnline = backendOnline && ollamaOnline;

  // Auto-retry on mount with exponential backoff
  useEffect(() => {
    if (!allOnline && !isLoading && retryCount < 3) {
      const timer = setTimeout(() => {
        refetchHealth();
        refetchOllama();
        setRetryCount(prev => prev + 1);
      }, Math.pow(2, retryCount) * 1000); // 1s, 2s, 4s
      
      return () => clearTimeout(timer);
    }
  }, [allOnline, isLoading, retryCount, refetchHealth, refetchOllama]);

  // Reset retry count when connection is restored
  useEffect(() => {
    if (allOnline) {
      setRetryCount(0);
    }
  }, [allOnline]);

  const handleRetry = () => {
    setRetryCount(0);
    refetchHealth();
    refetchOllama();
  };

  // Don't show overlay if everything is online or dismissed
  if (allOnline || dismissed) {
    return null;
  }

  // Don't show overlay during initial loading
  if (isLoading && retryCount === 0) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full mx-4 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-warning/10 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-warning" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Connection Issues</h2>
            <p className="text-sm text-muted-foreground">Some services are unavailable</p>
          </div>
        </div>

        <div className="space-y-3">
          {/* Backend Status */}
          <div className={cn(
            "flex items-center justify-between p-3 rounded-lg border",
            backendOnline 
              ? "bg-success/10 border-success/20" 
              : "bg-destructive/10 border-destructive/20"
          )}>
            <div className="flex items-center gap-2">
              <Server className={cn("w-4 h-4", backendOnline ? "text-success" : "text-destructive")} />
              <span className="text-sm font-medium">FastAPI Backend</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">localhost:8000</span>
              {backendOnline ? (
                <Check className="w-4 h-4 text-success" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-destructive animate-pulse" />
              )}
            </div>
          </div>

          {/* Ollama Status */}
          <div className={cn(
            "flex items-center justify-between p-3 rounded-lg border",
            ollamaOnline 
              ? "bg-success/10 border-success/20" 
              : "bg-destructive/10 border-destructive/20"
          )}>
            <div className="flex items-center gap-2">
              <Sparkles className={cn("w-4 h-4", ollamaOnline ? "text-success" : "text-destructive")} />
              <span className="text-sm font-medium">Ollama AI Engine</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">localhost:11434</span>
              {ollamaOnline ? (
                <Check className="w-4 h-4 text-success" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-destructive animate-pulse" />
              )}
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-muted/50 rounded-lg p-3 space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Quick Fix</p>
          <div className="space-y-1 text-sm text-muted-foreground">
            {!backendOnline && (
              <p>• Run: <code className="bg-muted px-1 rounded">cd backend && uvicorn app.main:app --reload</code></p>
            )}
            {!ollamaOnline && (
              <p>• Run: <code className="bg-muted px-1 rounded">ollama serve</code></p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button 
            onClick={handleRetry} 
            className="flex-1"
            disabled={isRefetching}
          >
            {isRefetching ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry Connection
              </>
            )}
          </Button>
          <Button 
            variant="outline" 
            onClick={() => setDismissed(true)}
          >
            Dismiss
          </Button>
        </div>

        {retryCount > 0 && (
          <p className="text-xs text-center text-muted-foreground">
            Attempt {retryCount}/3 - Will auto-retry
          </p>
        )}
      </div>
    </div>
  );
}
