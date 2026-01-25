import { useWidgetStore } from "@/stores/widget.store";
import { WidgetHeader } from "@/components/layout";

interface ArticlePageProps {
  articleId: string;
}

export function ArticlePage({ articleId }: ArticlePageProps) {
  const setView = useWidgetStore((state) => state.setView);

  // Mock article content - in real app, fetch from API
  const article = {
    id: articleId,
    title: "Как начать работу с OmniSupport",
    content: `
# Добро пожаловать в OmniSupport!

OmniSupport — это омниканальная платформа для поддержки клиентов.

## Быстрый старт

1. **Создайте аккаунт** — зарегистрируйтесь на нашем сайте
2. **Настройте каналы** — подключите Telegram, WhatsApp или виджет
3. **Пригласите команду** — добавьте операторов поддержки
4. **Начните работу** — отвечайте на обращения клиентов

## Нужна помощь?

Наша команда поддержки всегда готова помочь. Напишите нам в чат!
    `.trim(),
  };

  return (
    <>
      <WidgetHeader showBack onBack={() => setView("articles")} />

      <div className="flex-1 overflow-y-auto p-4 bg-[var(--omni-background)]">
        <article className="prose prose-sm max-w-none">
          <h1 className="text-lg font-semibold text-[var(--omni-text)] mb-4">
            {article.title}
          </h1>

          <div className="text-sm text-[var(--omni-text)] whitespace-pre-wrap leading-relaxed">
            {/* Simple markdown-like rendering */}
            {article.content.split("\n").map((line, i) => {
              if (line.startsWith("# ")) {
                return (
                  <h1
                    key={i}
                    className="text-lg font-bold text-[var(--omni-text)] mt-4 mb-2"
                  >
                    {line.slice(2)}
                  </h1>
                );
              }
              if (line.startsWith("## ")) {
                return (
                  <h2
                    key={i}
                    className="text-base font-semibold text-[var(--omni-text)] mt-4 mb-2"
                  >
                    {line.slice(3)}
                  </h2>
                );
              }
              if (line.match(/^\d+\./)) {
                return (
                  <p key={i} className="ml-4 mb-1">
                    {line}
                  </p>
                );
              }
              if (line.trim() === "") {
                return <br key={i} />;
              }
              return (
                <p key={i} className="mb-2">
                  {line}
                </p>
              );
            })}
          </div>
        </article>
      </div>
    </>
  );
}
