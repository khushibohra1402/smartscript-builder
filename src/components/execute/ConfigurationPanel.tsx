import { useState } from 'react';
import { ChevronDown, Monitor, Smartphone, Check, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { TestConfiguration, DeviceType, Platform, TestType, Project } from '@/types/automation';
import { cn } from '@/lib/utils';

const mockProjects: Project[] = [
  { id: 'proj-1', name: 'YouTube Automation', description: 'Video streaming tests', libraryPath: '/libs/youtube', createdAt: '2024-01-15' },
  { id: 'proj-2', name: 'E-Commerce Portal', description: 'Shopping flow tests', libraryPath: '/libs/ecommerce', createdAt: '2024-01-10' },
  { id: 'proj-3', name: 'Mobile Banking App', description: 'Banking transactions', libraryPath: '/libs/banking', createdAt: '2024-01-05' },
];

const platformOptions: Record<DeviceType, { value: Platform; label: string }[]> = {
  web: [
    { value: 'chrome', label: 'Chrome' },
    { value: 'firefox', label: 'Firefox' },
    { value: 'safari', label: 'Safari' },
  ],
  mobile: [
    { value: 'android', label: 'Android' },
    { value: 'ios', label: 'iOS' },
  ],
};

interface ConfigurationPanelProps {
  config: TestConfiguration;
  onConfigChange: (config: TestConfiguration) => void;
  deviceValidated: boolean;
  onValidateDevice: () => void;
  isValidating: boolean;
}

export function ConfigurationPanel({
  config,
  onConfigChange,
  deviceValidated,
  onValidateDevice,
  isValidating,
}: ConfigurationPanelProps) {
  const updateConfig = <K extends keyof TestConfiguration>(
    key: K,
    value: TestConfiguration[K]
  ) => {
    onConfigChange({ ...config, [key]: value });
  };

  return (
    <div className="glass-card p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Test Configuration</h3>
        {deviceValidated && (
          <div className="flex items-center gap-1.5 text-success text-sm">
            <Check className="w-4 h-4" />
            <span>Device Ready</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Project Selection */}
        <div className="col-span-2">
          <Label className="text-sm text-muted-foreground mb-2 block">Project</Label>
          <Select
            value={config.project?.id || ''}
            onValueChange={(value) => {
              const project = mockProjects.find(p => p.id === value);
              updateConfig('project', project || null);
            }}
          >
            <SelectTrigger className="bg-secondary border-border">
              <SelectValue placeholder="Select a project" />
            </SelectTrigger>
            <SelectContent>
              {mockProjects.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  <div className="flex flex-col">
                    <span>{project.name}</span>
                    <span className="text-xs text-muted-foreground">{project.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Device Type */}
        <div>
          <Label className="text-sm text-muted-foreground mb-2 block">Device Type</Label>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => {
                updateConfig('deviceType', 'web');
                updateConfig('platform', 'chrome');
              }}
              className={cn(
                "flex items-center justify-center gap-2 p-3 rounded-lg border transition-all",
                config.deviceType === 'web'
                  ? "bg-primary/10 border-primary text-primary"
                  : "bg-secondary border-border text-muted-foreground hover:border-primary/50"
              )}
            >
              <Monitor className="w-4 h-4" />
              <span className="text-sm font-medium">Web</span>
            </button>
            <button
              onClick={() => {
                updateConfig('deviceType', 'mobile');
                updateConfig('platform', 'android');
              }}
              className={cn(
                "flex items-center justify-center gap-2 p-3 rounded-lg border transition-all",
                config.deviceType === 'mobile'
                  ? "bg-primary/10 border-primary text-primary"
                  : "bg-secondary border-border text-muted-foreground hover:border-primary/50"
              )}
            >
              <Smartphone className="w-4 h-4" />
              <span className="text-sm font-medium">Mobile</span>
            </button>
          </div>
        </div>

        {/* Platform */}
        <div>
          <Label className="text-sm text-muted-foreground mb-2 block">Platform</Label>
          <Select
            value={config.platform}
            onValueChange={(value) => updateConfig('platform', value as Platform)}
          >
            <SelectTrigger className="bg-secondary border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {platformOptions[config.deviceType].map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Test Type */}
        <div>
          <Label className="text-sm text-muted-foreground mb-2 block">Test Type</Label>
          <Select
            value={config.testType}
            onValueChange={(value) => updateConfig('testType', value as TestType)}
          >
            <SelectTrigger className="bg-secondary border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="functional">Functional</SelectItem>
              <SelectItem value="regression">Regression</SelectItem>
              <SelectItem value="smoke">Smoke</SelectItem>
              <SelectItem value="integration">Integration</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Test Case Name */}
        <div>
          <Label className="text-sm text-muted-foreground mb-2 block">Test Case Name</Label>
          <Input
            value={config.testCaseName}
            onChange={(e) => updateConfig('testCaseName', e.target.value)}
            placeholder="e.g., Login Flow Test"
            className="bg-secondary border-border"
          />
        </div>
      </div>

      {/* Validate Button */}
      <div className="flex items-center gap-3 pt-2">
        <Button
          onClick={onValidateDevice}
          disabled={!config.project || isValidating}
          className={cn(
            "flex-1",
            deviceValidated 
              ? "bg-success hover:bg-success/90" 
              : "bg-primary hover:bg-primary/90"
          )}
        >
          {isValidating ? (
            <>
              <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin mr-2" />
              Validating...
            </>
          ) : deviceValidated ? (
            <>
              <Check className="w-4 h-4 mr-2" />
              Device Validated
            </>
          ) : (
            'Validate Device Connection'
          )}
        </Button>
      </div>

      {!deviceValidated && config.project && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-warning/10 border border-warning/20">
          <AlertCircle className="w-4 h-4 text-warning mt-0.5" />
          <p className="text-sm text-warning">
            Validate device connection before writing your test description
          </p>
        </div>
      )}
    </div>
  );
}
