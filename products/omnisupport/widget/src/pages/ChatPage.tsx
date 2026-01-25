import { useConversation, useWidgetConfig } from "@/hooks";
import { useWidgetStore } from "@/stores/widget.store";
import { WidgetHeader } from "@/components/layout";
import { ChatMessages, MessageInput } from "@/components/chat";
import { PrechatForm } from "@/components/forms";
import { Spinner } from "@/components/ui";

export function ChatPage() {
  const { hasConversation, prechatCompleted, isLoading } = useConversation();
  const { requiresEmail, requiresName, isOnline } = useWidgetConfig();
  const setView = useWidgetStore((state) => state.setView);
  const completePrechat = useWidgetStore((state) => state.completePrechat);

  // Show loading state
  if (isLoading && !hasConversation) {
    return (
      <>
        <WidgetHeader />
        <div className="flex-1 flex items-center justify-center bg-[var(--omni-background)]">
          <Spinner size="lg" />
        </div>
      </>
    );
  }

  // Show offline form if not online
  if (!isOnline) {
    setView("offline");
    return null;
  }

  // Show prechat form if required and not completed
  const needsPrechat = (requiresEmail || requiresName) && !prechatCompleted && !hasConversation;

  if (needsPrechat) {
    return (
      <>
        <WidgetHeader />
        <PrechatForm onComplete={completePrechat} />
      </>
    );
  }

  // Show chat
  return (
    <>
      <WidgetHeader />
      <ChatMessages />
      <MessageInput />
    </>
  );
}
