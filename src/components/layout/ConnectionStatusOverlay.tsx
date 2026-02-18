import { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw, Server, Sparkles, Check, Link, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useHealth, useOllamaStatus } from '@/hooks/useApi';
import { cn } from '@/lib/utils';
import { isMixedContentBlocked, setBackendUrl, getBackendUrl } from '@/services/api/config';

export function ConnectionStatusOverlay() {
  const [dismissed, setDismissed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [customUrl, setCustomUrl] = useState(getBackendUrl());
  const [urlSaved, setUrlSaved] = useState(false);
  const mixedContent = isMixedContentBlocked();

  const {
    data: health,
    isLoading: healthLoading,
    error: healthError,
    refetch: refetchHealth,
    isRefetching: isRefetchingHealth,
  } = useHealth();

  const {
    data: ollamaStatus,
    isLoading: ollamaLoading,
    error: ollamaError,
    refetch: refetchOllama,
    isRefetching: isRefetchingOllama,
  } = useOllamaStatus();

  const backendOnline = !healthError && !!health;
  const ollamaOnline = !ollamaError && !!ollamaStatus;
  const isLoading = healthLoading || ollamaLoading;
  const isRefetching = isRefetchingHealth || isRefetchingOllama;
  const allOnline = backendOnline && ollamaOnline;

  // Auto-retry (skip when mixed-content would just hang forever)
  useEffect(() => {
    if (!allOnline && !isLoading && retryCount < 3 && !mixedContent) {
      const timer = setTimeout(() => {
        refetchHealth();
        refetchOllama();
        setRetryCount((prev) => prev + 1);
      }, Math.pow(2, retryCount) * 1000);
      return () => clearTimeout(timer);
    }
  }, [allOnline, isLoading, retryCount, refetchHealth, refetchOllama, mixedContent]);

  useEffect(() => {
    if (allOnline) setRetryCount(0);
  }, [allOnline]);

  const handleRetry = () => {
    setRetryCount(0);
    refetchHealth();
    refetchOllama();
  };

  const handleSaveUrl = () => {
    const trimmed = customUrl.trim();
    if (!trimmed) return;
    setBackendUrl(trimmed);
    setUrlSaved(true);
    setTimeout(() => {
      setUrlSaved(false);
      handleRetry();
    }, 800);
  };

  if (allOnline || dismissed) return null;
  if (isLoading && retryCount === 0 && !mixedContent) return null;

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-card border border-border rounded-xl shadow-xl max-w-lg w-full mx-4 p-6 space-y-5">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-warning/10 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6 text-warning" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              {mixedContent ? 'Mixed Content Blocked' : 'Connection Issues'}
            </h2>
            <p className="text-sm text-muted-foreground">
              {mixedContent
                ? 'Your browser is blocking HTTP requests from this HTTPS page'
                : 'Some services are unavailable'}
            </p>
          </div>
        </div>

        {/* Mixed-content explanation */}
        {mixedContent && (
          <div className="bg-warning/10 border border-warning/30 rounded-lg p-4 space-y-3 text-sm">
            <p className="font-medium text-foreground">Why is this happening?</p>
            <p className="text-muted-foreground">
              The Lovable preview is served over <strong>HTTPS</strong> but your backend runs on{' '}
              <code className="bg-muted px-1 rounded">http://localhost:8000</code>. Browsers silently
              block these "mixed content" requests — so every fetch hangs forever (Pending, 0 B) and
              no logs appear anywhere.
            </p>
            <p className="font-medium text-foreground mt-2">Fix options:</p>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              <li>
                <strong>Run the frontend locally</strong> — open{' '}
                <code className="bg-muted px-1 rounded">http://localhost:5173</code> in your browser
                instead of using the Lovable cloud preview. Both backend and frontend will be HTTP and
                work fine.
              </li>
              <li>
                <strong>Use ngrok / Cloudflare Tunnel</strong> to expose your local backend over
                HTTPS, then enter that URL below.
              </li>
            </ol>
          </div>
        )}

        {/* Service status pills */}
        <div className="space-y-3">
          <div
            className={cn(
              'flex items-center justify-between p-3 rounded-lg border',
              backendOnline
                ? 'bg-success/10 border-success/20'
                : 'bg-destructive/10 border-destructive/20'
            )}
          >
            <div className="flex items-center gap-2">
              <Server className={cn('w-4 h-4', backendOnline ? 'text-success' : 'text-destructive')} />
              <span className="text-sm font-medium">FastAPI Backend</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{getBackendUrl()}</span>
              {backendOnline ? (
                <Check className="w-4 h-4 text-success" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-destructive animate-pulse" />
              )}
            </div>
          </div>

          <div
            className={cn(
              'flex items-center justify-between p-3 rounded-lg border',
              ollamaOnline
                ? 'bg-success/10 border-success/20'
                : 'bg-destructive/10 border-destructive/20'
            )}
          >
            <div className="flex items-center gap-2">
              <Sparkles className={cn('w-4 h-4', ollamaOnline ? 'text-success' : 'text-destructive')} />
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

        {/* Custom backend URL input */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            <Link className="w-3 h-3" />
            Backend URL (editable)
          </label>
          <div className="flex gap-2">
            <Input
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="https://your-tunnel.ngrok.io"
              className="flex-1 text-sm font-mono"
            />
            <Button
              size="sm"
              variant={urlSaved ? 'default' : 'outline'}
              onClick={handleSaveUrl}
              className="shrink-0"
            >
              {urlSaved ? <Check className="w-4 h-4" /> : 'Save & Retry'}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Tip: must be HTTPS when using the Lovable cloud preview (e.g. ngrok tunnel).
          </p>
        </div>

        {/* Quick-fix for non-mixed-content issues */}
        {!mixedContent && (
          <div className="bg-muted/50 rounded-lg p-3 space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Quick Fix</p>
            <div className="space-y-1 text-sm text-muted-foreground">
              {!backendOnline && (
                <p>
                  • Run:{' '}
                  <code className="bg-muted px-1 rounded">
                    cd backend && uvicorn app.main:app --reload
                  </code>
                </p>
              )}
              {!ollamaOnline && (
                <p>
                  • Run: <code className="bg-muted px-1 rounded">ollama serve</code>
                </p>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Button onClick={handleRetry} className="flex-1" disabled={isRefetching || mixedContent}>
            {isRefetching ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Checking…
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry Connection
              </>
            )}
          </Button>
          <Button variant="outline" onClick={() => setDismissed(true)}>
            Dismiss
          </Button>
        </div>

        {!mixedContent && retryCount > 0 && (
          <p className="text-xs text-center text-muted-foreground">
            Attempt {retryCount}/3 — will auto-retry
          </p>
        )}

        {/* Link to run locally */}
        <a
          href="http://localhost:5173"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1 text-xs text-primary hover:underline"
        >
          <ExternalLink className="w-3 h-3" />
          Open app at localhost:5173 (recommended for local dev)
        </a>
      </div>
    </div>
  );
}
