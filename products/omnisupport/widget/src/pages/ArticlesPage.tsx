import { useState } from "react";
import { Search, ChevronRight, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWidgetStore } from "@/stores/widget.store";
import { WidgetHeader } from "@/components/layout";

// Mock articles data - in real app, this would come from API
const mockArticles = [
  {
    id: "1",
    title: "Как начать работу с OmniSupport",
    description: "Руководство по быстрому старту для новых пользователей",
    category: "Начало работы",
  },
  {
    id: "2",
    title: "Настройка каналов связи",
    description: "Подключение Telegram, WhatsApp и виджета на сайт",
    category: "Настройка",
  },
  {
    id: "3",
    title: "Работа с диалогами",
    description: "Как эффективно управлять обращениями клиентов",
    category: "Использование",
  },
  {
    id: "4",
    title: "Настройка AI-ассистента",
    description: "Обучение бота и настройка автоответов",
    category: "AI",
  },
  {
    id: "5",
    title: "Часто задаваемые вопросы",
    description: "Ответы на популярные вопросы пользователей",
    category: "FAQ",
  },
];

export function ArticlesPage() {
  const [search, setSearch] = useState("");
  const setView = useWidgetStore((state) => state.setView);

  const filteredArticles = mockArticles.filter(
    (article) =>
      article.title.toLowerCase().includes(search.toLowerCase()) ||
      article.description.toLowerCase().includes(search.toLowerCase())
  );

  const handleArticleClick = (_articleId: string) => {
    // In real app, navigate to article page
    // For now, just go back to chat
    setView("chat");
  };

  return (
    <>
      <WidgetHeader />

      <div className="flex-1 overflow-y-auto bg-[var(--omni-background)]">
        {/* Search */}
        <div className="p-4 bg-[var(--omni-surface)] border-b border-[var(--omni-border)]">
          <div className="relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--omni-text-muted)]"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по статьям..."
              className={cn(
                "w-full pl-9 pr-3 py-2 text-sm rounded-lg",
                "bg-[var(--omni-background)] text-[var(--omni-text)]",
                "border border-[var(--omni-border)]",
                "placeholder:text-[var(--omni-text-muted)]",
                "focus:outline-none focus:border-[var(--omni-primary)] focus:ring-2 focus:ring-[var(--omni-primary)]/10"
              )}
            />
          </div>
        </div>

        {/* Articles list */}
        <div className="p-2">
          {filteredArticles.length === 0 ? (
            <div className="text-center py-8">
              <FileText
                size={32}
                className="mx-auto text-[var(--omni-text-muted)] mb-3"
              />
              <p className="text-sm text-[var(--omni-text-muted)]">
                Статьи не найдены
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredArticles.map((article) => (
                <button
                  key={article.id}
                  onClick={() => handleArticleClick(article.id)}
                  className={cn(
                    "w-full p-3 rounded-lg text-left transition-colors",
                    "bg-[var(--omni-surface)] hover:bg-[var(--omni-border-light)]",
                    "border border-transparent hover:border-[var(--omni-border)]",
                    "flex items-center gap-3 group"
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <span className="text-xs text-[var(--omni-primary)] font-medium">
                      {article.category}
                    </span>
                    <h3 className="text-sm font-medium text-[var(--omni-text)] truncate">
                      {article.title}
                    </h3>
                    <p className="text-xs text-[var(--omni-text-muted)] truncate">
                      {article.description}
                    </p>
                  </div>
                  <ChevronRight
                    size={16}
                    className="text-[var(--omni-text-muted)] group-hover:text-[var(--omni-text)] transition-colors"
                  />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
