import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConnectionStatusOverlay } from "@/components/layout/ConnectionStatusOverlay";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
      staleTime: 30000,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <ConnectionStatusOverlay />
      <BrowserRouter>
        <Routes>
          {/* Main views - all handled by Index with view state */}
          <Route path="/" element={<Index />} />
          <Route path="/dashboard" element={<Index initialView="dashboard" />} />
          <Route path="/execute" element={<Index initialView="execute" />} />
          <Route path="/history" element={<Index initialView="history" />} />
          <Route path="/projects" element={<Index initialView="projects" />} />
          <Route path="/devices" element={<Index initialView="devices" />} />
          <Route path="/settings" element={<Index initialView="settings" />} />
          <Route path="/architecture" element={<Index initialView="architecture" />} />
          
          {/* Catch-all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
