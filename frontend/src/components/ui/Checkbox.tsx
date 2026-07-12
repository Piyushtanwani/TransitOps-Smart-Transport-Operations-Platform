import * as React from 'react';
import { cn } from '../../lib/utils';
import { Check } from 'lucide-react';

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, id, ...props }, ref) => {
    const checkboxId = id || label.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex items-center space-x-2">
        <div className="relative flex items-center justify-center">
          <input
            type="checkbox"
            id={checkboxId}
            ref={ref}
            className={cn(
              "peer h-4 w-4 appearance-none rounded-sm border border-surface-2 bg-surface-1 transition-all checked:border-signal checked:bg-signal focus:outline-none focus:ring-2 focus:ring-signal focus:ring-offset-1 focus:ring-offset-surface-0",
              className
            )}
            {...props}
          />
          <Check className="pointer-events-none absolute h-3 w-3 text-surface-0 opacity-0 peer-checked:opacity-100" strokeWidth={3} />
        </div>
        <label
          htmlFor={checkboxId}
          className="text-sm font-medium leading-none text-on-surface peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          {label}
        </label>
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';
