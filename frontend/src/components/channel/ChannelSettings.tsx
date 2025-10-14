import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChannelType } from "@/types/models";
import { GripVertical } from "lucide-react";
import { useState } from "react";
import { ChannelIcon, getChannelLabel } from "./ChannelIcon";

interface ChannelPreferences {
  enabled: Record<ChannelType, boolean>;
  priority: ChannelType[];
  retryLimit: number;
  timeoutSeconds: number;
}

interface ChannelSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialPreferences: ChannelPreferences;
  onSave: (preferences: ChannelPreferences) => void;
}

export function ChannelSettings({
  open,
  onOpenChange,
  initialPreferences,
  onSave,
}: ChannelSettingsProps) {
  const [preferences, setPreferences] = useState<ChannelPreferences>(initialPreferences);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(preferences);
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to save channel preferences:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setPreferences(initialPreferences);
  };

  const toggleChannelEnabled = (channel: ChannelType) => {
    setPreferences((prev) => ({
      ...prev,
      enabled: {
        ...prev.enabled,
        [channel]: !prev.enabled[channel],
      },
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Channel Settings</DialogTitle>
          <DialogDescription>
            Configure your communication channel preferences and fallback behavior.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Channel Priority */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">Channel Priority</Label>
            <p className="text-sm text-muted-foreground">
              Drag to reorder channels. Higher channels are tried first.
            </p>
            <div className="space-y-2">
              {preferences.priority.map((channel, index) => (
                <div
                  key={channel}
                  className="flex items-center gap-3 p-3 border rounded-lg bg-card"
                >
                  <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
                  <div className="flex items-center gap-2 flex-1">
                    <ChannelIcon channel={channel} size={16} />
                    <span className="font-medium">{getChannelLabel(channel)}</span>
                    <span className="text-xs text-muted-foreground">
                      (Priority {index + 1})
                    </span>
                  </div>
                  <Button
                    variant={preferences.enabled[channel] ? "default" : "outline"}
                    size="sm"
                    onClick={() => toggleChannelEnabled(channel)}
                  >
                    {preferences.enabled[channel] ? "Enabled" : "Disabled"}
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {/* Retry Settings */}
          <div className="space-y-3">
            <Label htmlFor="retryLimit" className="text-base font-semibold">
              Retry Limit
            </Label>
            <p className="text-sm text-muted-foreground">
              Maximum number of reconnection attempts per channel.
            </p>
            <Select
              value={preferences.retryLimit.toString()}
              onValueChange={(val) =>
                setPreferences((prev) => ({
                  ...prev,
                  retryLimit: parseInt(val),
                }))
              }
            >
              <SelectTrigger id="retryLimit">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3">3 attempts</SelectItem>
                <SelectItem value="5">5 attempts</SelectItem>
                <SelectItem value="10">10 attempts</SelectItem>
                <SelectItem value="999">Unlimited</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Timeout Settings */}
          <div className="space-y-3">
            <Label htmlFor="timeout" className="text-base font-semibold">
              Connection Timeout
            </Label>
            <p className="text-sm text-muted-foreground">
              How long to wait before considering a channel unavailable.
            </p>
            <div className="flex items-center gap-2">
              <Input
                id="timeout"
                type="number"
                min="5"
                max="300"
                value={preferences.timeoutSeconds}
                onChange={(e) =>
                  setPreferences((prev) => ({
                    ...prev,
                    timeoutSeconds: parseInt(e.target.value) || 30,
                  }))
                }
                className="w-24"
              />
              <span className="text-sm text-muted-foreground">seconds</span>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={handleReset} disabled={isSaving}>
            Reset to Default
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Default preferences factory
export function getDefaultChannelPreferences(): ChannelPreferences {
  return {
    enabled: {
      [ChannelType.WEBSOCKET]: true,
      [ChannelType.EMAIL]: true,
      [ChannelType.SLACK]: false,
    },
    priority: [ChannelType.WEBSOCKET, ChannelType.EMAIL, ChannelType.SLACK],
    retryLimit: 5,
    timeoutSeconds: 30,
  };
}
