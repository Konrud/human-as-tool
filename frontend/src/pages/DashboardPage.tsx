import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { CheckCircle2, MessageSquare, Moon, Sun } from "lucide-react";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [selectedChannel, setSelectedChannel] = useState("websocket");

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Avatar className="h-12 w-12">
              <AvatarFallback className="bg-primary text-primary-foreground">
                {user?.name?.[0]?.toUpperCase() || "U"}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-2xl font-bold">Welcome, {user?.name}</h1>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={toggleTheme}>
              {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </Button>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>

        {/* Success Alert */}
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>Phase 3 Implementation Complete!</AlertTitle>
          <AlertDescription>
            Feedback request UI with pause/resume workflow is now ready. Test the interactive
            demo!
          </AlertDescription>
        </Alert>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-4">
          <Button onClick={() => navigate("/chat")} size="lg" className="gap-2">
            <MessageSquare className="h-5 w-5" />
            Start Chat Session
          </Button>
          <Button
            onClick={() => navigate("/feedback-demo")}
            size="lg"
            variant="outline"
            className="gap-2"
          >
            <CheckCircle2 className="h-5 w-5" />
            View Feedback Demo
          </Button>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Shadcn/ui Components */}
          <Card>
            <CardHeader>
              <CardTitle>shadcn/ui Components</CardTitle>
              <CardDescription>Mobile-first UI library</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="channel-select">Channel Selector</Label>
                <Select value={selectedChannel} onValueChange={setSelectedChannel}>
                  <SelectTrigger id="channel-select">
                    <SelectValue placeholder="Select channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="websocket">WebSocket</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="slack">Slack</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 flex-wrap">
                <Button size="sm">Default</Button>
                <Button size="sm" variant="secondary">
                  Secondary
                </Button>
                <Button size="sm" variant="outline">
                  Outline
                </Button>
                <Button size="sm" variant="ghost">
                  Ghost
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Authentication */}
          <Card>
            <CardHeader>
              <CardTitle>Authentication</CardTitle>
              <CardDescription>Placeholder auth system</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[200px] rounded-md border p-4">
                <div className="space-y-2 text-sm">
                  <p>
                    <strong>Status:</strong> Authenticated ✓
                  </p>
                  <p>
                    <strong>User ID:</strong> {user?.id}
                  </p>
                  <p>
                    <strong>Email:</strong> {user?.email}
                  </p>
                  <p>
                    <strong>Name:</strong> {user?.name}
                  </p>
                  <p className="text-muted-foreground pt-2 border-t">
                    Mock authentication system with localStorage token management and
                    auto-refresh capability.
                  </p>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Validation */}
          <Card>
            <CardHeader>
              <CardTitle>Zod Validation</CardTitle>
              <CardDescription>Runtime type validation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Session schemas
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Message schemas
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Feedback schemas
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Channel schemas
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Agent schemas
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Responsive Design */}
          <Card>
            <CardHeader>
              <CardTitle>Mobile-First Design</CardTitle>
              <CardDescription>Touch-friendly interface</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button size="touch" className="w-full">
                Touch Target (44px)
              </Button>
              <p className="text-sm text-muted-foreground">
                Breakpoints: xs (475px), sm (640px), md (768px), lg (1024px), xl (1280px), 2xl
                (1536px)
              </p>
            </CardContent>
          </Card>

          {/* Theme Support */}
          <Card>
            <CardHeader>
              <CardTitle>Dark Mode</CardTitle>
              <CardDescription>CSS variable-based theming</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Current theme:</span>
                  <span className="text-sm font-medium capitalize">{theme}</span>
                </div>
                <Button onClick={toggleTheme} variant="outline" className="w-full">
                  Toggle Theme
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* VS Code Setup */}
          <Card>
            <CardHeader>
              <CardTitle>VS Code Configuration</CardTitle>
              <CardDescription>Development environment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ESLint integration
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Prettier formatting
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  TypeScript analysis
                </p>
                <p className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Tailwind IntelliSense
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
