import { cn } from "@/lib/utils";
import { ChannelType } from "@/types/models";
import { Hash, Mail, MessageSquare } from "lucide-react";

interface ChannelIconProps {
  channel: ChannelType;
  className?: string;
  size?: number;
}

export function ChannelIcon({ channel, className, size = 16 }: ChannelIconProps) {
  const iconProps = {
    className: cn("flex-shrink-0", className),
    size,
  };

  switch (channel) {
    case ChannelType.WEBSOCKET:
      return <MessageSquare {...iconProps} />;
    case ChannelType.EMAIL:
      return <Mail {...iconProps} />;
    case ChannelType.SLACK:
      return <Hash {...iconProps} />;
    default:
      return <MessageSquare {...iconProps} />;
  }
}

export function getChannelLabel(channel: ChannelType): string {
  switch (channel) {
    case ChannelType.WEBSOCKET:
      return "Chat";
    case ChannelType.EMAIL:
      return "Email";
    case ChannelType.SLACK:
      return "Slack";
    default:
      return "Unknown";
  }
}

export function getChannelDescription(channel: ChannelType): string {
  switch (channel) {
    case ChannelType.WEBSOCKET:
      return "Real-time chat connection";
    case ChannelType.EMAIL:
      return "Email notifications";
    case ChannelType.SLACK:
      return "Slack workspace integration";
    default:
      return "";
  }
}
