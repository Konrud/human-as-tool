import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { ChannelStatus } from "@/types/models";
import { AlertCircle, CheckCircle, Clock, WifiOff } from "lucide-react";

interface ChannelStatusBadgeProps {
  status: ChannelStatus;
  lastActive?: Date;
  errorCount?: number;
  className?: string;
  showTooltip?: boolean;
}

export function ChannelStatusBadge({
  status,
  lastActive,
  errorCount = 0,
  className,
  showTooltip = true,
}: ChannelStatusBadgeProps) {
  const getStatusConfig = () => {
    switch (status) {
      case ChannelStatus.ACTIVE:
        return {
          icon: <CheckCircle className="h-3 w-3" />,
          text: "Active",
          variant: "default" as const,
          className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        };
      case ChannelStatus.INACTIVE:
        return {
          icon: <WifiOff className="h-3 w-3" />,
          text: "Inactive",
          variant: "secondary" as const,
          className: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
        };
      case ChannelStatus.ERROR:
        return {
          icon: <AlertCircle className="h-3 w-3" />,
          text: "Error",
          variant: "destructive" as const,
          className: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
        };
      case ChannelStatus.RECONNECTING:
        return {
          icon: <Clock className="h-3 w-3 animate-spin" />,
          text: "Reconnecting",
          variant: "outline" as const,
          className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        };
      default:
        return {
          icon: <WifiOff className="h-3 w-3" />,
          text: "Unknown",
          variant: "secondary" as const,
          className: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
        };
    }
  };

  const config = getStatusConfig();

  const formatLastActive = (date?: Date) => {
    if (!date) return "Never";
    const now = new Date().getTime();
    const then = new Date(date).getTime();
    const diff = now - then;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "Just now";
  };

  const badge = (
    <Badge
      variant={config.variant}
      className={cn(
        "flex items-center gap-1 text-xs font-medium",
        config.className,
        className
      )}
    >
      {config.icon}
      <span>{config.text}</span>
    </Badge>
  );

  if (!showTooltip) {
    return badge;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent side="bottom" className="text-xs">
          <div className="space-y-1">
            <p className="font-semibold">{config.text}</p>
            <p className="text-muted-foreground">
              Last active: {formatLastActive(lastActive)}
            </p>
            {errorCount > 0 && <p className="text-red-500">Errors: {errorCount}</p>}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
