import { ReactNode } from "react";

const COLOR_STYLES: Record<string, string> = {
  red: "bg-accent-red/10 text-accent-red",
  green: "bg-green-500/10 text-green-600",
  blue: "bg-blue-500/10 text-blue-600",
  orange: "bg-orange-500/10 text-orange-600",
  dark: "bg-dark/10 text-dark",
};

const SIZE_STYLES = {
  md: "w-9 h-9 rounded-lg",
  lg: "w-12 h-12 rounded-xl",
};

interface PanelIconProps {
  children: ReactNode;
  color?: keyof typeof COLOR_STYLES;
  size?: keyof typeof SIZE_STYLES;
}

export default function PanelIcon({ children, color = "red", size = "md" }: PanelIconProps) {
  return (
    <span className={`flex items-center justify-center shrink-0 ${SIZE_STYLES[size]} ${COLOR_STYLES[color]}`}>
      {children}
    </span>
  );
}
