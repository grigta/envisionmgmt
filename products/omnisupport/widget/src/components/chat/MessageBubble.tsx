import { cn, formatTime } from "@/lib/utils";
import type { Message } from "@/types";
import { Avatar } from "@/components/ui";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isCustomer = message.senderType === "customer";
  const isBot = message.senderType === "bot";

  return (
    <div
      className={cn(
        "flex gap-2 max-w-[85%] animate-fade-in",
        isCustomer ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
    >
      {/* Avatar for operator/bot */}
      {!isCustomer && (
        <Avatar
          name={isBot ? "AI" : "Оператор"}
          size="sm"
          className="flex-shrink-0 mt-1"
        />
      )}

      {/* Message content */}
      <div
        className={cn(
          "rounded-2xl px-4 py-2.5",
          isCustomer
            ? "bg-[var(--omni-primary)] text-[var(--omni-text-on-primary)] rounded-br-sm"
            : "bg-[var(--omni-border-light)] text-[var(--omni-text)] rounded-bl-sm"
        )}
      >
        {/* Text content */}
        {message.content.text && (
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.content.text}
          </p>
        )}

        {/* Image content */}
        {message.contentType === "image" && message.content.url && (
          <img
            src={message.content.url}
            alt="Изображение"
            className="max-w-full rounded-lg mt-1"
          />
        )}

        {/* File content */}
        {message.contentType === "file" && message.content.url && (
          <a
            href={message.content.url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "flex items-center gap-2 mt-1 text-sm underline",
              isCustomer ? "text-white/90" : "text-[var(--omni-primary)]"
            )}
          >
            📎 {message.content.fileName || "Файл"}
          </a>
        )}

        {/* Timestamp */}
        <p
          className={cn(
            "text-[10px] mt-1 text-right",
            isCustomer ? "text-white/60" : "text-[var(--omni-text-muted)]"
          )}
        >
          {formatTime(message.createdAt)}
        </p>
      </div>
    </div>
  );
}
