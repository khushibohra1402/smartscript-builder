import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#2dd4bf',
    primaryTextColor: '#e2e8f0',
    primaryBorderColor: '#334155',
    lineColor: '#64748b',
    secondaryColor: '#7c3aed',
    tertiaryColor: '#1e293b',
    background: '#0f172a',
    mainBkg: '#1e293b',
    nodeBorder: '#334155',
    clusterBkg: '#1e293b',
    titleColor: '#e2e8f0',
    edgeLabelBackground: '#1e293b',
  },
  flowchart: { curve: 'basis', padding: 20 },
  fontFamily: 'JetBrains Mono, monospace',
  fontSize: 13,
});

interface MermaidDiagramProps {
  chart: string;
  title?: string;
}

export function MermaidDiagram({ chart, title }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState('');

  useEffect(() => {
    const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;
    mermaid.render(id, chart).then(({ svg }) => {
      setSvg(svg);
    }).catch(console.error);
  }, [chart]);

  return (
    <div className="space-y-3">
      {title && (
        <h3 className="text-sm font-semibold text-primary font-mono uppercase tracking-wider">
          {title}
        </h3>
      )}
      <div
        ref={containerRef}
        className="glass-card p-6 overflow-x-auto scrollbar-thin"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
}
