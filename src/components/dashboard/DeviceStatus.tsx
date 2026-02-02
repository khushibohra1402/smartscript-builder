import { Monitor, Smartphone, Wifi, WifiOff, Loader2, AlertCircle } from 'lucide-react';
import { useConnectedDevices } from '@/hooks/useApi';
import { cn } from '@/lib/utils';

export function DeviceStatusPanel() {
  const { data: devices, isLoading, error } = useConnectedDevices();

  if (isLoading) {
    return (
      <div className="glass-card animate-slide-up">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold text-foreground">Connected Devices</h3>
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
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold text-foreground">Connected Devices</h3>
        </div>
        <div className="p-6 flex flex-col items-center gap-2 text-center">
          <AlertCircle className="w-8 h-8 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load devices. Is the backend running?
          </p>
        </div>
      </div>
    );
  }

  if (!devices || devices.length === 0) {
    return (
      <div className="glass-card animate-slide-up">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold text-foreground">Connected Devices</h3>
        </div>
        <div className="p-6 text-center">
          <p className="text-sm text-muted-foreground">
            No devices connected. Start the backend and connect a browser or mobile device.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card animate-slide-up">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-foreground">Connected Devices</h3>
      </div>

      <div className="p-4 space-y-3">
        {devices.map((device) => (
          <div
            key={device.id}
            className={cn(
              "flex items-center gap-3 p-3 rounded-lg border transition-colors",
              device.status === 'ready' ? "bg-success/5 border-success/20" :
              device.status === 'busy' ? "bg-warning/5 border-warning/20" :
              "bg-muted/50 border-border"
            )}
          >
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center",
              device.status === 'ready' ? "bg-success/10" :
              device.status === 'busy' ? "bg-warning/10" : "bg-muted"
            )}>
              {device.device_type === 'web' ? (
                <Monitor className={cn(
                  "w-5 h-5",
                  device.status === 'ready' ? "text-success" :
                  device.status === 'busy' ? "text-warning" : "text-muted-foreground"
                )} />
              ) : (
                <Smartphone className={cn(
                  "w-5 h-5",
                  device.status === 'ready' ? "text-success" :
                  device.status === 'busy' ? "text-warning" : "text-muted-foreground"
                )} />
              )}
            </div>

            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">{device.name}</p>
              <p className="text-xs text-muted-foreground capitalize">{device.platform}</p>
            </div>

            <div className="flex items-center gap-1.5">
              {device.status === 'offline' ? (
                <WifiOff className="w-3.5 h-3.5 text-muted-foreground" />
              ) : (
                <Wifi className={cn(
                  "w-3.5 h-3.5",
                  device.status === 'ready' ? "text-success" : "text-warning"
                )} />
              )}
              <span className={cn(
                "text-xs font-medium capitalize",
                device.status === 'ready' ? "text-success" :
                device.status === 'busy' ? "text-warning" : "text-muted-foreground"
              )}>
                {device.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}