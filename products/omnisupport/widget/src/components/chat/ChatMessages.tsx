import { useEffect, useRef } from "react";
import { useMessages, useWidgetConfig } from "@/hooks";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { Spinner } from "@/components/ui";

export function ChatMessages() {
  const { messages, isTyping, typingName } = useMessages();
  const { welcomeMessage, isLoading } = useWidgetConfig();
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto p-4 space-y-3 bg-[var(--omni-background)]"
    >
      {/* Welcome message */}
      {welcomeMessage && messages.length === 0 && (
        <div className="text-center py-6">
          <p className="text-sm text-[var(--omni-text-muted)] whitespace-pre-wrap">
            {welcomeMessage}
          </p>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Typing indicator */}
      {isTyping && <TypingIndicator name={typingName} />}
    </div>
  );
}
