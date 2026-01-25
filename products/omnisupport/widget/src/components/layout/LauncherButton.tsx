import { MessageCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWidgetStore } from "@/stores/widget.store";

export function LauncherButton() {
  const isOpen = useWidgetStore((state) => state.isOpen);
  const toggle = useWidgetStore((state) => state.toggle);
  const config = useWidgetStore((state) => state.config);
  const messages = useWidgetStore((state) => state.messages);

  // Count unread messages (from operator/bot when widget is closed)
  const unreadCount = isOpen
    ? 0
    : messages.filter((m) => m.senderType !== "customer").length;

  const position = config?.position || "bottom_right";
  const positionClasses = {
    bottom_right: "bottom-5 right-5",
    bottom_left: "bottom-5 left-5",
    top_right: "top-5 right-5",
    top_left: "top-5 left-5",
  };

  return (
    <button
      onClick={toggle}
      className={cn(
        "fixed z-[9999] w-[var(--omni-launcher-size)] h-[var(--omni-launcher-size)]",
        "rounded-full shadow-lg transition-all duration-300",
        "flex items-center justify-center",
        "bg-[var(--omni-primary)] text-[var(--omni-text-on-primary)]",
        "hover:scale-110 hover:shadow-xl",
        "focus:outline-none focus-visible:ring-4 focus-visible:ring-[var(--omni-primary)]/30",
        positionClasses[position]
      )}
      aria-label={isOpen ? "Закрыть чат" : "Открыть чат"}
    >
      <div
        className={cn(
          "transition-transform duration-300",
          isOpen && "rotate-90"
        )}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </div>

      {/* Unread badge */}
      {unreadCount > 0 && !isOpen && (
        <span
          className={cn(
            "absolute -top-1 -right-1",
            "min-w-5 h-5 px-1.5 rounded-full",
            "bg-[var(--omni-error)] text-white text-xs font-bold",
            "flex items-center justify-center",
            "animate-bounce-in"
          )}
        >
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
    </button>
  );
}
