import { useEffect, useState, useCallback } from "react";
import { wsManager } from "@/lib/websocket";
import { useWidgetStore } from "@/stores/widget.store";

/**
 * Hook to manage WebSocket connection
 */
export function useWebSocket() {
  const conversation = useWidgetStore((state) => state.conversation);
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  useEffect(() => {
    if (!conversation) {
      setIsConnected(false);
      return;
    }

    const handleConnected = () => {
      setIsConnected(true);
      setIsReconnecting(false);
    };

    const handleDisconnected = () => {
      setIsConnected(false);
    };

    const handleReconnecting = () => {
      setIsReconnecting(true);
    };

    wsManager.on("connected", handleConnected);
    wsManager.on("disconnected", handleDisconnected);
    wsManager.on("reconnecting", handleReconnecting);

    // Check initial connection state
    setIsConnected(wsManager.isConnected());

    return () => {
      wsManager.off("connected", handleConnected);
      wsManager.off("disconnected", handleDisconnected);
      wsManager.off("reconnecting", handleReconnecting);
    };
  }, [conversation]);

  const sendTyping = useCallback((isTyping: boolean) => {
    wsManager.sendTyping(isTyping);
  }, []);

  return {
    isConnected,
    isReconnecting,
    sendTyping,
  };
}
