import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'gold' | 'copper' | 'success' | 'warning' | 'error' | 'info' | 'slate';
  children: React.ReactNode;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'gold', className = '', children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-[var(--radius-sm)] text-xs font-medium transition-smooth';

    const variantClasses = {
      gold: 'bg-gold-500/20 text-gold-400 border border-gold-500/30',
      copper: 'bg-copper-500/20 text-copper-400 border border-copper-500/30',
      success: 'bg-success/20 text-success border border-success/30',
      warning: 'bg-warning/20 text-warning border border-warning/30',
      error: 'bg-error/20 text-error border border-error/30',
      info: 'bg-info/20 text-info border border-info/30',
      slate: 'bg-slate-700/50 text-slate-300 border border-slate-600'
    };

    const classes = `${baseClasses} ${variantClasses[variant]} ${className}`;

    return (
      <span ref={ref} className={classes} {...props}>
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
