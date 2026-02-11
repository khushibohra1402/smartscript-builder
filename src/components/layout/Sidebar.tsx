import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Play, 
  History, 
  Settings, 
  FolderOpen,
  Monitor,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Sparkles,
  Server,
  AlertCircle,
  BookOpen
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHealth, useOllamaStatus } from '@/hooks/useApi';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  route: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, route: '/dashboard' },
  { id: 'execute', label: 'Execute Test', icon: <Play className="w-5 h-5" />, route: '/execute' },
  { id: 'history', label: 'History', icon: <History className="w-5 h-5" />, route: '/history' },
  { id: 'projects', label: 'Projects', icon: <FolderOpen className="w-5 h-5" />, route: '/projects' },
  { id: 'devices', label: 'Devices', icon: <Monitor className="w-5 h-5" />, route: '/devices' },
  { id: 'settings', label: 'Settings', icon: <Settings className="w-5 h-5" />, route: '/settings' },
  { id: 'architecture', label: 'Architecture', icon: <BookOpen className="w-5 h-5" />, route: '/architecture' },
];

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
   
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth();
  const { data: ollamaStatus, isLoading: ollamaLoading, error: ollamaError } = useOllamaStatus();
   
  const backendStatus = useMemo(() => {
    if (healthLoading) return { status: 'loading', label: 'Checking...', color: 'bg-warning' };
    if (healthError) return { status: 'offline', label: 'Backend Offline', color: 'bg-destructive' };
    if (health?.status === 'ok') return { status: 'online', label: 'Backend Online', color: 'bg-success' };
    return { status: 'unknown', label: 'Unknown', color: 'bg-muted-foreground' };
  }, [health, healthLoading, healthError]);
   
  const aiStatus = useMemo(() => {
    if (ollamaLoading) return { status: 'loading', label: 'Checking Ollama...', detail: '', color: 'bg-warning' };
    if (ollamaError || !ollamaStatus?.is_available) return { 
      status: 'offline', 
      label: 'Ollama Offline', 
      detail: 'Run: ollama serve',
      color: 'bg-destructive' 
    };
    return { 
      status: 'online', 
      label: 'Ollama Ready', 
      detail: ollamaStatus?.active_model || 'localhost:11434',
      color: 'bg-success' 
    };
  }, [ollamaStatus, ollamaLoading, ollamaError]);

  const handleNavClick = (item: NavItem) => {
    onViewChange(item.id);
    navigate(item.route);
  };

  return (
    <aside 
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-sidebar-border">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Cpu className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-sm text-foreground">SmartScript</span>
              <span className="text-[10px] text-muted-foreground">Builder v1.1</span>
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-md hover:bg-sidebar-accent transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-muted-foreground" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => handleNavClick(item)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
              activeView === item.id
                ? "bg-primary/10 text-primary border border-primary/20"
                : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
            )}
          >
            <span className={cn(activeView === item.id && "text-primary")}>
              {item.icon}
            </span>
            {!collapsed && (
              <span className="text-sm font-medium">{item.label}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Status Section */}
      <div className="p-3 border-t border-sidebar-border">
        {/* Backend Status */}
        <div className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-lg mb-2",
          collapsed && "justify-center"
        )}>
          <div className="relative">
            <Server className="w-4 h-4 text-muted-foreground" />
            <span className={cn(
              "absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full",
              backendStatus.color,
              backendStatus.status === 'loading' && "animate-pulse"
            )} />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">{backendStatus.label}</span>
              <span className="text-[10px] text-muted-foreground">localhost:8000</span>
            </div>
          )}
        </div>
        
        {/* Ollama Status */}
        <div className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-lg bg-sidebar-accent",
          collapsed && "justify-center"
        )}>
          <div className="relative">
            {aiStatus.status === 'offline' ? (
              <AlertCircle className="w-4 h-4 text-destructive" />
            ) : (
              <Sparkles className="w-4 h-4 text-primary" />
            )}
            <span className={cn(
              "absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full",
              aiStatus.color,
              aiStatus.status === 'loading' && "animate-pulse"
            )} />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">{aiStatus.label}</span>
              <span className="text-[10px] text-muted-foreground">{aiStatus.detail}</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
