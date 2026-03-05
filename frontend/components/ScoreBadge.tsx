"use client";

interface BM25BadgeProps {
  score: number;
}

export function BM25ScoreBadge({ score }: BM25BadgeProps) {
  return (
    <div className="mt-3 flex justify-between items-start">
      <div className="data-label">BM25_Score</div>
      <div className="font-black bg-black text-[#00ffff] px-2 font-mono text-sm">
        {score.toFixed(2)}
      </div>
    </div>
  );
}

interface SemanticBadgeProps {
  certainty: number | null;
  distance: number | null;
}

export function SemanticScoreBadge({ certainty, distance }: SemanticBadgeProps) {
  const pct = certainty !== null ? Math.round(certainty * 100) : null;
  return (
    <div className="mt-3">
      <div className="data-label">Match_Confidence</div>
      {pct !== null && (
        <div className="font-black text-2xl italic leading-none mt-1">{pct}%</div>
      )}
      {distance !== null && (
        <div className="data-label font-mono mt-1">dist: {distance.toFixed(3)}</div>
      )}
    </div>
  );
}
