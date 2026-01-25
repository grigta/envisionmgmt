import { useWidgetStore } from "@/stores/widget.store";

/**
 * Hook to access widget configuration
 */
export function useWidgetConfig() {
  const config = useWidgetStore((state) => state.config);
  const isLoading = useWidgetStore((state) => state.isLoading);
  const error = useWidgetStore((state) => state.error);

  return {
    config,
    isLoading,
    error,
    isOnline: config?.isOnline ?? false,
    requiresEmail: config?.requireEmail ?? false,
    requiresName: config?.requireName ?? false,
    welcomeMessage: config?.welcomeMessage,
    placeholderText: config?.placeholderText ?? "Напишите сообщение...",
    offlineMessage: config?.offlineMessage,
    showBranding: config?.showBranding ?? true,
  };
}
