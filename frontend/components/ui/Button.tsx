import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "primary", size = "md", className = "", children, ...props },
    ref,
  ) => {
    const baseClasses =
      "inline-flex items-center justify-center font-medium transition-smooth focus:outline-none focus-visible:outline-2 focus-visible:outline-gold-500 focus-visible:outline-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

    const variantClasses = {
      primary:
        "gradient-gold text-white hover:animate-pulse-glow shadow-gold active:scale-95",
      secondary:
        "glass border border-gold-500 text-gold-400 hover:glass-strong hover:border-gold-400 hover:shadow-gold",
      ghost:
        "bg-transparent border border-slate-600 text-slate-300 hover:glass-light hover:text-gold-400 hover:border-gold-600",
    };

    // 44x44 is WCAG 2.5.5 (AAA) and Apple's HIG; the AA floor in 2.5.8 is
    // 24x24. Both dimensions matter -- a height-only floor still left
    // icon-only and numeric buttons 40px wide.
    //
    // The floor lifts at `lg`, not `sm`: a phone held sideways is 667px wide
    // and still a finger. Scoping this to `sm` switched the floor off exactly
    // when the screen got shorter and targets got harder to hit.
    const sizeClasses = {
      sm: "px-3 py-1.5 text-sm rounded-[var(--radius-sm)] min-h-11 min-w-11 lg:min-h-0 lg:min-w-0",
      md: "px-4 py-2 text-base rounded-[var(--radius-md)] min-h-11 min-w-11 lg:min-h-0 lg:min-w-0",
      lg: "px-6 py-3 text-lg rounded-[var(--radius-lg)]",
    };

    const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;

    return (
      <button ref={ref} className={classes} {...props}>
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
