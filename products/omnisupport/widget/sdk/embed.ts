/**
 * OmniSupport Widget SDK
 *
 * Public API for embedding and controlling the widget.
 */

import { StrictMode, createElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { App } from "../src/App";
import { useWidgetStore } from "../src/stores/widget.store";
import { identifyVisitor } from "../src/lib/visitor";
import type { OmniSupportAPI, InitOptions, IdentifyData } from "../src/types";

// Event emitter for widget events
type EventCallback = (...args: unknown[]) => void;
const eventListeners: Map<string, Set<EventCallback>> = new Map();

function emit(event: string, ...args: unknown[]) {
  eventListeners.get(event)?.forEach((callback) => {
    try {
      callback(...args);
    } catch (error) {
      console.warn("[OmniSupport] Event callback error:", error);
    }
  });
}

// Widget state
let root: Root | null = null;
let container: HTMLElement | null = null;
let shadowRoot: ShadowRoot | null = null;
let isInitialized = false;

/**
 * Initialize the widget
 */
function init(tenantSlug: string, options: InitOptions = {}): void {
  if (isInitialized) {
    console.warn("[OmniSupport] Widget already initialized");
    return;
  }

  // Set API URL if provided
  if (options.locale) {
    // Handle locale if needed
  }

  // Create container with Shadow DOM for style isolation
  container = document.createElement("div");
  container.id = "omnisupport-widget-root";
  container.style.cssText = `
    position: fixed;
    z-index: ${options.zIndex || 9999};
    top: 0;
    left: 0;
    width: 0;
    height: 0;
  `;
  document.body.appendChild(container);

  // Create shadow root for style isolation
  shadowRoot = container.attachShadow({ mode: "open" });

  // Create inner container
  const innerContainer = document.createElement("div");
  innerContainer.id = "omnisupport-widget";
  innerContainer.className = "omni-widget";
  shadowRoot.appendChild(innerContainer);

  // Inject styles into shadow root
  const styleLink = document.createElement("link");
  styleLink.rel = "stylesheet";
  styleLink.href = getWidgetUrl() + "/widget.css";
  shadowRoot.insertBefore(styleLink, innerContainer);

  // Mount React app
  root = createRoot(innerContainer);
  root.render(createElement(StrictMode, null, createElement(App, { tenantSlug })));

  isInitialized = true;
  emit("ready");
}

/**
 * Open the widget
 */
function open(): void {
  if (!isInitialized) {
    console.warn("[OmniSupport] Widget not initialized");
    return;
  }
  useWidgetStore.getState().open();
  emit("open");
}

/**
 * Close the widget
 */
function close(): void {
  if (!isInitialized) {
    console.warn("[OmniSupport] Widget not initialized");
    return;
  }
  useWidgetStore.getState().close();
  emit("close");
}

/**
 * Toggle widget open/closed
 */
function toggle(): void {
  if (!isInitialized) {
    console.warn("[OmniSupport] Widget not initialized");
    return;
  }
  useWidgetStore.getState().toggle();
}

/**
 * Identify the user
 */
function identify(data: IdentifyData): void {
  if (!isInitialized) {
    console.warn("[OmniSupport] Widget not initialized");
    return;
  }

  // Update visitor data
  identifyVisitor(data);

  // Update store
  useWidgetStore.getState().identify(data);

  emit("identify", data);
}

/**
 * Subscribe to widget events
 */
function on(event: string, callback: EventCallback): void {
  if (!eventListeners.has(event)) {
    eventListeners.set(event, new Set());
  }
  eventListeners.get(event)!.add(callback);
}

/**
 * Unsubscribe from widget events
 */
function off(event: string, callback: EventCallback): void {
  eventListeners.get(event)?.delete(callback);
}

/**
 * Get widget URL from script src
 */
function getWidgetUrl(): string {
  const scripts = document.getElementsByTagName("script");
  for (let i = 0; i < scripts.length; i++) {
    const src = scripts[i].src;
    if (src.includes("omnisupport") || src.includes("widget")) {
      return src.replace(/\/[^/]+$/, "");
    }
  }
  return "https://widget.omnisupport.ru";
}

// Export public API
export const OmniSupport: OmniSupportAPI = {
  init,
  open,
  close,
  toggle,
  identify,
  on,
  off,
};

// Make available globally
if (typeof window !== "undefined") {
  (window as unknown as { OmniSupport: OmniSupportAPI }).OmniSupport = OmniSupport;
}

export default OmniSupport;
