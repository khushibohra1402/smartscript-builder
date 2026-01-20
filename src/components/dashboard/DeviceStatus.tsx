import { Monitor, Smartphone, Wifi, WifiOff } from 'lucide-react';
import { DeviceStatus as DeviceStatusType } from '@/types/automation';
import { cn } from '@/lib/utils';

const mockDevices: DeviceStatusType[] = [
  { id: 'dev-1', name: 'Chrome Browser', type: 'web', platform: 'chrome', status: 'ready', lastSeen: '2024-01-20T10:30:00Z' },
  { id: 'dev-2', name: 'Firefox Browser', type: 'web', platform: 'firefox', status: 'ready', lastSeen: '2024-01-20T10:30:00Z' },
  { id: 'dev-3', name: 'Samsung Galaxy S23', type: 'mobile', platform: 'android', status: 'busy', lastSeen: '2024-01-20T10:28:00Z' },
  { id: 'dev-4', name: 'iPhone 15 Pro', type: 'mobile', platform: 'ios', status: 'offline', lastSeen: '2024-01-19T18:00:00Z' },
];

export function DeviceStatusPanel() {
  return (
    <div className="glass-card animate-slide-up">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-foreground">Connected Devices</h3>
      </div>

      <div className="p-4 space-y-3">
        {mockDevices.map((device) => (
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
              {device.type === 'web' ? (
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
