/** Widget configuration from backend */
export interface WidgetConfig {
  tenantId: string;
  tenantName: string;
  primaryColor: string;
  textColor: string;
  backgroundColor: string;
  position: WidgetPosition;
  welcomeMessage: string | null;
  placeholderText: string;
  offlineMessage: string | null;
  requireEmail: boolean;
  requireName: boolean;
  showBranding: boolean;
  isOnline: boolean;
}

export type WidgetPosition = "bottom_right" | "bottom_left" | "top_right" | "top_left";

/** Visitor data stored in localStorage */
export interface VisitorData {
  id: string;
  name?: string;
  email?: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

/** Conversation */
export interface Conversation {
  id: string;
  customerId: string;
  createdAt: string;
}

/** Message from API */
export interface Message {
  id: string;
  senderType: "customer" | "operator" | "bot";
  contentType: "text" | "image" | "file";
  content: MessageContent;
  createdAt: string;
}

export interface MessageContent {
  text?: string;
  url?: string;
  fileName?: string;
  mimeType?: string;
}

/** API Responses */
export interface StartConversationResponse {
  conversation_id: string;
  customer_id: string;
}

export interface GetMessagesResponse {
  messages: ApiMessage[];
}

export interface ApiMessage {
  id: string;
  sender_type: string;
  content_type: string;
  content: MessageContent;
  created_at: string;
}

export interface SendMessageResponse {
  message_id: string;
  created_at: string;
}

/** Prechat form field */
export interface PrechatField {
  name: string;
  label: string;
  type: "text" | "email" | "tel" | "textarea";
  required: boolean;
  placeholder?: string;
}

/** Prechat form data */
export interface PrechatFormData {
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
  [key: string]: string | undefined;
}

/** WebSocket events */
export type WSEventType =
  | "message"
  | "typing_start"
  | "typing_stop"
  | "conversation_closed"
  | "operator_joined";

export interface WSEvent {
  type: WSEventType;
  data: unknown;
}

export interface WSMessageEvent {
  type: "message";
  data: {
    id: string;
    sender_type: string;
    content_type: string;
    content: MessageContent;
    created_at: string;
  };
}

export interface WSTypingEvent {
  type: "typing_start" | "typing_stop";
  data: {
    sender_type: string;
    sender_name?: string;
  };
}

/** Widget SDK public API */
export interface OmniSupportAPI {
  init: (tenantSlug: string, options?: InitOptions) => void;
  open: () => void;
  close: () => void;
  toggle: () => void;
  identify: (userData: IdentifyData) => void;
  on: (event: string, callback: (...args: unknown[]) => void) => void;
  off: (event: string, callback: (...args: unknown[]) => void) => void;
}

export interface InitOptions {
  position?: WidgetPosition;
  zIndex?: number;
  locale?: string;
}

export interface IdentifyData {
  email?: string;
  name?: string;
  phone?: string;
  metadata?: Record<string, unknown>;
}
