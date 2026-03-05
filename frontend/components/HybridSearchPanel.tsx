"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { searchHybrid, HybridSearchResponse } from "@/lib/api";
import { ExplainerTooltip } from "./ExplainerTooltip";

interface Props {
  query: string;
  collection: string;
  limit?: number;
}

const spring = { type: "spring" as const, stiffness: 200, damping: 20 };

const HYBRID_TOOLTIP = {
  title: "Hybrid Search",
  body: "Hybrid search fuses BM25 keyword matching with neural vector search using Reciprocal Rank Fusion (RRF). The alpha slider blends both signals — 0 is pure keyword, 1 is pure semantic, 0.5 balances both.",
};

const HYBRID_SCORE_TOOLTIP = {
  title: "Hybrid Score",
  body: "The fused relevance score from Reciprocal Rank Fusion — a rank-based combination of BM25 and vector similarity scores. Higher is more relevant.",
};

const RECALL_TOOLTIP = {
  title: "RECALL@10",
  body: "Hybrid search consistently outperforms either method alone — especially for queries that mix exact terminology with conceptual meaning. The alpha slider lets you tune the balance for your specific use case.",
};

function alphaLabel(alpha: number): string {
  if (alpha <= 0.1) return "Pure_BM25";
  if (alpha <= 0.35) return "Keyword_Dominant";
  if (alpha <= 0.65) return "Balanced_Fusion";
  if (alpha <= 0.9) return "Semantic_Dominant";
  return "Pure_Vector";
}

function SkeletonCard() {
  return (
    <div className="border-b-4 border-black bg-white p-4 animate-pulse">
      <div className="h-4 bg-black/10 w-3/4 mb-2" />
      <div className="h-3 bg-black/10 w-full mb-1" />
      <div className="h-3 bg-black/10 w-5/6" />
    </div>
  );
}

export function HybridSearchPanel({ query, collection, limit = 10 }: Props) {
  const [alpha, setAlpha] = useState(0.5);
  const [results, setResults] = useState<HybridSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const doSearch = useCallback(
    async (q: string, col: string, a: number) => {
      if (!q.trim()) return;
      setLoading(true);
      setError(null);
      try {
        const data = await searchHybrid(q, col, a, limit);
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Hybrid search failed");
      } finally {
        setLoading(false);
      }
    },
    [limit]
  );

  useEffect(() => {
    doSearch(query, collection, alpha);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, collection]);

  const handleAlphaChange = (newAlpha: number) => {
    setAlpha(newAlpha);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(query, collection, newAlpha), 300);
  };

  return (
    <div>
      {/* Header — matches ResultsPanel exactly */}
      <div
        className="border-4 border-black p-3 mb-4"
        style={{ backgroundColor: "#ffff00", boxShadow: "4px 4px 0px 0px #000000" }}
      >
        <div className="flex items-center justify-between gap-2">
          <ExplainerTooltip title={HYBRID_TOOLTIP.title} body={HYBRID_TOOLTIP.body}>
            <span className="font-black uppercase tracking-tighter text-base text-black">
              Engine: Hybrid_Fusion
            </span>
          </ExplainerTooltip>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <ExplainerTooltip title={RECALL_TOOLTIP.title} body={RECALL_TOOLTIP.body}>
              <div className="text-[9px] border-2 border-black px-1.5 py-0.5 bg-white font-mono font-bold leading-none cursor-help">
                RECALL@10: <span>96%</span>
              </div>
            </ExplainerTooltip>
            {results && (
              <span className="bg-black text-[#ffff00] px-2 py-0.5 font-black font-mono text-sm leading-none">
                {Math.round(results.hybrid_ms)}ms
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Alpha slider */}
      <div
        className="bg-white border-4 border-black p-4 mb-4"
        style={{ boxShadow: "4px 4px 0px 0px #000000" }}
      >
        <div className="flex items-center justify-between mb-3">
          <span className="data-label" style={{ color: "#00aaaa" }}>BM25_Keyword</span>
          <span className="font-mono text-[10px] font-bold bg-black text-white px-2 py-0.5">
            alpha={alpha.toFixed(2)} // {alphaLabel(alpha)}
          </span>
          <span className="data-label" style={{ color: "#aa00aa" }}>Vector_Neural</span>
        </div>
        <div className="relative">
          {/* Track */}
          <div className="h-3 border-2 border-black bg-white relative">
            {/* Fill from left (keyword side, cyan tint) */}
            <div
              className="absolute top-0 left-0 h-full"
              style={{
                width: `${alpha * 100}%`,
                backgroundColor: "#ffff00",
              }}
            />
          </div>
          {/* Range input overlaid */}
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={alpha}
            onChange={(e) => handleAlphaChange(parseFloat(e.target.value))}
            className="absolute inset-0 w-full opacity-0 cursor-pointer h-3"
            style={{ margin: 0 }}
          />
          {/* Custom thumb */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-5 h-5 border-2 border-black bg-[#ffff00] pointer-events-none"
            style={{
              left: `calc(${alpha * 100}% - 10px)`,
              boxShadow: "2px 2px 0px 0px #000000",
            }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="font-mono text-[9px] opacity-40">0.0</span>
          <span className="font-mono text-[9px] opacity-40">0.5</span>
          <span className="font-mono text-[9px] opacity-40">1.0</span>
        </div>
      </div>

      {/* Results */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="hybrid-loading"
            className="bg-white border-4 border-black divide-y-4 divide-black overflow-hidden"
            style={{ boxShadow: "4px 4px 0px 0px #000000" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </motion.div>
        ) : error ? (
          <div className="bg-white border-4 border-black p-4" style={{ boxShadow: "4px 4px 0px 0px #000000" }}>
            <p className="font-black uppercase text-sm">Error</p>
            <p className="font-mono text-xs opacity-70 mt-1">{error}</p>
          </div>
        ) : results && results.results.length === 0 ? (
          <div className="bg-white border-4 border-black p-5 text-center" style={{ boxShadow: "4px 4px 0px 0px #000000" }}>
            <p className="font-black uppercase text-sm">No hybrid results found.</p>
          </div>
        ) : results ? (
          <motion.div
            key={`hybrid-${alpha}`}
            className="bg-white border-4 border-black divide-y-4 divide-black overflow-hidden"
            style={{ boxShadow: "4px 4px 0px 0px #000000" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {results.results.map((r, i) => (
              <motion.div
                key={r.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...spring, delay: i * 0.07 }}
                className={`p-6 transition-colors hover:bg-[#ffff00]/10 ${i === 0 ? "border-l-8 border-l-[#ffff00]" : ""}`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="data-label mb-1">Document_Title</div>
                    <h3 className="font-black text-lg leading-tight uppercase text-black truncate">
                      {r.title}
                    </h3>
                  </div>
                  {r.score != null && (
                    <ExplainerTooltip title={HYBRID_SCORE_TOOLTIP.title} body={HYBRID_SCORE_TOOLTIP.body}>
                      <div className="flex-shrink-0 text-right">
                        <div className="data-label mb-1">Hybrid_Score</div>
                        <span className="bg-black px-2 py-0.5 font-black font-mono text-sm" style={{ color: "#ffff00" }}>
                          {r.score.toFixed(4)}
                        </span>
                      </div>
                    </ExplainerTooltip>
                  )}
                </div>
                <div className="bg-black/5 p-3 border-2 border-black/10 font-mono text-xs">
                  {r.description}
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
