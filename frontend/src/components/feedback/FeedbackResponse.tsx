import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { FeedbackRequest } from "@/types/models";
import { FeedbackType } from "@/types/models";
import { Check, Loader2, X } from "lucide-react";
import { useState } from "react";

interface FeedbackResponseProps {
  request: FeedbackRequest;
  onSubmitApproval?: (approved: boolean) => void;
  onSubmitInput?: (content: string) => void;
  loading?: boolean;
  className?: string;
}

export function FeedbackResponse({
  request,
  onSubmitApproval,
  onSubmitInput,
  loading,
  className,
}: FeedbackResponseProps) {
  const [inputValue, setInputValue] = useState("");
  const [charCount, setCharCount] = useState(0);

  const handleInputChange = (value: string) => {
    setInputValue(value);
    setCharCount(value.length);
  };

  const handleSubmitInput = () => {
    if (inputValue.trim() && onSubmitInput) {
      onSubmitInput(inputValue.trim());
      setInputValue("");
      setCharCount(0);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmitInput();
    }
  };

  if (request.type === FeedbackType.APPROVAL) {
    return (
      <div className={className}>
        <div className="flex gap-2 sm:gap-3">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => onSubmitApproval?.(true)}
                  disabled={loading}
                  variant="default"
                  className="flex-1 min-h-[44px] touch-manipulation bg-green-600 hover:bg-green-700"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      <span>Approve</span>
                    </>
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Approve this request and resume the agent</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => onSubmitApproval?.(false)}
                  disabled={loading}
                  variant="destructive"
                  className="flex-1 min-h-[44px] touch-manipulation"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <X className="h-4 w-4 mr-2" />
                      <span>Reject</span>
                    </>
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Reject this request and resume the agent</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    );
  }

  // INPUT type
  return (
    <div className={className}>
      <div className="space-y-2">
        <Textarea
          value={inputValue}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
            handleInputChange(e.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Type your response here..."
          disabled={loading}
          className="min-h-[80px] resize-none touch-manipulation"
          maxLength={2000}
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {charCount > 0 && `${charCount} / 2000 characters`}
            {charCount === 0 && "Ctrl+Enter to submit"}
          </span>
          <Button
            onClick={handleSubmitInput}
            disabled={loading || !inputValue.trim()}
            className="min-h-[44px] touch-manipulation"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Submit Response
          </Button>
        </div>
      </div>
    </div>
  );
}
