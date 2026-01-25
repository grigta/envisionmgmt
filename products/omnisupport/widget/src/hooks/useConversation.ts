import { useWidgetStore } from "@/stores/widget.store";

/**
 * Hook to manage conversation
 */
export function useConversation() {
  const conversation = useWidgetStore((state) => state.conversation);
  const isLoading = useWidgetStore((state) => state.isLoading);
  const error = useWidgetStore((state) => state.error);
  const startConversation = useWidgetStore((state) => state.startConversation);
  const prechatCompleted = useWidgetStore((state) => state.prechatCompleted);
  const completePrechat = useWidgetStore((state) => state.completePrechat);

  return {
    conversation,
    hasConversation: !!conversation,
    isLoading,
    error,
    startConversation,
    prechatCompleted,
    completePrechat,
  };
}
