import { 
  Activity, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Zap 
} from 'lucide-react';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { RecentExecutions } from '@/components/dashboard/RecentExecutions';
import { DeviceStatusPanel } from '@/components/dashboard/DeviceStatus';
import { ExecutionResult } from '@/types/automation';

interface DashboardViewProps {
  onViewResult: (result: ExecutionResult) => void;
}

export function DashboardView({ onViewResult }: DashboardViewProps) {
  return (
    <div className="p-6 space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatsCard
          title="Total Executions"
          value={247}
          subtitle="This month"
          icon={Activity}
          trend={{ value: 12, isPositive: true }}
          variant="primary"
        />
        <StatsCard
          title="Pass Rate"
          value="94.2%"
          subtitle="Last 30 days"
          icon={CheckCircle2}
          trend={{ value: 3.5, isPositive: true }}
          variant="success"
        />
        <StatsCard
          title="Failed Tests"
          value={14}
          subtitle="Requires attention"
          icon={XCircle}
          trend={{ value: 2, isPositive: false }}
          variant="destructive"
        />
        <StatsCard
          title="Avg Duration"
          value="18.3s"
          subtitle="Per test case"
          icon={Clock}
          trend={{ value: 8, isPositive: true }}
          variant="warning"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <RecentExecutions onViewResult={onViewResult} />
        </div>
        <div>
          <DeviceStatusPanel />
        </div>
      </div>
    </div>
  );
}
