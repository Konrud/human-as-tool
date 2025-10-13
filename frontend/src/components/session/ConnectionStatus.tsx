import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChannelStatus } from "@/types/models";
import { AlertCircle, RefreshCw, WifiOff } from "lucide-react";

interface ConnectionStatusProps {
  status: ChannelStatus;
  onReconnect?: () => void;
  className?: string;
}

export function ConnectionStatus({ status, onReconnect, className }: ConnectionStatusProps) {
  const getStatusConfig = () => {
    switch (status) {
      case ChannelStatus.ACTIVE:
        return null; // Don't show anything when connected
      case ChannelStatus.RECONNECTING:
        return {
          icon: <RefreshCw className="h-4 w-4 animate-spin" />,
          title: "Reconnecting...",
          description: "Attempting to restore connection",
          variant: "default" as const,
          showRetry: false,
        };
      case ChannelStatus.ERROR:
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          title: "Connection Error",
          description: "Unable to connect to the server",
          variant: "destructive" as const,
          showRetry: true,
        };
      case ChannelStatus.INACTIVE:
      default:
        return {
          icon: <WifiOff className="h-4 w-4" />,
          title: "Disconnected",
          description: "Connection to the server was lost",
          variant: "default" as const,
          showRetry: true,
        };
    }
  };

  const config = getStatusConfig();

  if (!config) {
    return null;
  }

  return (
    <Alert
      variant={config.variant}
      className={cn("shadow-[2px_5px_17px_-5px_rgba(0,0,0,0.25)] mb-4", className)}
    >
      {config.icon}
      <div className="flex items-center justify-between flex-1">
        <div>
          <AlertTitle>{config.title}</AlertTitle>
          <AlertDescription>{config.description}</AlertDescription>
        </div>
        {config.showRetry && onReconnect && (
          <Button onClick={onReconnect} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </div>
    </Alert>
  );
}
