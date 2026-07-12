import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface DateInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const DateInput = forwardRef<HTMLInputElement, DateInputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col space-y-1 w-full">
        <label className="text-[11px] uppercase tracking-wide text-ink-mute font-medium">
          {label}
        </label>
        <input
          type="date"
          ref={ref}
          className={`rounded-md border bg-surface-1 px-3 py-2 text-sm text-ink focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal ${
            error ? 'border-danger' : 'border-surface-2'
          } ${className}`}
          {...props}
        />
        {error && <span className="text-xs text-danger">{error}</span>}
      </div>
    );
  }
);

DateInput.displayName = 'DateInput';
