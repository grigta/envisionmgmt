import { useState } from "react";
import { CheckCircle } from "lucide-react";
import { useWidgetConfig } from "@/hooks";
import { useWidgetStore } from "@/stores/widget.store";
import { Button, Input, Textarea } from "@/components/ui";

export function OfflineForm() {
  const { offlineMessage } = useWidgetConfig();
  const config = useWidgetStore((state) => state.config);
  const setView = useWidgetStore((state) => state.setView);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Введите ваше имя";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Введите email";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Некорректный email";
    }

    if (!formData.message.trim()) {
      newErrors.message = "Введите сообщение";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      // TODO: API call to submit offline form
      // For now, simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIsSubmitted(true);
    } catch {
      // Handle error
    } finally {
      setIsSubmitting(false);
    }
  };

  // Success state
  if (isSubmitted) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[var(--omni-background)]">
        <div className="w-16 h-16 rounded-full bg-[var(--omni-success)]/10 flex items-center justify-center mb-4">
          <CheckCircle size={32} className="text-[var(--omni-success)]" />
        </div>
        <h3 className="text-lg font-semibold text-[var(--omni-text)] mb-2">
          Заявка отправлена
        </h3>
        <p className="text-sm text-[var(--omni-text-muted)] text-center mb-6">
          Мы свяжемся с вами в ближайшее время
        </p>
        <Button variant="secondary" onClick={() => setView("chat")}>
          Вернуться в чат
        </Button>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 bg-[var(--omni-background)]">
      <div className="max-w-sm mx-auto">
        {/* Offline message */}
        <div className="text-center mb-6 pt-4">
          <p className="text-sm text-[var(--omni-text-muted)] whitespace-pre-wrap">
            {offlineMessage || "Сейчас мы не в сети. Оставьте заявку и мы свяжемся с вами."}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Имя"
            placeholder="Как к вам обращаться?"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={errors.name}
            required
          />

          <Input
            type="email"
            label="Email"
            placeholder="your@email.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={errors.email}
            required
          />

          <Textarea
            label="Сообщение"
            placeholder="Опишите вашу проблему..."
            value={formData.message}
            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
            error={errors.message}
            rows={4}
            required
          />

          <Button
            type="submit"
            className="w-full"
            isLoading={isSubmitting}
          >
            Отправить заявку
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
