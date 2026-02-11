import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { DashboardView } from '@/components/views/DashboardView';
import { ExecuteView } from '@/components/views/ExecuteView';
import { HistoryView } from '@/components/views/HistoryView';
import { ProjectsView } from '@/components/views/ProjectsView';
import { DevicesView } from '@/components/views/DevicesView';
import { SettingsView } from '@/components/views/SettingsView';
import { ArchitectureView } from '@/components/views/ArchitectureView';
import { ResultsViewer } from '@/components/results/ResultsViewer';
import { ExecutionResult } from '@/types/automation';

const viewConfig: Record<string, { title: string; subtitle?: string; route: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'Overview of your automation framework', route: '/dashboard' },
  execute: { title: 'Execute Test', subtitle: 'Configure and run AI-generated tests', route: '/execute' },
  history: { title: 'Execution History', subtitle: 'View past test executions', route: '/history' },
  projects: { title: 'Projects', subtitle: 'Manage your automation projects', route: '/projects' },
  devices: { title: 'Connected Devices', subtitle: 'View and manage devices', route: '/devices' },
  settings: { title: 'Settings', subtitle: 'Configure your automation framework', route: '/settings' },
  architecture: { title: 'Technical Architecture', subtitle: 'System design & RAG pipeline reference', route: '/architecture' },
};

interface IndexProps {
  initialView?: string;
}

export default function Index({ initialView }: IndexProps) {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Determine active view from route or prop
  const getViewFromPath = (path: string): string => {
    const routeToView: Record<string, string> = {
      '/': 'dashboard',
      '/dashboard': 'dashboard',
      '/execute': 'execute',
      '/history': 'history',
      '/projects': 'projects',
      '/devices': 'devices',
      '/settings': 'settings',
      '/architecture': 'architecture',
    };
    return routeToView[path] || 'dashboard';
  };

  const [activeView, setActiveView] = useState(initialView || getViewFromPath(location.pathname));
  const [selectedResult, setSelectedResult] = useState<ExecutionResult | null>(null);

  // Sync view with route changes
  useEffect(() => {
    const viewFromPath = getViewFromPath(location.pathname);
    if (viewFromPath !== activeView && !initialView) {
      setActiveView(viewFromPath);
    }
  }, [location.pathname, initialView, activeView]);

  const handleViewChange = (view: string) => {
    setActiveView(view);
    setSelectedResult(null);
    const route = viewConfig[view]?.route || '/';
    navigate(route);
  };

  const handleViewResult = (result: ExecutionResult) => {
    setSelectedResult(result);
  };

  const handleBackFromResult = () => {
    setSelectedResult(null);
  };

  const handleExecutionComplete = (result: ExecutionResult) => {
    setSelectedResult(result);
  };

  const currentConfig = viewConfig[activeView] || { title: 'Dashboard', route: '/' };

  const renderView = () => {
    if (selectedResult) {
      return <ResultsViewer result={selectedResult} onBack={handleBackFromResult} />;
    }

    switch (activeView) {
      case 'dashboard':
        return <DashboardView onViewResult={handleViewResult} />;
      case 'execute':
        return <ExecuteView onExecutionComplete={handleExecutionComplete} />;
      case 'history':
        return <HistoryView onViewResult={handleViewResult} />;
      case 'projects':
        return <ProjectsView />;
      case 'devices':
        return <DevicesView />;
      case 'settings':
        return <SettingsView />;
      case 'architecture':
        return <ArchitectureView />;
      default:
        return <DashboardView onViewResult={handleViewResult} />;
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar activeView={activeView} onViewChange={handleViewChange} />
      
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title={selectedResult ? 'Execution Result' : currentConfig.title} 
          subtitle={selectedResult ? selectedResult.testName : currentConfig.subtitle} 
        />
        
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {renderView()}
        </div>
      </main>
    </div>
  );
}
