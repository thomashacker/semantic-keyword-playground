"use client";

import { DatasetInfo } from "@/lib/api";
import { HiDatabase } from "react-icons/hi";

interface Props {
  query: string;
  setQuery: (q: string) => void;
  dataset: string;
  setDataset: (d: string) => void;
  onSearch: () => void;
  loading: boolean;
  datasetInfo: DatasetInfo;
}

const DATASETS = ["Landmarks", "Movies", "Science", "Games", "Pokemon"];

const DESCRIPTIONS: Record<string, string> = {
  Landmarks: "World-famous landmarks with descriptions, countries, and categories.",
  Movies: "Classic and contemporary films with plot summaries.",
  Science: "Scientific concepts with explanations across physics, biology, astronomy, and more.",
  Games: "Steam games with descriptions, genres, and developers.",
  Pokemon: "Pokémon with Pokédex entries, types, and abilities.",
};

export function SearchBar({
  query,
  setQuery,
  dataset,
  setDataset,
  onSearch,
  loading,
  datasetInfo,
}: Props) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") onSearch();
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Dataset tabs with floating label */}
      <div className="relative pt-4">
        <span className="absolute top-0 left-4 bg-white border-2 border-black px-2 text-[10px] font-bold z-10 uppercase">
          Dataset_Selection
        </span>
        <div className="flex gap-0">
          {DATASETS.map((d, i) => (
            <button
              key={d}
              onClick={() => setDataset(d)}
              className={`neo-button text-sm px-3 py-2 ${i > 0 ? "-ml-[4px]" : ""} ${
                dataset === d
                  ? "bg-black text-white border-black z-10"
                  : "bg-white text-black hover:bg-black/5"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Dataset info card — between tabs and input */}
      <div className="flex items-center gap-3 px-3 py-2 border-4 border-black bg-white -mt-[4px]">
        <HiDatabase className="w-4 h-4 text-black shrink-0 opacity-60" />
        <div className="min-w-0 flex items-center gap-2">
          <span className="font-mono text-xs bg-black text-white px-1">
            {datasetInfo.record_count.toLocaleString()} records
          </span>
          <p className="font-mono text-[10px] opacity-50 uppercase truncate">
            {DESCRIPTIONS[datasetInfo.name] || datasetInfo.description}
          </p>
        </div>
      </div>

      {/* Query input */}
      <div className="flex gap-0 items-stretch mt-6">
        <div className="flex-1 relative">
          <span className="absolute -top-3 left-4 bg-white border-2 border-black px-2 text-[10px] font-bold z-10 uppercase">
            System_Query_Input
          </span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Search ${dataset}...`}
            className="neo-input h-16 text-xl w-full"
          />
        </div>
        <button
          onClick={onSearch}
          disabled={loading || !query.trim()}
          className="neo-button-primary h-16 px-10 text-xl uppercase -ml-[4px] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "..." : "Execute"}
        </button>
      </div>
    </div>
  );
}
