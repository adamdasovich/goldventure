import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className = '', ...props }, ref) => {
    const inputClasses = `
      w-full px-4 py-2.5
      glass-light
      rounded-[var(--radius-sm)]
      border border-slate-600
      text-slate-100 placeholder-slate-500
      transition-smooth
      focus:outline-none
      focus:border-gold-500
      focus:glass
      disabled:opacity-50 disabled:cursor-not-allowed
      ${icon ? 'pl-10' : ''}
      ${error ? 'border-error focus:border-error' : ''}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    return (
      <div className="w-full">
        {label && (
          <label className="block mb-2 text-sm font-medium text-slate-300">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {icon}
            </div>
          )}
          <input ref={ref} className={inputClasses} {...props} />
        </div>
        {error && (
          <p className="mt-1.5 text-sm text-error">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className = '', ...props }, ref) => {
    const textareaClasses = `
      w-full px-4 py-2.5
      glass-light
      rounded-[var(--radius-sm)]
      border border-slate-600
      text-slate-100 placeholder-slate-500
      transition-smooth
      focus:outline-none
      focus:border-gold-500
      focus:glass
      disabled:opacity-50 disabled:cursor-not-allowed
      resize-vertical
      min-h-[100px]
      ${error ? 'border-error focus:border-error' : ''}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    return (
      <div className="w-full">
        {label && (
          <label className="block mb-2 text-sm font-medium text-slate-300">
            {label}
          </label>
        )}
        <textarea ref={ref} className={textareaClasses} {...props} />
        {error && (
          <p className="mt-1.5 text-sm text-error">{error}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
