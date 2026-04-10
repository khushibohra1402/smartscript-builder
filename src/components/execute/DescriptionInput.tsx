import { useState, useEffect } from 'react';
import { Sparkles, Play, Loader2, Code, Eye, EyeOff } from 'lucide-react';
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
  onCodeChange?: (code: string) => void;
}

export function DescriptionInput({
  value,
  onChange,
  disabled,
  onGenerate,
  onExecute,
  isGenerating,
  generatedCode,
  onCodeChange,
}: DescriptionInputProps) {
  const [showCode, setShowCode] = useState(false);

  // Auto-show the code editor when a script is generated (including empty string from errors)
  useEffect(() => {
    if (generatedCode !== null) {
      setShowCode(true);
    }
  }, [generatedCode]);

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
            {showCode ? (
              <><EyeOff className="w-4 h-4 mr-1" /> Hide Code</>
            ) : (
              <><Code className="w-4 h-4 mr-1" /> View Code</>
            )}
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

      {/* Editable Script Editor */}
      {showCode && generatedCode !== null && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Generated Script (editable)</span>
            <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">Python</span>
          </div>
          <Textarea
            value={generatedCode}
            onChange={(e) => onCodeChange?.(e.target.value)}
            className="min-h-[240px] bg-muted border-border font-mono text-sm text-foreground resize-y"
            spellCheck={false}
          />
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