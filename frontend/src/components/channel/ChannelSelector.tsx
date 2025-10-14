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
          <ChannelIcon channel={value} size={16} />
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
              <div className="flex items-center justify-between w-full gap-3">
                <div className="flex items-center gap-2">
                  <ChannelIcon channel={channel} size={16} />
                  <span className="font-medium">{getChannelLabel(channel)}</span>
                </div>
                <ChannelStatusBadge status={status} showTooltip={false} />
              </div>
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
