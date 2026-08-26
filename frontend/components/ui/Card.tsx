import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "glass" | "glass-strong" | "glass-card";
  children: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ variant = "glass-card", className = "", children, ...props }, ref) => {
    const classes = `${variant} rounded-[var(--radius-lg)] ${className}`;

    return (
      <div ref={ref} className={classes} {...props}>
        {children}
      </div>
    );
  },
);

Card.displayName = "Card";

export const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", children, ...props }, ref) => {
  return (
    <div ref={ref} className={`p-6 ${className}`} {...props}>
      {children}
    </div>
  );
});

CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className = "", children, ...props }, ref) => {
  return (
    // Solid gold, not the old gradient — the gradient shimmer is what read as
    // dated, the gold itself never was. Roman, not italic: h1/h2 carry the
    // slant, and italicising every card title would be a lot of it.
    <h3
      ref={ref}
      className={`font-display text-lg font-semibold tracking-tight text-gold-400 ${className}`}
      {...props}
    >
      {children}
    </h3>
  );
});

CardTitle.displayName = "CardTitle";

export const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className = "", children, ...props }, ref) => {
  return (
    <p ref={ref} className={`mt-2 text-slate-400 ${className}`} {...props}>
      {children}
    </p>
  );
});

CardDescription.displayName = "CardDescription";

export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", children, ...props }, ref) => {
  return (
    <div ref={ref} className={`px-6 pb-6 ${className}`} {...props}>
      {children}
    </div>
  );
});

CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", children, ...props }, ref) => {
  return (
    <div ref={ref} className={`px-6 pb-6 pt-4 ${className}`} {...props}>
      {children}
    </div>
  );
});

CardFooter.displayName = "CardFooter";
