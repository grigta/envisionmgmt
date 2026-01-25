import { useEffect } from "react";
import { useWidgetStore } from "@/stores/widget.store";
import { LauncherButton, WidgetContainer } from "@/components/layout";
import { ChatPage, ArticlesPage, ArticlePage, OfflineFormPage } from "@/pages";
import { Spinner } from "@/components/ui";

interface AppProps {
  tenantSlug: string;
}

export function App({ tenantSlug }: AppProps) {
  const init = useWidgetStore((state) => state.init);
  const isLoading = useWidgetStore((state) => state.isLoading);
  const error = useWidgetStore((state) => state.error);
  const currentView = useWidgetStore((state) => state.currentView);
  const config = useWidgetStore((state) => state.config);

  // Initialize widget on mount
  useEffect(() => {
    init(tenantSlug);
  }, [tenantSlug, init]);

  // Show nothing if loading initial config
  if (isLoading && !config) {
    return (
      <>
        <LauncherButton />
        <WidgetContainer>
          <div className="flex-1 flex items-center justify-center">
            <Spinner size="lg" />
          </div>
        </WidgetContainer>
      </>
    );
  }

  // Show error if config failed to load
  if (error && !config) {
    return (
      <>
        <LauncherButton />
        <WidgetContainer>
          <div className="flex-1 flex items-center justify-center p-6">
            <p className="text-sm text-[var(--omni-error)] text-center">{error}</p>
          </div>
        </WidgetContainer>
      </>
    );
  }

  // Render current view
  const renderView = () => {
    switch (currentView) {
      case "chat":
        return <ChatPage />;
      case "articles":
        return <ArticlesPage />;
      case "article":
        return <ArticlePage articleId="1" />;
      case "offline":
        return <OfflineFormPage />;
      default:
        return <ChatPage />;
    }
  };

  return (
    <>
      <LauncherButton />
      <WidgetContainer>{renderView()}</WidgetContainer>
    </>
  );
}
