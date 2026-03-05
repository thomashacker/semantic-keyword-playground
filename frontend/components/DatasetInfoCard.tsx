"use client";

import { DatasetInfo } from "@/lib/api";
import { HiDatabase } from "react-icons/hi";

interface Props {
  dataset: DatasetInfo | null;
}

const DESCRIPTIONS: Record<string, string> = {
  Landmarks:
    "250 world-famous landmarks with descriptions, countries, and categories.",
  Movies: "300 classic and contemporary films with plot summaries.",
  Science:
    "200 scientific concepts with explanations across physics, biology, astronomy, and more.",
};

export function DatasetInfoCard({ dataset }: Props) {
  if (!dataset) return null;
  return (
    <div className="flex items-center gap-3 p-3 border-4 border-black bg-white" style={{ boxShadow: "4px 4px 0px 0px #000000" }}>
      <HiDatabase className="w-5 h-5 text-black shrink-0" />
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-black uppercase text-sm">{dataset.name}</span>
          <span className="font-mono text-xs bg-black text-white px-1">
            {dataset.record_count.toLocaleString()} records
          </span>
        </div>
        <p className="font-mono text-[10px] opacity-60 uppercase mt-0.5 truncate">
          {DESCRIPTIONS[dataset.name] || dataset.description}
        </p>
      </div>
    </div>
  );
}
