import React, { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonProps = {
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  state?: "primary" | "secondary" | "dropdown" | "destructive";
  size?: "small" | "medium" | "large";
} & ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({
  children,
  className,
  disabled,
  ...allProps
}: ButtonProps) {
  return (
    <button
      className={`flex flex-row ${
        disabled ? "pointer-events-none" : ""
      } bg-transparent hover:bg-white/10 text-white rounded-[4px] border active:translate-y-[2px] active:scale-[0.99] duration-250 border-white/20 text-base px-3 py-1 transition-all ease-out duration-250 ${className}`}
      {...allProps}
    >
      {children}
    </button>
  );
}

export function LoadingSVG({
  diameter = 20,
  strokeWidth = 4,
}: {
  diameter?: number;
  strokeWidth?: number;
}) {
  return (
    <svg
      className="animate-spin"
      fill="none"
      viewBox="0 0 24 24"
      style={{
        width: `${diameter}px`,
        height: `${diameter}px`,
      }}
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth={strokeWidth}
      ></circle>
      <path
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
}
