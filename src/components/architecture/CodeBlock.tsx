import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  fileName?: string;
}

export function CodeBlock({ code, language = 'python', title, fileName }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-2">
      {title && (
        <h4 className="text-sm font-semibold text-muted-foreground">{title}</h4>
      )}
      <div className="glass-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-border/50 bg-muted/30">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-destructive/60" />
            <span className="w-3 h-3 rounded-full bg-warning/60" />
            <span className="w-3 h-3 rounded-full bg-success/60" />
            {fileName && (
              <span className="ml-3 text-xs text-muted-foreground font-mono">{fileName}</span>
            )}
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <pre className="p-4 overflow-x-auto scrollbar-thin text-sm leading-relaxed">
          <code className="font-mono text-foreground/90">{code}</code>
        </pre>
      </div>
    </div>
  );
}
