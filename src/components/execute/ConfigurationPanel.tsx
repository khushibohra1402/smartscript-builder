import { Monitor, Smartphone, Tv, Check, AlertCircle, Loader2 } from 'lucide-react';
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
import { TestConfiguration, DeviceType, Platform, TestType } from '@/types/automation';
import { useProjects } from '@/hooks/useApi';
import { cn } from '@/lib/utils';

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
  stb: [
    { value: 'stb_linux', label: 'STB Linux' },
    { value: 'stb_proprietary', label: 'STB Proprietary' },
  ],
};

interface RadioOptionProps {
  label: string;
  value: string;
  selected: boolean;
  onChange: () => void;
}

function RadioOption({ label, value, selected, onChange }: RadioOptionProps) {
  return (
    <button
      type="button"
      onClick={onChange}
      className={cn(
        "px-4 py-2 rounded-lg border text-sm font-medium transition-all",
        selected
          ? "bg-primary/10 border-primary text-primary"
          : "bg-secondary border-border text-muted-foreground hover:border-primary/50"
      )}
    >
      {label}
    </button>
  );
}

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
  const { data: projects, isLoading: isLoadingProjects, error: projectsError } = useProjects();

  const updateConfig = <K extends keyof TestConfiguration>(
    key: K,
    value: TestConfiguration[K]
  ) => {
    onConfigChange({ ...config, [key]: value });
  };

  const isSTB = config.deviceType === 'stb';

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
        {/* 1. Project Selection */}
        <div className="col-span-2">
          <Label className="text-sm text-muted-foreground mb-2 block">Project</Label>
          <Select
            value={config.project?.id || ''}
            onValueChange={(value) => {
              const project = projects?.find(p => p.id === value);
              if (project) {
                updateConfig('project', {
                  id: project.id,
                  name: project.name,
                  description: project.description || '',
                  libraryPath: project.library_path,
                  createdAt: project.created_at,
                });
              } else {
                updateConfig('project', null);
              }
            }}
            disabled={isLoadingProjects}
          >
            <SelectTrigger className="bg-secondary border-border">
              {isLoadingProjects ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Loading projects...</span>
                </div>
              ) : (
                <SelectValue placeholder="Select a project" />
              )}
            </SelectTrigger>
            <SelectContent>
              {projectsError && (
                <div className="p-2 text-sm text-destructive">
                  Failed to load projects. Is the backend running?
                </div>
              )}
              {projects?.length === 0 && (
                <div className="p-2 text-sm text-muted-foreground">
                  No projects found. Create one first.
                </div>
              )}
              {projects?.map((project) => (
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

        {/* 2. Device Type */}
        <div className="col-span-2">
          <Label className="text-sm text-muted-foreground mb-2 block">Device Type</Label>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => {
                onConfigChange({ ...config, deviceType: 'web', platform: 'chrome' });
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
                onConfigChange({ ...config, deviceType: 'mobile', platform: 'android' });
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
            <button
              onClick={() => {
                onConfigChange({
                  ...config,
                  deviceType: 'stb',
                  platform: 'stb_linux',
                  stbModel: config.stbModel || 'G4',
                  stbType: config.stbType || 'Production',
                  rcuType: config.rcuType || 'IRRX',
                  smartPlugEnabled: config.smartPlugEnabled ?? false,
                  hdmiCaptureIndex: config.hdmiCaptureIndex ?? 0,
                });
              }}
              className={cn(
                "flex items-center justify-center gap-2 p-3 rounded-lg border transition-all",
                config.deviceType === 'stb'
                  ? "bg-primary/10 border-primary text-primary"
                  : "bg-secondary border-border text-muted-foreground hover:border-primary/50"
              )}
            >
              <Tv className="w-4 h-4" />
              <span className="text-sm font-medium">STB</span>
            </button>
          </div>
        </div>

        {/* --- STB-specific fields --- */}
        {isSTB && (
          <>
            {/* 3. STB Model */}
            <div className="col-span-2">
              <Label className="text-sm text-muted-foreground mb-2 block">STB Model</Label>
              <div className="flex gap-2">
                <RadioOption label="G4" value="G4" selected={config.stbModel === 'G4'} onChange={() => updateConfig('stbModel', 'G4')} />
                <RadioOption label="G5" value="G5" selected={config.stbModel === 'G5'} onChange={() => updateConfig('stbModel', 'G5')} />
              </div>
            </div>

            {/* 4. STB Type */}
            <div className="col-span-2">
              <Label className="text-sm text-muted-foreground mb-2 block">STB Type</Label>
              <div className="flex gap-2">
                <RadioOption label="Production" value="Production" selected={config.stbType === 'Production'} onChange={() => updateConfig('stbType', 'Production')} />
                <RadioOption label="Development" value="Development" selected={config.stbType === 'Development'} onChange={() => updateConfig('stbType', 'Development')} />
              </div>
            </div>

            {/* 5. STB IP */}
            <div className="col-span-2">
              <Label className="text-sm text-muted-foreground mb-2 block">STB IP Address</Label>
              <Input
                value={config.stbIp || ''}
                onChange={(e) => updateConfig('stbIp', e.target.value)}
                placeholder="e.g., 192.168.1.45"
                className="bg-secondary border-border"
              />
            </div>

            {/* 6. RCU Type */}
            <div className="col-span-2">
              <Label className="text-sm text-muted-foreground mb-2 block">RCU Type</Label>
              <div className="flex gap-2">
                <RadioOption label="IRRX" value="IRRX" selected={config.rcuType === 'IRRX'} onChange={() => updateConfig('rcuType', 'IRRX')} />
                <RadioOption label="RPRCU" value="RPRCU" selected={config.rcuType === 'RPRCU'} onChange={() => updateConfig('rcuType', 'RPRCU')} />
              </div>
            </div>

            {/* 7. RCU IP */}
            <div className="col-span-2">
              <Label className="text-sm text-muted-foreground mb-2 block">RCU IP Address</Label>
              <Input
                value={config.rcuIp || config.redratIp || ''}
                onChange={(e) => {
                  onConfigChange({ ...config, rcuIp: e.target.value, redratIp: e.target.value });
                }}
                placeholder="e.g., 192.168.1.60"
                className="bg-secondary border-border"
              />
            </div>

            {/* 8. Smart Plug */}
            <div className="col-span-2">
              <Label className="text-sm text-muted-foreground mb-2 block">Smart Plug</Label>
              <div className="flex gap-2">
                <RadioOption label="Yes" value="yes" selected={config.smartPlugEnabled === true} onChange={() => updateConfig('smartPlugEnabled', true)} />
                <RadioOption label="No" value="no" selected={config.smartPlugEnabled === false || config.smartPlugEnabled === undefined} onChange={() => updateConfig('smartPlugEnabled', false)} />
              </div>
            </div>

            {/* 9. Smart Plug IP (conditional) */}
            {config.smartPlugEnabled && (
              <div className="col-span-2">
                <Label className="text-sm text-muted-foreground mb-2 block">Smart Plug IP Address</Label>
                <Input
                  value={config.smartPlugIp || ''}
                  onChange={(e) => updateConfig('smartPlugIp', e.target.value)}
                  placeholder="e.g., 192.168.1.70"
                  className="bg-secondary border-border"
                />
              </div>
            )}

            {/* HDMI Capture Index */}
            <div>
              <Label className="text-sm text-muted-foreground mb-2 block">HDMI Capture Index</Label>
              <Input
                type="number"
                value={config.hdmiCaptureIndex ?? 0}
                onChange={(e) => updateConfig('hdmiCaptureIndex', parseInt(e.target.value) || 0)}
                placeholder="0"
                className="bg-secondary border-border"
              />
            </div>
          </>
        )}

        {/* Non-STB: Platform selector */}
        {!isSTB && (
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
        )}

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
