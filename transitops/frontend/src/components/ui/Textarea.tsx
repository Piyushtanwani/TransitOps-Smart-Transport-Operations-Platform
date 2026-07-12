import { forwardRef } from 'react';
import type { TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col space-y-1 w-full">
        <label className="text-[11px] uppercase tracking-wide text-ink-mute font-medium">
          {label}
        </label>
        <textarea
          ref={ref}
          className={`rounded-md border bg-surface-1 px-3 py-2 text-sm text-ink placeholder:text-ink-mute focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal ${
            error ? 'border-danger' : 'border-surface-2'
          } ${className}`}
          {...props}
        />
        {error && <span className="text-xs text-danger">{error}</span>}
        {hint && !error && <span className="text-xs text-ink-mute">{hint}</span>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
