"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { getSuggestions } from "@/lib/api";

const FALLBACK_QUERIES: Record<string, string[]> = {
  Landmarks: [
    "landmark in France",
    "ancient ruins by the sea",
    "big waterfall in North America",
  ],
  Movies: [
    "film about artificial intelligence and emotions",
    "movie where poor people trick rich people",
    "heist movie set inside the mind",
  ],
  Science: [
    "why is the sky blue",
    "invisible matter in the universe",
    "how life adapts over generations",
  ],
  Games: [
    "open world RPG with crafting",
    "horror survival game",
    "racing game with customization",
  ],
  Pokemon: [
    "electric mouse pokemon",
    "legendary dragon that controls time",
    "ghost type haunting old buildings",
  ],
};

interface Props {
  dataset: string;
  onSelect: (query: string) => void;
}

export function ExampleQueries({ dataset, onSelect }: Props) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getSuggestions(dataset, 3)
      .then((data) => {
        if (!cancelled) setSuggestions(data.slice(0, 3));
      })
      .catch(() => {
        if (!cancelled) setSuggestions(FALLBACK_QUERIES[dataset] || []);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [dataset]);

  if (loading) {
    return (
      <div className="flex flex-wrap gap-2 items-center">
        <span className="data-label mr-1">Try:</span>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-7 w-28 bg-white border-2 border-black animate-pulse" />
        ))}
      </div>
    );
  }

  const queries = (suggestions.length ? suggestions : FALLBACK_QUERIES[dataset] || []).slice(0, 3);

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <span className="data-label mr-1">Try:</span>
      {queries.map((q, i) => (
        <motion.button
          key={q}
          onClick={() => onSelect(q)}
          className="neo-button text-xs py-1 px-3 border-2 font-normal normal-case tracking-normal"
          style={{ boxShadow: "2px 2px 0px 0px #000000" }}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 20, delay: i * 0.05 }}
          whileHover={{ y: -2, boxShadow: "4px 6px 0px 0px #000000" }}
          whileTap={{ y: 2, boxShadow: "0px 0px 0px 0px #000000", scale: 0.97 }}
        >
          {q}
        </motion.button>
      ))}
    </div>
  );
}
