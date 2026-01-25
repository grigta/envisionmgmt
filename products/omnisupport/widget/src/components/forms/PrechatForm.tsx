import { useState } from "react";
import { useConversation, useWidgetConfig } from "@/hooks";
import { useWidgetStore } from "@/stores/widget.store";
import { Button, Input, Textarea } from "@/components/ui";

interface PrechatFormProps {
  onComplete: () => void;
}

export function PrechatForm({ onComplete }: PrechatFormProps) {
  const { startConversation, isLoading, error } = useConversation();
  const { requiresEmail, requiresName, welcomeMessage } = useWidgetConfig();
  const config = useWidgetStore((state) => state.config);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (requiresName && !formData.name.trim()) {
      newErrors.name = "Введите ваше имя";
    }

    if (requiresEmail) {
      if (!formData.email.trim()) {
        newErrors.email = "Введите email";
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = "Некорректный email";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      await startConversation({
        name: formData.name || undefined,
        email: formData.email || undefined,
        initialMessage: formData.message || undefined,
      });
      onComplete();
    } catch {
      // Error is handled in store
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 bg-[var(--omni-background)]">
      <div className="max-w-sm mx-auto">
        {/* Welcome message */}
        {welcomeMessage && (
          <div className="text-center mb-6 pt-4">
            <p className="text-sm text-[var(--omni-text-muted)] whitespace-pre-wrap">
              {welcomeMessage}
            </p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name field */}
          <Input
            label="Имя"
            placeholder="Как к вам обращаться?"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={errors.name}
            required={requiresName}
          />

          {/* Email field */}
          <Input
            type="email"
            label="Email"
            placeholder="your@email.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={errors.email}
            required={requiresEmail}
          />

          {/* Message field */}
          <Textarea
            label="Сообщение"
            placeholder="Чем можем помочь?"
            value={formData.message}
            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
            rows={3}
          />

          {/* Error message */}
          {error && (
            <p className="text-sm text-[var(--omni-error)] text-center">
              {error}
            </p>
          )}

          {/* Submit button */}
          <Button
            type="submit"
            className="w-full"
            isLoading={isLoading}
          >
            Начать чат
          </Button>
        </form>

        {/* Branding */}
        {config?.showBranding && (
          <p className="text-center text-xs text-[var(--omni-text-muted)] mt-6">
            Powered by{" "}
            <a
              href="https://omnisupport.ru"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--omni-primary)] hover:underline"
            >
              OmniSupport
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
