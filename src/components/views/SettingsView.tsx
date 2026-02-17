import { useState, useEffect } from 'react';
import { Save, Server, Sparkles, RefreshCw, Check, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { useHealth, useOllamaStatus } from '@/hooks/useApi';
import { cn } from '@/lib/utils';

interface AppSettings {
  apiUrl: string;
  wsUrl: string;
  ollamaHost: string;
  ollamaModel: string;
  autoRetry: boolean;
  darkMode: boolean;
}

const defaultSettings: AppSettings = {
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000',
  ollamaHost: 'http://localhost:11434',
  ollamaModel: 'mistral:7b',
  autoRetry: true,
  darkMode: true,
};

export function SettingsView() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [hasChanges, setHasChanges] = useState(false);
  const { toast } = useToast();
  
  const { data: health, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth();
  const { data: ollamaStatus, isLoading: ollamaLoading, error: ollamaError, refetch: refetchOllama } = useOllamaStatus();

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('smartscript-settings');
    if (saved) {
      try {
        setSettings({ ...defaultSettings, ...JSON.parse(saved) });
      } catch {
        // Use defaults if parsing fails
      }
    }
  }, []);

  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    localStorage.setItem('smartscript-settings', JSON.stringify(settings));
    setHasChanges(false);
    toast({
      title: 'Settings Saved',
      description: 'Your configuration has been updated.',
    });
  };

  const handleTestConnections = () => {
    refetchHealth();
    refetchOllama();
    toast({
      title: 'Testing Connections',
      description: 'Checking backend and AI engine...',
    });
  };

  const backendOnline = !healthError && !!health;
  const ollamaOnline = !ollamaError && !!ollamaStatus && (
    ollamaStatus?.ollama?.healthy === true || ollamaStatus?.is_available === true || !!ollamaStatus
  );

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Settings</h2>
          <p className="text-muted-foreground">Configure your automation framework</p>
        </div>
        <Button onClick={handleSave} disabled={!hasChanges}>
          <Save className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>

      {/* Connection Status */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Connection Status</h3>
          <Button variant="outline" size="sm" onClick={handleTestConnections}>
            <RefreshCw className={cn(
              "w-4 h-4 mr-2",
              (healthLoading || ollamaLoading) && "animate-spin"
            )} />
            Test Connections
          </Button>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2">
          {/* Backend Status */}
          <div className={cn(
            "flex items-center justify-between p-4 rounded-lg border",
            backendOnline 
              ? "bg-success/10 border-success/20" 
              : "bg-destructive/10 border-destructive/20"
          )}>
            <div className="flex items-center gap-3">
              <Server className={cn("w-5 h-5", backendOnline ? "text-success" : "text-destructive")} />
              <div>
                <p className="font-medium text-foreground">FastAPI Backend</p>
                <p className="text-xs text-muted-foreground">{settings.apiUrl}</p>
              </div>
            </div>
            {backendOnline ? (
              <Check className="w-5 h-5 text-success" />
            ) : (
              <AlertCircle className="w-5 h-5 text-destructive" />
            )}
          </div>

          {/* Ollama Status */}
          <div className={cn(
            "flex items-center justify-between p-4 rounded-lg border",
            ollamaOnline 
              ? "bg-success/10 border-success/20" 
              : "bg-destructive/10 border-destructive/20"
          )}>
            <div className="flex items-center gap-3">
              <Sparkles className={cn("w-5 h-5", ollamaOnline ? "text-success" : "text-destructive")} />
              <div>
                <p className="font-medium text-foreground">Ollama AI Engine</p>
                <p className="text-xs text-muted-foreground">
                  {ollamaStatus?.ollama?.configured_model || ollamaStatus?.active_model || settings.ollamaModel}
                </p>
              </div>
            </div>
            {ollamaOnline ? (
              <Check className="w-5 h-5 text-success" />
            ) : (
              <AlertCircle className="w-5 h-5 text-destructive" />
            )}
          </div>
        </div>
      </div>

      {/* API Configuration */}
      <div className="glass-card p-6 space-y-4">
        <h3 className="text-lg font-semibold text-foreground">API Configuration</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="apiUrl">Backend URL</Label>
            <Input
              id="apiUrl"
              value={settings.apiUrl}
              onChange={(e) => updateSetting('apiUrl', e.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="wsUrl">WebSocket URL</Label>
            <Input
              id="wsUrl"
              value={settings.wsUrl}
              onChange={(e) => updateSetting('wsUrl', e.target.value)}
              placeholder="ws://localhost:8000"
            />
          </div>
        </div>
      </div>

      {/* AI Configuration */}
      <div className="glass-card p-6 space-y-4">
        <h3 className="text-lg font-semibold text-foreground">AI Engine Configuration</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="ollamaHost">Ollama Host</Label>
            <Input
              id="ollamaHost"
              value={settings.ollamaHost}
              onChange={(e) => updateSetting('ollamaHost', e.target.value)}
              placeholder="http://localhost:11434"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ollamaModel">Model</Label>
            <Input
              id="ollamaModel"
              value={settings.ollamaModel}
              onChange={(e) => updateSetting('ollamaModel', e.target.value)}
              placeholder="mistral:7b"
            />
            <p className="text-xs text-muted-foreground">
              Run: ollama pull {settings.ollamaModel}
            </p>
          </div>
        </div>
      </div>

      <Separator />

      {/* Preferences */}
      <div className="glass-card p-6 space-y-4">
        <h3 className="text-lg font-semibold text-foreground">Preferences</h3>
        
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-foreground">Auto-retry on failure</p>
            <p className="text-sm text-muted-foreground">
              Automatically retry failed connections up to 3 times
            </p>
          </div>
          <Switch
            checked={settings.autoRetry}
            onCheckedChange={(checked) => updateSetting('autoRetry', checked)}
          />
        </div>

        <Separator />

        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-foreground">Dark Mode</p>
            <p className="text-sm text-muted-foreground">
              Toggle between light and dark theme
            </p>
          </div>
          <Switch
            checked={settings.darkMode}
            onCheckedChange={(checked) => {
              updateSetting('darkMode', checked);
              document.documentElement.classList.toggle('dark', checked);
            }}
          />
        </div>
      </div>
    </div>
  );
}
