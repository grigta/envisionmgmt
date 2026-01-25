import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useWidgetStore } from "@/stores/widget.store";

interface WidgetContainerProps {
  children: ReactNode;
}

export function WidgetContainer({ children }: WidgetContainerProps) {
  const isOpen = useWidgetStore((state) => state.isOpen);
  const config = useWidgetStore((state) => state.config);

  const position = config?.position || "bottom_right";

  const positionClasses = {
    bottom_right: "bottom-24 right-5",
    bottom_left: "bottom-24 left-5",
    top_right: "top-24 right-5",
    top_left: "top-24 left-5",
  };

  const transformOrigin = {
    bottom_right: "bottom right",
    bottom_left: "bottom left",
    top_right: "top right",
    top_left: "top left",
  };

  if (!isOpen) return null;

  return (
    <div
      className={cn(
        "omni-widget fixed z-[9998]",
        "w-[var(--omni-widget-width)] h-[var(--omni-widget-height)]",
        "max-w-[calc(100vw-40px)] max-h-[calc(100vh-120px)]",
        "bg-[var(--omni-surface)] rounded-2xl shadow-2xl",
        "flex flex-col overflow-hidden",
        "animate-slide-up",
        positionClasses[position]
      )}
      style={{ transformOrigin: transformOrigin[position] }}
      role="dialog"
      aria-label="Чат поддержки"
    >
      {children}
    </div>
  );
}
