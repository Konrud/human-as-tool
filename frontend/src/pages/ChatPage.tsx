import { ChannelFallbackAlert } from "@/components/channel/ChannelFallbackAlert";
import { ChannelReconnecting } from "@/components/channel/ChannelReconnecting";
import { ChannelSelector } from "@/components/channel/ChannelSelector";
import {
  ChannelSettings,
  getDefaultChannelPreferences,
} from "@/components/channel/ChannelSettings";
import { ChatSession } from "@/components/session/ChatSession";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { ChannelStatus, ChannelType } from "@/types/models";
import { Moon, Settings, Sun } from "lucide-react";
import React, { useState } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

export const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();
  const [channelSettingsOpen, setChannelSettingsOpen] = useState(false);
  const [channelPreferences, setChannelPreferences] = useState(getDefaultChannelPreferences());

  // Mock channel status - in real app, this would come from useSession
  const [mockChannelStatus] = useState<Record<ChannelType, ChannelStatus>>({
    [ChannelType.WEBSOCKET]: ChannelStatus.ACTIVE,
    [ChannelType.EMAIL]: ChannelStatus.INACTIVE,
    [ChannelType.SLACK]: ChannelStatus.INACTIVE,
  });

  // Mock fallback state
  const [showFallback, setShowFallback] = useState(false);
  const [fallbackInfo, setFallbackInfo] = useState<{
    previousChannel: ChannelType;
    currentChannel: ChannelType;
    reason: string;
  } | null>(null);

  // Mock reconnecting state
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  const handleSessionUpdate = (sessionId: string) => {
    if (!currentSessionId) {
      setCurrentSessionId(sessionId);
    }
  };

  const handleChannelChange = (channel: ChannelType) => {
    console.log("Channel changed to:", channel);
    // In real app, this would call session.actions.changePreferredChannel(channel)

    // Demo: Simulate fallback when switching to Email (for testing)
    if (channel === ChannelType.EMAIL) {
      setFallbackInfo({
        previousChannel: ChannelType.WEBSOCKET,
        currentChannel: ChannelType.EMAIL,
        reason: "WebSocket connection timed out",
      });
      setShowFallback(true);
    }
  };

  const handleRetryChannel = () => {
    console.log("Retrying channel");
    setShowFallback(false);
    setIsReconnecting(true);
    setReconnectAttempts(1);
    // Simulate reconnection
    setTimeout(() => {
      setIsReconnecting(false);
      setReconnectAttempts(0);
    }, 5000);
  };

  const handleCancelReconnect = () => {
    setIsReconnecting(false);
    setReconnectAttempts(0);
  };

  const handleSaveChannelPreferences = async (preferences: typeof channelPreferences) => {
    console.log("Saving channel preferences:", preferences);
    setChannelPreferences(preferences);
    // In real app, this would send to backend via WebSocket
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* User Info */}
            <div className="flex items-center gap-3">
              <Avatar className="h-9 w-9">
                <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                  {user?.name?.[0]?.toUpperCase() || "U"}
                </AvatarFallback>
              </Avatar>
              <div className="hidden sm:block">
                <h2 className="text-sm font-semibold">{user?.name}</h2>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              {/* Channel Selector */}
              <ChannelSelector
                value={channelPreferences.priority[0]}
                channelStatus={mockChannelStatus}
                onChange={handleChannelChange}
                disabled={false}
              />

              {/* Theme Toggle */}
              <Button
                variant="outline"
                size="icon"
                onClick={toggleTheme}
                className="h-10 w-10"
              >
                {theme === "light" ? (
                  <Moon className="h-4 w-4" />
                ) : (
                  <Sun className="h-4 w-4" />
                )}
              </Button>

              {/* Channel Settings */}
              <Button
                variant="outline"
                size="icon"
                onClick={() => setChannelSettingsOpen(true)}
                className="h-10 w-10 hidden md:flex"
              >
                <Settings className="h-4 w-4" />
              </Button>

              {/* Logout */}
              <Button variant="outline" onClick={logout} className="h-10">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Channel Reconnecting Indicator */}
      {isReconnecting && (
        <ChannelReconnecting
          channel={ChannelType.WEBSOCKET}
          attempts={reconnectAttempts}
          maxAttempts={5}
          nextRetryIn={5}
          onCancel={handleCancelReconnect}
        />
      )}

      {/* Main Chat Area */}
      <main className="flex-1 container max-w-6xl mx-auto px-4 py-6 overflow-hidden">
        {/* Channel Fallback Alert */}
        {showFallback && fallbackInfo && (
          <ChannelFallbackAlert
            previousChannel={fallbackInfo.previousChannel}
            currentChannel={fallbackInfo.currentChannel}
            reason={fallbackInfo.reason}
            onRetry={handleRetryChannel}
            onDismiss={() => setShowFallback(false)}
            className="mb-4"
          />
        )}

        <div className="h-full">
          <ChatSession
            wsUrl={WS_URL}
            sessionId={currentSessionId}
            onSessionUpdate={handleSessionUpdate}
          />
        </div>
      </main>

      {/* Channel Settings Dialog */}
      <ChannelSettings
        open={channelSettingsOpen}
        onOpenChange={setChannelSettingsOpen}
        initialPreferences={channelPreferences}
        onSave={handleSaveChannelPreferences}
      />
    </div>
  );
};
