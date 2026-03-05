"use client";

import { motion } from "framer-motion";
import { BM25Result, SemanticResult } from "@/lib/api";
import { HighlightText } from "./HighlightText";
import { ExplainerTooltip } from "./ExplainerTooltip";

const BM25_SCORE_TOOLTIP = {
  title: "BM25 Score",
  body: "Term frequency × inverse document frequency, normalized by document length. Higher scores mean more exact word matches — BM25 only counts words that literally appear in the document.",
};

const CERTAINTY_TOOLTIP = {
  title: "Match Confidence",
  body: "Cosine similarity between the query embedding and the document embedding, expressed as a percentage. 100% means identical meaning. Above 85% is a strong semantic match even without shared words.",
};

interface BM25CardProps {
  result: BM25Result;
  index: number;
  queryTerms?: string[];
}

export function BM25ResultCard({ result, index, queryTerms = [] }: BM25CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.07,
        type: "spring",
        stiffness: 200,
        damping: 20,
      }}
      exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
      className={`p-6 transition-colors hover:bg-[#00ffff]/10 ${index === 0 ? "border-l-8 border-l-[#00ffff]" : ""}`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <div className="data-label mb-1">Document_Title</div>
          <h3 className="font-black text-lg leading-tight uppercase text-black truncate">
            {result.title}
          </h3>
        </div>
        <ExplainerTooltip title={BM25_SCORE_TOOLTIP.title} body={BM25_SCORE_TOOLTIP.body}>
          <div className="flex-shrink-0 text-right">
            <div className="data-label mb-1">BM25_Score</div>
            <span className="bg-black px-2 py-0.5 font-black font-mono text-sm" style={{ color: "#00ffff" }}>
              {result.score.toFixed(3)}
            </span>
          </div>
        </ExplainerTooltip>
      </div>
      <div className="bg-black/5 p-3 border-2 border-black/10 font-mono text-xs">
        <HighlightText text={result.description} terms={queryTerms} />
      </div>
    </motion.div>
  );
}

interface SemanticCardProps {
  result: SemanticResult;
  index: number;
}

export function SemanticResultCard({ result, index }: SemanticCardProps) {
  const pct = result.certainty != null
    ? (result.certainty * 100).toFixed(2)
    : result.distance != null
      ? ((1 - result.distance) * 100).toFixed(2)
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.07,
        type: "spring",
        stiffness: 200,
        damping: 20,
      }}
      exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
      className="p-6 transition-colors hover:bg-[#ff00ff]/5"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <div className="data-label mb-1">Document_Title</div>
          <h3 className="font-black text-lg leading-tight uppercase text-black truncate">
            {result.title}
          </h3>
        </div>
        {pct != null && (
          <ExplainerTooltip title={CERTAINTY_TOOLTIP.title} body={CERTAINTY_TOOLTIP.body}>
            <div className="flex-shrink-0 text-right">
              <div className="data-label mb-1" style={{ color: "#ff00ff" }}>Match_Confidence</div>
              <span className="font-black text-2xl italic leading-none" style={{ color: "#ff00ff" }}>
                {pct}%
              </span>
            </div>
          </ExplainerTooltip>
        )}
      </div>
      <div className="bg-black/5 p-3 border-2 border-black/10 font-mono text-xs">
        {result.description}
      </div>
    </motion.div>
  );
}
