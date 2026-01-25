import { Avatar } from "@/components/ui";

interface TypingIndicatorProps {
  name?: string | null;
}

export function TypingIndicator({ name }: TypingIndicatorProps) {
  return (
    <div className="flex gap-2 max-w-[85%] mr-auto animate-fade-in">
      <Avatar name={name || "Оператор"} size="sm" className="flex-shrink-0 mt-1" />

      <div className="bg-[var(--omni-border-light)] text-[var(--omni-text-muted)] rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1">
          <span
            className="w-2 h-2 rounded-full bg-current animate-typing"
            style={{ animationDelay: "0s" }}
          />
          <span
            className="w-2 h-2 rounded-full bg-current animate-typing"
            style={{ animationDelay: "0.2s" }}
          />
          <span
            className="w-2 h-2 rounded-full bg-current animate-typing"
            style={{ animationDelay: "0.4s" }}
          />
        </div>
      </div>
    </div>
  );
}
