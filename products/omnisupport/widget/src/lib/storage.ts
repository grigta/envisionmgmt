const STORAGE_PREFIX = "omni_";

/**
 * Safe localStorage wrapper with JSON serialization
 */
export const storage = {
  /**
   * Get item from localStorage
   */
  get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(STORAGE_PREFIX + key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },

  /**
   * Set item in localStorage
   */
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
    } catch {
      // localStorage might be full or disabled
      console.warn("[OmniSupport] Failed to save to localStorage");
    }
  },

  /**
   * Remove item from localStorage
   */
  remove(key: string): void {
    try {
      localStorage.removeItem(STORAGE_PREFIX + key);
    } catch {
      // Ignore errors
    }
  },

  /**
   * Clear all widget-related items
   */
  clear(): void {
    try {
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(STORAGE_PREFIX)) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach((key) => localStorage.removeItem(key));
    } catch {
      // Ignore errors
    }
  },
};

/** Storage keys */
export const STORAGE_KEYS = {
  VISITOR: "visitor",
  CONVERSATION: "conversation",
  MESSAGES: "messages",
  PRECHAT_COMPLETED: "prechat_completed",
} as const;
