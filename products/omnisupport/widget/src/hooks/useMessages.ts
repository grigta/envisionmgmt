import { useWidgetStore } from "@/stores/widget.store";

/**
 * Hook to manage messages
 */
export function useMessages() {
  const messages = useWidgetStore((state) => state.messages);
  const isTyping = useWidgetStore((state) => state.isTyping);
  const typingName = useWidgetStore((state) => state.typingName);
  const isSending = useWidgetStore((state) => state.isSending);
  const sendMessage = useWidgetStore((state) => state.sendMessage);
  const loadMessages = useWidgetStore((state) => state.loadMessages);

  return {
    messages,
    isTyping,
    typingName,
    isSending,
    sendMessage,
    loadMessages,
    hasMessages: messages.length > 0,
  };
}
