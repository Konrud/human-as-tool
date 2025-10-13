import { ChatSession } from "@/components/session/ChatSession";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { ChannelType } from "@/types/models";
import { Moon, Settings, Sun } from "lucide-react";
import React, { useState } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

export const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [selectedChannel, setSelectedChannel] = useState<ChannelType>(ChannelType.WEBSOCKET);
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();

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
              <Select
                value={selectedChannel}
                onValueChange={(value) => setSelectedChannel(value as ChannelType)}
              >
                <SelectTrigger className="w-[140px] h-10">
                  <SelectValue placeholder="Channel" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ChannelType.WEBSOCKET}>WebSocket</SelectItem>
                  <SelectItem value={ChannelType.EMAIL}>Email</SelectItem>
                  <SelectItem value={ChannelType.SLACK}>Slack</SelectItem>
                </SelectContent>
              </Select>

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

              {/* Settings */}
              <Button variant="outline" size="icon" className="h-10 w-10 hidden md:flex">
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

      {/* Main Chat Area */}
      <main className="flex-1 container max-w-6xl mx-auto px-4 py-6 overflow-hidden">
        <div className="h-full">
          <ChatSession
            wsUrl={WS_URL}
            sessionId={currentSessionId}
            onSessionUpdate={handleSessionUpdate}
          />
        </div>
      </main>
    </div>
  );
};
