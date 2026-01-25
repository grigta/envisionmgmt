import type {
  WidgetConfig,
  StartConversationResponse,
  GetMessagesResponse,
  SendMessageResponse,
  ApiMessage,
  Message,
} from "@/types";

/** API base URL - configurable via environment or init */
let apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

/** Mock mode for testing without backend */
let mockMode = import.meta.env.VITE_MOCK_MODE === "true" ||
  new URLSearchParams(window.location.search).get("mock") === "true";

/**
 * Set API base URL
 */
export function setApiBaseUrl(url: string): void {
  apiBaseUrl = url.replace(/\/$/, "");
}

/**
 * Get API base URL
 */
export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

/**
 * Enable/disable mock mode
 */
export function setMockMode(enabled: boolean): void {
  mockMode = enabled;
}

/** Mock data for demo */
const mockConfig: WidgetConfig = {
  tenantId: "demo-tenant-id",
  tenantName: "Demo Company",
  primaryColor: "#0369a1",
  textColor: "#ffffff",
  backgroundColor: "#ffffff",
  position: "bottom_right",
  welcomeMessage: "Привет! Чем можем помочь?",
  placeholderText: "Напишите сообщение...",
  offlineMessage: "Сейчас мы не в сети. Оставьте сообщение.",
  requireEmail: false,
  requireName: false,
  showBranding: true,
  isOnline: true,
};

const mockMessages: Message[] = [];
let mockMessageId = 1;

/**
 * API client for widget endpoints
 */
class ApiClient {
  private getUrl(): string {
    return `${apiBaseUrl}/widget/v1`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.getUrl()}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get widget configuration by tenant slug
   */
  async getConfig(tenantSlug: string): Promise<WidgetConfig> {
    // Mock mode
    if (mockMode) {
      await this.delay(300);
      return { ...mockConfig, tenantName: tenantSlug || "Demo Company" };
    }

    const data = await this.request<{
      tenant_id: string;
      tenant_name: string;
      primary_color: string;
      text_color: string;
      background_color: string;
      position: string;
      welcome_message: string | null;
      placeholder_text: string;
      offline_message: string | null;
      require_email: boolean;
      require_name: boolean;
      show_branding: boolean;
      is_online: boolean;
    }>(`/config/${tenantSlug}`);

    return {
      tenantId: data.tenant_id,
      tenantName: data.tenant_name,
      primaryColor: data.primary_color,
      textColor: data.text_color,
      backgroundColor: data.background_color,
      position: data.position as WidgetConfig["position"],
      welcomeMessage: data.welcome_message,
      placeholderText: data.placeholder_text,
      offlineMessage: data.offline_message,
      requireEmail: data.require_email,
      requireName: data.require_name,
      showBranding: data.show_branding,
      isOnline: data.is_online,
    };
  }

  /**
   * Start a new conversation
   */
  async startConversation(
    tenantSlug: string,
    visitorId: string,
    data?: {
      name?: string;
      email?: string;
      initialMessage?: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<StartConversationResponse> {
    // Mock mode
    if (mockMode) {
      await this.delay(500);
      const conversationId = `conv-${Date.now()}`;
      const customerId = `cust-${Date.now()}`;

      // Add initial message if provided
      if (data?.initialMessage) {
        mockMessages.push({
          id: `msg-${mockMessageId++}`,
          senderType: "customer",
          contentType: "text",
          content: { text: data.initialMessage },
          createdAt: new Date().toISOString(),
        });

        // Simulate operator response after 2 seconds
        setTimeout(() => {
          mockMessages.push({
            id: `msg-${mockMessageId++}`,
            senderType: "operator",
            contentType: "text",
            content: { text: "Здравствуйте! Спасибо за обращение. Чем могу помочь?" },
            createdAt: new Date().toISOString(),
          });
        }, 2000);
      }

      return {
        conversation_id: conversationId,
        customer_id: customerId,
      };
    }

    return this.request<StartConversationResponse>(
      `/conversations?tenant_slug=${encodeURIComponent(tenantSlug)}`,
      {
        method: "POST",
        body: JSON.stringify({
          visitor_id: visitorId,
          name: data?.name,
          email: data?.email,
          initial_message: data?.initialMessage,
          metadata: data?.metadata || {},
        }),
      }
    );
  }

  /**
   * Get conversation messages
   */
  async getMessages(
    conversationId: string,
    options?: { after?: string; limit?: number }
  ): Promise<Message[]> {
    // Mock mode
    if (mockMode) {
      await this.delay(200);
      return [...mockMessages];
    }

    const params = new URLSearchParams();
    if (options?.after) params.set("after", options.after);
    if (options?.limit) params.set("limit", options.limit.toString());

    const query = params.toString() ? `?${params.toString()}` : "";
    const response = await this.request<GetMessagesResponse>(
      `/conversations/${conversationId}/messages${query}`
    );

    return response.messages.map(this.transformMessage);
  }

  /**
   * Send a message
   */
  async sendMessage(
    conversationId: string,
    content: string,
    contentType: string = "text"
  ): Promise<SendMessageResponse> {
    // Mock mode
    if (mockMode) {
      await this.delay(300);
      const messageId = `msg-${mockMessageId++}`;
      const createdAt = new Date().toISOString();

      // Add to mock messages
      mockMessages.push({
        id: messageId,
        senderType: "customer",
        contentType: "text",
        content: { text: content },
        createdAt,
      });

      // Simulate operator response after 1-3 seconds
      const responses = [
        "Понял вас, сейчас проверю.",
        "Отличный вопрос! Давайте разберёмся.",
        "Спасибо за информацию. Один момент...",
        "Хорошо, помогу вам с этим.",
      ];

      setTimeout(() => {
        mockMessages.push({
          id: `msg-${mockMessageId++}`,
          senderType: "operator",
          contentType: "text",
          content: { text: responses[Math.floor(Math.random() * responses.length)] },
          createdAt: new Date().toISOString(),
        });
      }, 1000 + Math.random() * 2000);

      return {
        message_id: messageId,
        created_at: createdAt,
      };
    }

    return this.request<SendMessageResponse>(
      `/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({
          content,
          content_type: contentType,
        }),
      }
    );
  }

  /**
   * Transform API message to internal format
   */
  private transformMessage(msg: ApiMessage): Message {
    return {
      id: msg.id,
      senderType: msg.sender_type as Message["senderType"],
      contentType: msg.content_type as Message["contentType"],
      content: msg.content,
      createdAt: msg.created_at,
    };
  }

  /**
   * Simulate network delay
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

export const api = new ApiClient();
