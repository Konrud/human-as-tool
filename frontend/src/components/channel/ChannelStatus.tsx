import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ChannelStatus as ChannelStatusEnum, ChannelType } from "@/types/models";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { ChannelIcon, getChannelDescription, getChannelLabel } from "./ChannelIcon";
import { ChannelStatusBadge } from "./ChannelStatusBadge";

interface ChannelInfo {
  type: ChannelType;
  status: ChannelStatusEnum;
  lastActive?: Date;
  errorCount?: number;
  errorMessage?: string;
}

interface ChannelStatusProps {
  channels: ChannelInfo[];
  onRetry?: (channel: ChannelType) => void;
  className?: string;
}

export function ChannelStatus({ channels, onRetry, className }: ChannelStatusProps) {
  const [expandedChannels, setExpandedChannels] = useState<Set<ChannelType>>(new Set());

  const toggleExpanded = (channel: ChannelType) => {
    setExpandedChannels((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(channel)) {
        newSet.delete(channel);
      } else {
        newSet.add(channel);
      }
      return newSet;
    });
  };

  const hasErrors = channels.some((ch) => ch.status === ChannelStatusEnum.ERROR);

  return (
    <div className={cn("space-y-4", className)}>
      {hasErrors && (
        <Alert variant="destructive">
          <AlertTitle>Channel Connection Issues</AlertTitle>
          <AlertDescription>
            Some communication channels are experiencing errors. Messages may be delayed or
            routed through alternative channels.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {channels.map((channel) => {
          const isExpanded = expandedChannels.has(channel.type);
          const hasError = channel.status === ChannelStatusEnum.ERROR;
          const canRetry = hasError && channel.status !== ChannelStatusEnum.RECONNECTING;

          return (
            <Card
              key={channel.type}
              className={cn("transition-all", hasError && "border-destructive")}
            >
              <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <ChannelIcon channel={channel.type} size={20} />
                    <div>
                      <h3 className="font-semibold text-sm">
                        {getChannelLabel(channel.type)}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {getChannelDescription(channel.type)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Status Badge */}
                <div className="mb-3">
                  <ChannelStatusBadge
                    status={channel.status}
                    lastActive={channel.lastActive}
                    errorCount={channel.errorCount}
                  />
                </div>

                {/* Expandable Details */}
                {(channel.errorMessage || channel.errorCount) && (
                  <div className="space-y-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleExpanded(channel.type)}
                      className="w-full justify-start h-8 text-xs"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-3 w-3 mr-1" />
                      ) : (
                        <ChevronRight className="h-3 w-3 mr-1" />
                      )}
                      {isExpanded ? "Hide" : "Show"} details
                    </Button>

                    {isExpanded && (
                      <div className="space-y-2 pl-4 text-xs">
                        {channel.errorMessage && (
                          <div>
                            <span className="font-medium text-muted-foreground">Error:</span>
                            <p className="text-destructive mt-1">{channel.errorMessage}</p>
                          </div>
                        )}
                        {channel.errorCount && channel.errorCount > 0 && (
                          <div>
                            <span className="font-medium text-muted-foreground">
                              Error Count:
                            </span>
                            <p className="mt-1">{channel.errorCount}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Retry Button */}
                {canRetry && onRetry && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onRetry(channel.type)}
                    className="w-full mt-3 h-9"
                  >
                    Retry Connection
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
