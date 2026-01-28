import { X, ChevronLeft, FileText, MessageCircle, Sun, Moon, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWidgetStore } from "@/stores/widget.store";
import { Avatar } from "@/components/ui";

interface WidgetHeaderProps {
  showBack?: boolean;
  onBack?: () => void;
}

export function WidgetHeader({ showBack, onBack }: WidgetHeaderProps) {
  const config = useWidgetStore((state) => state.config);
  const close = useWidgetStore((state) => state.close);
  const currentView = useWidgetStore((state) => state.currentView);
  const setView = useWidgetStore((state) => state.setView);
  const theme = useWidgetStore((state) => state.theme);
  const toggleTheme = useWidgetStore((state) => state.toggleTheme);

  const ThemeIcon = theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;
  const themeLabel = theme === "light" ? "Светлая тема" : theme === "dark" ? "Тёмная тема" : "Системная тема";

  const titles: Record<string, string> = {
    chat: "Чат",
    articles: "Справка",
    article: "Статья",
    offline: "Оставить заявку",
  };

  return (
    <header
      className={cn(
        "flex-shrink-0 h-14 px-4",
        "bg-[var(--omni-primary)] text-[var(--omni-text-on-primary)]",
        "flex items-center gap-3"
      )}
    >
      {/* Back button */}
      {showBack && onBack && (
        <button
          onClick={onBack}
          className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          aria-label="Назад"
        >
          <ChevronLeft size={20} />
        </button>
      )}

      {/* Logo/Avatar */}
      {!showBack && (
        <Avatar
          name={config?.tenantName}
          size="sm"
          className="bg-white/20 text-white"
        />
      )}

      {/* Title */}
      <div className="flex-1 min-w-0">
        <h2 className="font-semibold truncate">
          {showBack ? titles[currentView] : config?.tenantName || "Поддержка"}
        </h2>
        {!showBack && config?.isOnline && (
          <p className="text-xs opacity-80 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            Онлайн
          </p>
        )}
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center gap-1">
        {currentView === "chat" && (
          <button
            onClick={() => setView("articles")}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="Справка"
          >
            <FileText size={18} />
          </button>
        )}

        {currentView === "articles" && (
          <button
            onClick={() => setView("chat")}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="Чат"
          >
            <MessageCircle size={18} />
          </button>
        )}

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          aria-label={themeLabel}
          title={themeLabel}
        >
          <ThemeIcon size={18} />
        </button>

        {/* Close button */}
        <button
          onClick={close}
          className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          aria-label="Закрыть"
        >
          <X size={18} />
        </button>
      </div>
    </header>
  );
}
