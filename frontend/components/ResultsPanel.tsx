"use client";

import { AnimatePresence, motion } from "framer-motion";
import { DualSearchResponse } from "@/lib/api";
import { BM25ResultCard, SemanticResultCard } from "./ResultCard";
import { ExplainerTooltip } from "./ExplainerTooltip";
import { VectorViz } from "./VectorViz";

const RECALL_TOOLTIP = {
  title: "RECALL@10",
  body: "Recall@10 measures how many of the truly relevant documents appear in the top 10 results. A score of 92% means ~9 out of 10 relevant documents were retrieved. These are approximate benchmark values — semantic search consistently outperforms BM25 on semantic queries.",
};

interface Props {
  results: DualSearchResponse | null;
  loading: boolean;
  error: string | null;
}

function SkeletonCard() {
  return (
    <div className="border-b-4 border-black bg-white p-4 animate-pulse">
      <div className="h-4 bg-black/10 w-3/4 mb-2" />
      <div className="h-3 bg-black/10 w-full mb-1" />
      <div className="h-3 bg-black/10 w-5/6 mb-1" />
      <div className="h-3 bg-black/10 w-4/6" />
    </div>
  );
}

function EmptyState({ type }: { type: "bm25" | "semantic" }) {
  if (type === "bm25") {
    return (
      <div className="bg-white border-4 border-black p-5 text-center" style={{ boxShadow: "4px 4px 0px 0px #000000" }}>
        <p className="font-black uppercase text-sm mb-1">No keyword matches found</p>
        <p className="text-xs font-mono opacity-70 leading-relaxed">
          BM25 requires exact words from your query to appear in the document.
          See how semantic search finds related results even without matching words.
        </p>
      </div>
    );
  }
  return (
    <div className="bg-white border-4 border-black p-5 text-center" style={{ boxShadow: "4px 4px 0px 0px #000000" }}>
      <p className="font-black uppercase text-sm">No semantic results found.</p>
    </div>
  );
}

const BM25_TOOLTIP = {
  title: "BM25 Keyword Search",
  body: "BM25 (Best Match 25) scores documents based on exact word matches. It's fast and precise — but only finds results containing the exact words in your query. 'Landmark in France' won't find 'Eiffel Tower' if it just says 'Paris monument'.",
};

const SEMANTIC_TOOLTIP = {
  title: "Semantic Vector Search",
  body: "Semantic search converts your query into a vector (a list of numbers representing meaning) using an AI embedding model. It finds documents whose meaning is closest — even without shared words. 'Landmark in France' finds Eiffel Tower because their concepts are close in vector space.",
};

// Static styles matching neo-panel but WITHOUT the :hover lift (issue 5 fix)
const PANEL_STYLE = {
  boxShadow: "4px 4px 0px 0px #000000",
} as const;
const PANEL_CLASS = "bg-white border-4 border-black p-0 divide-y-4 divide-black overflow-hidden";

export function ResultsPanel({ results, loading, error }: Props) {
  if (error) {
    return (
      <div className="bg-white border-4 border-black p-6 text-center" style={PANEL_STYLE}>
        <p className="font-black uppercase">Error</p>
        <p className="text-xs font-mono mt-1 opacity-70">{error}</p>
      </div>
    );
  }

  if (!results && !loading) {
    return (
      <div className="flex items-center justify-center py-20 font-mono text-sm opacity-40 uppercase">
        Enter a query above to compare BM25 and semantic search results.
      </div>
    );
  }

  const queryTerms = results?.query_terms ?? [];

  return (
    <div
      key={results?.query ?? "empty"}
      className="grid grid-cols-1 md:grid-cols-2 gap-6"
    >
      {/* BM25 Column */}
      <div>
        <div className="border-4 border-black p-3 mb-4" style={{ backgroundColor: "#00ffff", boxShadow: "4px 4px 0px 0px #000000" }}>
          <div className="flex items-center justify-between gap-2">
            <ExplainerTooltip title={BM25_TOOLTIP.title} body={BM25_TOOLTIP.body}>
              <span className="font-black uppercase tracking-tighter text-base">Engine: BM25_Keyword</span>
            </ExplainerTooltip>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <ExplainerTooltip title={RECALL_TOOLTIP.title} body={RECALL_TOOLTIP.body}>
                <div className="text-[9px] border-2 border-black px-1.5 py-0.5 bg-white font-mono font-bold leading-none cursor-help">
                  RECALL@10: <span>65%</span>
                </div>
              </ExplainerTooltip>
              {results && (
                <span className="bg-black text-[#00ffff] px-2 py-0.5 font-black font-mono text-sm leading-none">
                  {results.timing.bm25_ms.toFixed(0)}ms
                </span>
              )}
            </div>
          </div>
        </div>

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="bm25-loading"
              className={PANEL_CLASS}
              style={PANEL_STYLE}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {[...Array(3)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </motion.div>
          ) : results?.bm25.length === 0 ? (
            <EmptyState type="bm25" />
          ) : (
            <motion.div
              key="bm25-results"
              className={PANEL_CLASS}
              style={PANEL_STYLE}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {results?.bm25.map((r, i) => (
                <BM25ResultCard key={r.title} result={r} index={i} queryTerms={queryTerms} />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Semantic Column */}
      <div>
        <div className="border-4 border-black p-3 mb-4" style={{ backgroundColor: "#ff00ff", boxShadow: "4px 4px 0px 0px #000000" }}>
          <div className="flex items-center justify-between gap-2">
            <ExplainerTooltip title={SEMANTIC_TOOLTIP.title} body={SEMANTIC_TOOLTIP.body}>
              <span className="font-black uppercase tracking-tighter text-base text-white">Engine: Vector_Neural</span>
            </ExplainerTooltip>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <ExplainerTooltip title={RECALL_TOOLTIP.title} body={RECALL_TOOLTIP.body}>
                <div className="text-[9px] border-2 border-white px-1.5 py-0.5 font-mono font-bold text-white leading-none cursor-help">
                  RECALL@10: <span>92%</span>
                </div>
              </ExplainerTooltip>
              {results && (
                <span className="bg-black text-[#ff00ff] px-2 py-0.5 font-black font-mono text-sm leading-none">
                  {results.timing.semantic_ms.toFixed(0)}ms
                </span>
              )}
            </div>
          </div>
        </div>

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="semantic-loading"
              className={PANEL_CLASS}
              style={PANEL_STYLE}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {[...Array(3)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </motion.div>
          ) : results?.semantic.length === 0 ? (
            <EmptyState type="semantic" />
          ) : (
            <motion.div
              key="semantic-results"
              className={PANEL_CLASS}
              style={PANEL_STYLE}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {results?.semantic.map((r, i) => (
                <SemanticResultCard key={r.title} result={r} index={i} />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {results && results.semantic.length > 0 && (
          <VectorViz
            query={results.query}
            collection={results.collection}
          />
        )}
      </div>
    </div>
  );
}
