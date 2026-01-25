import type { WSEvent, WSMessageEvent, Message } from "@/types";
import { getApiBaseUrl } from "./api";

type EventCallback = (data: unknown) => void;

interface WebSocketManagerOptions {
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

/**
 * WebSocket manager with auto-reconnect
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private conversationId: string | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private pingTimeout: ReturnType<typeof setTimeout> | null = null;
  private isConnecting = false;
  private shouldReconnect = true;

  private options: Required<WebSocketManagerOptions> = {
    reconnectDelay: 1000,
    maxReconnectAttempts: 10,
    pingInterval: 30000,
  };

  constructor(options?: WebSocketManagerOptions) {
    if (options) {
      this.options = { ...this.options, ...options };
    }
  }

  /**
   * Connect to WebSocket for a conversation
   */
  connect(conversationId: string): void {
    if (this.isConnecting || (this.ws && this.conversationId === conversationId)) {
      return;
    }

    this.disconnect();
    this.conversationId = conversationId;
    this.shouldReconnect = true;
    this.doConnect();
  }

  private doConnect(): void {
    if (!this.conversationId || this.isConnecting) return;

    this.isConnecting = true;

    const baseUrl = getApiBaseUrl();
    const wsUrl = baseUrl.replace(/^http/, "ws");
    const url = `${wsUrl}/widget/v1/conversations/${this.conversationId}/ws`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.emit("connected", null);
        this.startPing();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSEvent;
          this.handleMessage(data);
        } catch {
          console.warn("[OmniSupport] Failed to parse WebSocket message");
        }
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.stopPing();
        this.emit("disconnected", null);

        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        this.isConnecting = false;
        console.warn("[OmniSupport] WebSocket error:", error);
        this.emit("error", error);
      };
    } catch (error) {
      this.isConnecting = false;
      console.warn("[OmniSupport] Failed to create WebSocket:", error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.stopPing();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.conversationId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Send data through WebSocket
   */
  send(data: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Send typing indicator
   */
  sendTyping(isTyping: boolean): void {
    this.send({
      type: isTyping ? "typing_start" : "typing_stop",
    });
  }

  /**
   * Subscribe to events
   */
  on(event: string, callback: EventCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  /**
   * Unsubscribe from events
   */
  off(event: string, callback: EventCallback): void {
    this.listeners.get(event)?.delete(callback);
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  private handleMessage(event: WSEvent): void {
    this.emit(event.type, event.data);

    // Also emit generic "message" event for new messages
    if (event.type === "message") {
      const msgEvent = event as WSMessageEvent;
      const message: Message = {
        id: msgEvent.data.id,
        senderType: msgEvent.data.sender_type as Message["senderType"],
        contentType: msgEvent.data.content_type as Message["contentType"],
        content: msgEvent.data.content,
        createdAt: msgEvent.data.created_at,
      };
      this.emit("new_message", message);
    }
  }

  private emit(event: string, data: unknown): void {
    this.listeners.get(event)?.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.warn("[OmniSupport] Event callback error:", error);
      }
    });
  }

  private scheduleReconnect(): void {
    if (
      this.reconnectAttempts >= this.options.maxReconnectAttempts ||
      !this.shouldReconnect
    ) {
      this.emit("reconnect_failed", null);
      return;
    }

    const delay = Math.min(
      this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      30000
    );

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.emit("reconnecting", { attempt: this.reconnectAttempts });
      this.doConnect();
    }, delay);
  }

  private startPing(): void {
    this.pingTimeout = setInterval(() => {
      this.send({ type: "ping" });
    }, this.options.pingInterval);
  }

  private stopPing(): void {
    if (this.pingTimeout) {
      clearInterval(this.pingTimeout);
      this.pingTimeout = null;
    }
  }
}

// Singleton instance
export const wsManager = new WebSocketManager();
