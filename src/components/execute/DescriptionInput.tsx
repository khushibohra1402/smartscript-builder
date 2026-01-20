import { useState } from 'react';
import { Sparkles, Play, Loader2, Code } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface DescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
  onGenerate: () => void;
  onExecute: () => void;
  isGenerating: boolean;
  generatedCode: string | null;
}

export function DescriptionInput({
  value,
  onChange,
  disabled,
  onGenerate,
  onExecute,
  isGenerating,
  generatedCode,
}: DescriptionInputProps) {
  const [showCode, setShowCode] = useState(false);

  const examplePrompts = [
    "Login to YouTube with Google account, search for 'React tutorials', and play the first video",
    "Add a product to cart, proceed to checkout, and verify the order summary",
    "Open the banking app, check account balance, and transfer $50 to savings",
  ];

  return (
    <div className={cn(
      "glass-card p-6 space-y-4 transition-opacity",
      disabled && "opacity-50 pointer-events-none"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">AI Test Generation</h3>
        </div>
        {generatedCode && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCode(!showCode)}
            className="text-muted-foreground"
          >
            <Code className="w-4 h-4 mr-1" />
            {showCode ? 'Hide Code' : 'View Code'}
          </Button>
        )}
      </div>

      {disabled && (
        <p className="text-sm text-muted-foreground">
          Please validate your device connection before writing test descriptions.
        </p>
      )}

      <div className="space-y-3">
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Describe what you want to test in natural language..."
          className="min-h-[120px] bg-secondary border-border resize-none"
          disabled={disabled}
        />

        <div className="flex flex-wrap gap-2">
          {examplePrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => onChange(prompt)}
              disabled={disabled}
              className="text-xs px-3 py-1.5 rounded-full bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground transition-colors"
            >
              {prompt.slice(0, 40)}...
            </button>
          ))}
        </div>
      </div>

      {showCode && generatedCode && (
        <div className="relative">
          <pre className="p-4 rounded-lg bg-muted border border-border overflow-x-auto scrollbar-thin">
            <code className="text-sm font-mono text-primary">
              {generatedCode}
            </code>
          </pre>
          <div className="absolute top-2 right-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
            Generated Python
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Button
          onClick={onGenerate}
          disabled={disabled || !value.trim() || isGenerating}
          variant="outline"
          className="flex-1 border-primary text-primary hover:bg-primary/10"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Generate Script
            </>
          )}
        </Button>

        <Button
          onClick={onExecute}
          disabled={disabled || !generatedCode}
          className="flex-1 bg-success hover:bg-success/90 text-success-foreground glow-success"
        >
          <Play className="w-4 h-4 mr-2" />
          Execute Test
        </Button>
      </div>
    </div>
  );
}
