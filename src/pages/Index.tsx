import { useState } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { DashboardView } from '@/components/views/DashboardView';
import { ExecuteView } from '@/components/views/ExecuteView';
import { HistoryView } from '@/components/views/HistoryView';
import { ResultsViewer } from '@/components/results/ResultsViewer';
import { ExecutionResult } from '@/types/automation';

const viewConfig: Record<string, { title: string; subtitle?: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'Overview of your automation framework' },
  execute: { title: 'Execute Test', subtitle: 'Configure and run AI-generated tests' },
  history: { title: 'Execution History', subtitle: 'View past test executions' },
  projects: { title: 'Projects', subtitle: 'Manage your automation projects' },
  devices: { title: 'Connected Devices', subtitle: 'View and manage devices' },
  settings: { title: 'Settings', subtitle: 'Configure your automation framework' },
};

export default function Index() {
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedResult, setSelectedResult] = useState<ExecutionResult | null>(null);

  const handleViewResult = (result: ExecutionResult) => {
    setSelectedResult(result);
  };

  const handleBackFromResult = () => {
    setSelectedResult(null);
  };

  const handleExecutionComplete = (result: ExecutionResult) => {
    setSelectedResult(result);
  };

  const currentConfig = viewConfig[activeView] || { title: 'Dashboard' };

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
      case 'devices':
      case 'settings':
        return (
          <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🚧</span>
              </div>
              <h2 className="text-xl font-semibold text-foreground mb-2">Coming Soon</h2>
              <p className="text-muted-foreground">This feature is under development</p>
            </div>
          </div>
        );
      default:
        return <DashboardView onViewResult={handleViewResult} />;
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      
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
