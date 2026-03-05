"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HiInformationCircle } from "react-icons/hi";

interface Props {
  title: string;
  body: string;
  children: React.ReactNode;
}

export function ExplainerTooltip({ title, body, children }: Props) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-help inline-flex items-center gap-1">
            {children}
            <HiInformationCircle className="w-4 h-4 text-black opacity-40 hover:opacity-100 transition-opacity" />
          </span>
        </TooltipTrigger>
        <TooltipContent
          className="max-w-xs p-4 bg-white border-4 border-black text-black"
          style={{ boxShadow: "4px 4px 0px 0px #000000" }}
        >
          <p className="font-black text-sm uppercase mb-1">{title}</p>
          <p className="font-mono text-xs opacity-70 leading-relaxed">{body}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
