import { create } from "zustand";
import type { WidgetConfig, Message, Conversation, VisitorData } from "@/types";
import { storage, STORAGE_KEYS } from "@/lib/storage";
import { getVisitor, updateVisitor } from "@/lib/visitor";
import { api } from "@/lib/api";
import { wsManager } from "@/lib/websocket";
import { adjustColor } from "@/lib/utils";

interface WidgetState {
  // UI State
  isOpen: boolean;
  isLoading: boolean;
  error: string | null;
  currentView: "chat" | "articles" | "article" | "offline";

  // Config
  tenantSlug: string | null;
  config: WidgetConfig | null;

  // Visitor
  visitor: VisitorData | null;

  // Conversation
  conversation: Conversation | null;
  messages: Message[];
  isTyping: boolean;
  typingName: string | null;
  isSending: boolean;

  // Prechat
  prechatCompleted: boolean;

  // Actions
  init: (tenantSlug: string) => Promise<void>;
  open: () => void;
  close: () => void;
  toggle: () => void;
  setView: (view: WidgetState["currentView"]) => void;

  // Visitor actions
  identify: (data: { email?: string; name?: string; metadata?: Record<string, unknown> }) => void;

  // Conversation actions
  startConversation: (data?: { name?: string; email?: string; initialMessage?: string }) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  loadMessages: () => Promise<void>;
  addMessage: (message: Message) => void;
  setTyping: (isTyping: boolean, name?: string) => void;

  // Prechat
  completePrechat: () => void;

  // Internal
  applyTheme: (config: WidgetConfig) => void;
}

export const useWidgetStore = create<WidgetState>((set, get) => ({
  // Initial state
  isOpen: false,
  isLoading: false,
  error: null,
  currentView: "chat",

  tenantSlug: null,
  config: null,

  visitor: null,

  conversation: null,
  messages: [],
  isTyping: false,
  typingName: null,
  isSending: false,

  prechatCompleted: false,

  // Initialize widget
  init: async (tenantSlug: string) => {
    set({ isLoading: true, error: null, tenantSlug });

    try {
      // Load visitor
      const visitor = getVisitor();
      set({ visitor });

      // Load config from API
      const config = await api.getConfig(tenantSlug);
      set({ config });

      // Apply theme colors
      get().applyTheme(config);

      // Check for existing conversation
      const savedConversation = storage.get<Conversation>(STORAGE_KEYS.CONVERSATION);
      if (savedConversation) {
        set({ conversation: savedConversation });

        // Load messages
        try {
          const messages = await api.getMessages(savedConversation.id);
          set({ messages });

          // Connect WebSocket
          wsManager.connect(savedConversation.id);
        } catch {
          // Conversation might be invalid, clear it
          storage.remove(STORAGE_KEYS.CONVERSATION);
          set({ conversation: null, messages: [] });
        }
      }

      // Check prechat status
      const prechatCompleted = storage.get<boolean>(STORAGE_KEYS.PRECHAT_COMPLETED) || false;
      set({ prechatCompleted });

      // Setup WebSocket listeners
      wsManager.on("new_message", (message) => {
        get().addMessage(message as Message);
      });

      wsManager.on("typing_start", (data: unknown) => {
        const typingData = data as { sender_name?: string };
        get().setTyping(true, typingData.sender_name);
      });

      wsManager.on("typing_stop", () => {
        get().setTyping(false);
      });

      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to initialize widget";
      set({ isLoading: false, error: message });
    }
  },

  // UI actions
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  setView: (currentView) => set({ currentView }),

  // Identify visitor
  identify: (data) => {
    const visitor = updateVisitor(data);
    set({ visitor });
  },

  // Start conversation
  startConversation: async (data) => {
    const { tenantSlug, visitor } = get();
    if (!tenantSlug || !visitor) return;

    set({ isLoading: true, error: null });

    try {
      const response = await api.startConversation(tenantSlug, visitor.id, data);

      const conversation: Conversation = {
        id: response.conversation_id,
        customerId: response.customer_id,
        createdAt: new Date().toISOString(),
      };

      // Save conversation
      storage.set(STORAGE_KEYS.CONVERSATION, conversation);
      set({ conversation });

      // Update visitor if data provided
      if (data?.name || data?.email) {
        updateVisitor({ name: data.name, email: data.email });
      }

      // Add initial message if sent
      if (data?.initialMessage) {
        const message: Message = {
          id: crypto.randomUUID(),
          senderType: "customer",
          contentType: "text",
          content: { text: data.initialMessage },
          createdAt: new Date().toISOString(),
        };
        set({ messages: [message] });
      }

      // Connect WebSocket (or start polling in mock mode)
      wsManager.connect(conversation.id);

      // Start message polling for mock mode
      startMessagePolling(conversation.id, get, set);

      set({ isLoading: false, prechatCompleted: true });
      storage.set(STORAGE_KEYS.PRECHAT_COMPLETED, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to start conversation";
      set({ isLoading: false, error: message });
    }
  },

  // Send message
  sendMessage: async (content: string) => {
    const { conversation, messages } = get();
    if (!conversation) return;

    // Create optimistic message
    const tempId = crypto.randomUUID();
    const optimisticMessage: Message = {
      id: tempId,
      senderType: "customer",
      contentType: "text",
      content: { text: content },
      createdAt: new Date().toISOString(),
    };

    set({
      messages: [...messages, optimisticMessage],
      isSending: true,
    });

    try {
      const response = await api.sendMessage(conversation.id, content);

      // Update message with real ID
      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === tempId
            ? { ...m, id: response.message_id, createdAt: response.created_at }
            : m
        ),
        isSending: false,
      }));
    } catch (error) {
      // Remove optimistic message on error
      set((state) => ({
        messages: state.messages.filter((m) => m.id !== tempId),
        isSending: false,
        error: error instanceof Error ? error.message : "Failed to send message",
      }));
    }
  },

  // Load messages
  loadMessages: async () => {
    const { conversation } = get();
    if (!conversation) return;

    try {
      const messages = await api.getMessages(conversation.id);
      set({ messages });
    } catch (error) {
      console.warn("[OmniSupport] Failed to load messages:", error);
    }
  },

  // Add message (from WebSocket)
  addMessage: (message: Message) => {
    set((state) => {
      // Avoid duplicates
      if (state.messages.some((m) => m.id === message.id)) {
        return state;
      }
      return { messages: [...state.messages, message] };
    });
  },

  // Set typing indicator
  setTyping: (isTyping: boolean, name?: string) => {
    set({ isTyping, typingName: name || null });
  },

  // Complete prechat
  completePrechat: () => {
    set({ prechatCompleted: true });
    storage.set(STORAGE_KEYS.PRECHAT_COMPLETED, true);
  },

  // Apply theme from config
  applyTheme: (config: WidgetConfig) => {
    const root = document.documentElement;

    root.style.setProperty("--omni-primary", config.primaryColor);
    root.style.setProperty("--omni-primary-hover", adjustColor(config.primaryColor, -15));
    root.style.setProperty("--omni-text-on-primary", config.textColor);
    root.style.setProperty("--omni-surface", config.backgroundColor);
  },
}));

// Message polling for mock mode (since WebSocket doesn't work with mocks)
let pollingInterval: ReturnType<typeof setInterval> | null = null;

function startMessagePolling(
  conversationId: string,
  get: () => WidgetState,
  set: (state: Partial<WidgetState>) => void
) {
  // Clear existing polling
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }

  // Poll every 1 second
  pollingInterval = setInterval(async () => {
    try {
      const messages = await api.getMessages(conversationId);
      const currentMessages = get().messages;

      // Only update if there are new messages
      if (messages.length > currentMessages.length) {
        set({ messages });
      }
    } catch {
      // Ignore polling errors
    }
  }, 1000);
}
