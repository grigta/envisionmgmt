import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-[var(--omni-text)] mb-1.5"
          >
            {label}
            {props.required && (
              <span className="text-[var(--omni-error)] ml-0.5">*</span>
            )}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "w-full px-3 py-2 text-sm rounded-lg border transition-colors duration-200",
            "bg-[var(--omni-surface)] text-[var(--omni-text)]",
            "border-[var(--omni-border)]",
            "placeholder:text-[var(--omni-text-muted)]",
            "focus:outline-none focus:border-[var(--omni-primary)] focus:ring-2 focus:ring-[var(--omni-primary)]/10",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            error && "border-[var(--omni-error)] focus:border-[var(--omni-error)] focus:ring-[var(--omni-error)]/10",
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-[var(--omni-error)]">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
