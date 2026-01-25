import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMessages, useWidgetConfig, useWebSocket } from "@/hooks";
import { Button } from "@/components/ui";

export function MessageInput() {
  const [text, setText] = useState("");
  const { sendMessage, isSending } = useMessages();
  const { placeholderText } = useWidgetConfig();
  const { sendTyping } = useWebSocket();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSubmit = async () => {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    setText("");
    sendTyping(false);
    await sendMessage(trimmed);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (value: string) => {
    setText(value);

    // Send typing indicator
    sendTyping(true);

    // Clear typing after 2 seconds of no input
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      sendTyping(false);
    }, 2000);
  };

  return (
    <div className="flex-shrink-0 p-3 bg-[var(--omni-surface)] border-t border-[var(--omni-border)]">
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholderText}
          rows={1}
          className={cn(
            "flex-1 px-3 py-2 text-sm rounded-xl resize-none",
            "bg-[var(--omni-background)] text-[var(--omni-text)]",
            "border border-[var(--omni-border)]",
            "placeholder:text-[var(--omni-text-muted)]",
            "focus:outline-none focus:border-[var(--omni-primary)] focus:ring-2 focus:ring-[var(--omni-primary)]/10",
            "max-h-[120px]"
          )}
          disabled={isSending}
        />

        <Button
          onClick={handleSubmit}
          disabled={!text.trim() || isSending}
          size="icon"
          className="flex-shrink-0 w-10 h-10 rounded-xl"
          aria-label="Отправить"
        >
          <Send size={18} />
        </Button>
      </div>
    </div>
  );
}
