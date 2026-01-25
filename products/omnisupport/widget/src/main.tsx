import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./index.css";

// Get tenant slug from URL or data attribute
function getTenantSlug(): string {
  // Try URL path: /widget/:tenantSlug
  const pathMatch = window.location.pathname.match(/\/widget\/([^\/]+)/);
  if (pathMatch) {
    return pathMatch[1];
  }

  // Try data attribute
  const container = document.getElementById("omnisupport-widget");
  const slug = container?.dataset.tenant;
  if (slug) {
    return slug;
  }

  // Try query param
  const params = new URLSearchParams(window.location.search);
  const querySlug = params.get("tenant");
  if (querySlug) {
    return querySlug;
  }

  // Default for development
  return "demo";
}

// Initialize widget
const tenantSlug = getTenantSlug();
const container = document.getElementById("omnisupport-widget");

if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <App tenantSlug={tenantSlug} />
    </StrictMode>
  );
}

// Export for SDK use
export { App };
export { useWidgetStore } from "./stores/widget.store";
export { setApiBaseUrl } from "./lib/api";
