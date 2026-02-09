import { RefreshCw, Smartphone, Monitor, Wifi, WifiOff, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useConnectedDevices } from '@/hooks/useApi';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

export function DevicesView() {
  const { data: devices, isLoading, error, refetch, isRefetching } = useConnectedDevices();

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 bg-muted animate-pulse rounded" />
          <div className="h-10 w-24 bg-muted animate-pulse rounded" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto">
            <WifiOff className="w-8 h-8 text-destructive" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">Failed to Load Devices</h2>
          <p className="text-muted-foreground">Is the backend running?</p>
          <Button onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-success text-success-foreground';
      case 'busy':
        return 'bg-warning text-warning-foreground';
      case 'offline':
        return 'bg-destructive text-destructive-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getDeviceIcon = (deviceType: string) => {
    return deviceType === 'mobile' ? Smartphone : Monitor;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Connected Devices</h2>
          <p className="text-muted-foreground">
            View and manage devices available for testing
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isRefetching}>
          <RefreshCw className={cn("w-4 h-4 mr-2", isRefetching && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-muted/50 border border-border rounded-lg p-4">
        <h3 className="font-medium text-foreground mb-2">Device Detection</h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• <strong>Android:</strong> Connect via USB with ADB debugging enabled</li>
          <li>• <strong>iOS:</strong> Connect via USB with libimobiledevice installed</li>
          <li>• <strong>Web:</strong> Browser binaries are auto-detected</li>
        </ul>
      </div>

      {/* Devices Grid */}
      {!devices || devices.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-border rounded-xl">
          <Wifi className="w-12 h-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No Devices Connected</h3>
          <p className="text-muted-foreground text-center max-w-sm">
            Connect a device via USB or ensure your browser is installed to see it here.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {devices.map((device: {
            id: string;
            name: string;
            device_type: string;
            platform: string;
            status: string;
            last_seen?: string;
          }) => {
            const DeviceIcon = getDeviceIcon(device.device_type);
            return (
              <div
                key={device.id}
                className="glass-card p-5 space-y-4 hover:border-primary/30 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center",
                      device.status === 'ready' ? "bg-success/10" : "bg-muted"
                    )}>
                      <DeviceIcon className={cn(
                        "w-5 h-5",
                        device.status === 'ready' ? "text-success" : "text-muted-foreground"
                      )} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">{device.name}</h3>
                      <p className="text-xs text-muted-foreground capitalize">
                        {device.platform} • {device.device_type}
                      </p>
                    </div>
                  </div>
                  <Badge className={cn("capitalize", getStatusColor(device.status))}>
                    {device.status}
                  </Badge>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-border">
                  <code className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                    {device.id}
                  </code>
                  {device.last_seen && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      <span>{format(new Date(device.last_seen), 'HH:mm:ss')}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
