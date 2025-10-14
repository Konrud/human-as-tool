import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { ChannelStatus, ChannelType } from "@/types/models";
import { ChannelIcon, getChannelLabel } from "./ChannelIcon";
import { ChannelStatusBadge } from "./ChannelStatusBadge";

interface ChannelSelectorProps {
  value: ChannelType;
  channelStatus: Record<ChannelType, ChannelStatus>;
  onChange: (channel: ChannelType) => void;
  disabled?: boolean;
  className?: string;
}

export function ChannelSelector({
  value,
  channelStatus,
  onChange,
  disabled = false,
  className,
}: ChannelSelectorProps) {
  const channels = [ChannelType.WEBSOCKET, ChannelType.EMAIL, ChannelType.SLACK];

  return (
    <Select
      value={value}
      onValueChange={(val) => onChange(val as ChannelType)}
      disabled={disabled}
    >
      <SelectTrigger
        className={cn("min-h-[44px] w-[160px]", className)}
        aria-label="Select communication channel"
      >
        <div className="flex items-center gap-2">
          <SelectValue placeholder="Select channel" />
        </div>
      </SelectTrigger>
      <SelectContent>
        {channels.map((channel) => {
          const status = channelStatus[channel];
          const isDisabled =
            status === ChannelStatus.ERROR || status === ChannelStatus.INACTIVE;

          return (
            <SelectItem
              key={channel}
              value={channel}
              disabled={isDisabled}
              className="min-h-[44px] cursor-pointer"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <ChannelIcon channel={channel} size={16} className="flex-shrink-0" />
                <span className="font-medium flex-1 min-w-0 truncate">
                  {getChannelLabel(channel)}
                </span>
                <div className="flex-shrink-0">
                  <ChannelStatusBadge status={status} showTooltip={false} />
                </div>
              </div>
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
