import type { VisitorData } from "@/types";
import { storage, STORAGE_KEYS } from "./storage";

/**
 * Generate a unique visitor ID
 */
function generateVisitorId(): string {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 10);
  return `v_${timestamp}_${randomPart}`;
}

/**
 * Get or create visitor data
 */
export function getVisitor(): VisitorData {
  const existing = storage.get<VisitorData>(STORAGE_KEYS.VISITOR);

  if (existing?.id) {
    return existing;
  }

  const visitor: VisitorData = {
    id: generateVisitorId(),
    createdAt: new Date().toISOString(),
  };

  storage.set(STORAGE_KEYS.VISITOR, visitor);
  return visitor;
}

/**
 * Update visitor data (e.g., after identification)
 */
export function updateVisitor(updates: Partial<VisitorData>): VisitorData {
  const current = getVisitor();
  const updated: VisitorData = {
    ...current,
    ...updates,
  };

  storage.set(STORAGE_KEYS.VISITOR, updated);
  return updated;
}

/**
 * Clear visitor data (for logout/reset)
 */
export function clearVisitor(): void {
  storage.remove(STORAGE_KEYS.VISITOR);
}

/**
 * Identify visitor with user data
 */
export function identifyVisitor(data: {
  email?: string;
  name?: string;
  metadata?: Record<string, unknown>;
}): VisitorData {
  return updateVisitor({
    email: data.email,
    name: data.name,
    metadata: data.metadata,
  });
}
