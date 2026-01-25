/**
 * OmniSupport Widget Loader
 *
 * Lightweight loader script (< 2KB) that loads the main widget bundle.
 *
 * Usage:
 * <script>
 *   (function(w,d,s,o,f,js,fjs){
 *     w['OmniSupport']=o;w[o]=w[o]||function(){
 *     (w[o].q=w[o].q||[]).push(arguments)};
 *     js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
 *     js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
 *   }(window,document,'script','omni','https://widget.omnisupport.ru/loader.js'));
 *
 *   omni('init', 'my-company-slug');
 *   omni('identify', { email: 'user@example.com', name: 'Иван' });
 * </script>
 */

interface OmniCommand {
  method: string;
  args: unknown[];
}

interface OmniWindow extends Window {
  omni: {
    q?: OmniCommand[];
    (...args: unknown[]): void;
  };
  OmniSupportWidget?: {
    init: (tenantSlug: string, options?: Record<string, unknown>) => void;
    open: () => void;
    close: () => void;
    toggle: () => void;
    identify: (data: Record<string, unknown>) => void;
  };
}

declare const window: OmniWindow;

(function () {
  const WIDGET_URL =
    (import.meta.env?.VITE_WIDGET_URL as string) ||
    "https://widget.omnisupport.ru";

  let isLoaded = false;
  let tenantSlug: string | null = null;
  const pendingCommands: OmniCommand[] = [];

  // Process queued commands
  function processQueue() {
    const queue = window.omni.q || [];
    queue.forEach((cmd) => {
      executeCommand(cmd.method, cmd.args);
    });
    pendingCommands.forEach((cmd) => {
      executeCommand(cmd.method, cmd.args);
    });
  }

  // Execute a command
  function executeCommand(method: string, args: unknown[]) {
    if (!isLoaded && method !== "init") {
      pendingCommands.push({ method, args });
      return;
    }

    switch (method) {
      case "init":
        tenantSlug = args[0] as string;
        loadWidget(tenantSlug, args[1] as Record<string, unknown> | undefined);
        break;

      case "open":
        window.OmniSupportWidget?.open();
        break;

      case "close":
        window.OmniSupportWidget?.close();
        break;

      case "toggle":
        window.OmniSupportWidget?.toggle();
        break;

      case "identify":
        window.OmniSupportWidget?.identify(args[0] as Record<string, unknown>);
        break;

      default:
        console.warn(`[OmniSupport] Unknown command: ${method}`);
    }
  }

  // Load the main widget bundle
  function loadWidget(
    slug: string,
    _options?: Record<string, unknown>
  ) {
    // Create container
    const container = document.createElement("div");
    container.id = "omnisupport-widget";
    container.dataset.tenant = slug;
    document.body.appendChild(container);

    // Load CSS
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = `${WIDGET_URL}/widget.css`;
    document.head.appendChild(css);

    // Load JS
    const script = document.createElement("script");
    script.src = `${WIDGET_URL}/widget.js`;
    script.async = true;
    script.onload = () => {
      isLoaded = true;
      processQueue();
    };
    script.onerror = () => {
      console.error("[OmniSupport] Failed to load widget");
    };
    document.body.appendChild(script);
  }

  // Replace queue function with command executor
  window.omni = function (...args: unknown[]) {
    const method = args[0] as string;
    const cmdArgs = args.slice(1);
    executeCommand(method, cmdArgs);
  };

  // Process any commands that were queued before loader loaded
  if (window.omni.q) {
    processQueue();
  }
})();
