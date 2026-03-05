"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SearchBar } from "@/components/SearchBar";
import { ResultsPanel } from "@/components/ResultsPanel";
import { ExampleQueries } from "@/components/ExampleQueries";
import { HybridSearchPanel } from "@/components/HybridSearchPanel";
import { searchDual, getDatasets, DualSearchResponse, DatasetInfo } from "@/lib/api";

const STATIC_DATASET_INFO: Record<string, DatasetInfo> = {
  Landmarks: {
    name: "Landmarks",
    description: "World-famous landmarks with descriptions, countries, and categories.",
    record_count: 250,
    fields: ["title", "description", "country", "category"],
    seeded: true,
  },
  Movies: {
    name: "Movies",
    description: "Classic and contemporary films with plot summaries.",
    record_count: 300,
    fields: ["title", "plot", "genre", "year"],
    seeded: true,
  },
  Science: {
    name: "Science",
    description: "Scientific concepts with explanations across physics, biology, astronomy, and more.",
    record_count: 200,
    fields: ["concept", "explanation", "field"],
    seeded: true,
  },
  Games: {
    name: "Games",
    description: "Steam games with descriptions, genres, and developers.",
    record_count: 5000,
    fields: ["title", "description", "genre", "developer", "year"],
    seeded: true,
  },
  Pokemon: {
    name: "Pokemon",
    description: "Pokémon with Pokédex entries, types, and abilities.",
    record_count: 1025,
    fields: ["title", "description", "type", "generation", "abilities"],
    seeded: true,
  },
};

const spring = { type: "spring" as const, stiffness: 280, damping: 22 };
const springBouncy = { type: "spring" as const, stiffness: 400, damping: 18 };

export default function Home() {
  const [query, setQuery] = useState("");
  const [dataset, setDataset] = useState("Landmarks");
  const [results, setResults] = useState<DualSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [datasetInfoMap, setDatasetInfoMap] = useState<Record<string, DatasetInfo>>(STATIC_DATASET_INFO);

  useEffect(() => {
    getDatasets().then((datasets) => {
      setDatasetInfoMap((prev) => {
        const updated = { ...prev };
        for (const d of datasets) {
          if (updated[d.name]) {
            updated[d.name] = { ...updated[d.name], record_count: d.record_count, seeded: d.seeded };
          }
        }
        return updated;
      });
    }).catch(() => { /* keep static fallback */ });
  }, []);
  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchDual(query.trim(), dataset);
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }, [query, dataset]);

  const handleExampleSelect = useCallback(
    async (q: string) => {
      setQuery(q);
      setLoading(true);
      setError(null);
      try {
        const data = await searchDual(q.trim(), dataset);
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
      } finally {
        setLoading(false);
      }
    },
    [dataset],
  );

  return (
    <>
      <main className="min-h-screen">
        <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">

          {/* Hero Header */}
          <motion.header
            initial={{ opacity: 0, y: -24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.05 }}
          >
            <motion.div
              className="inline-block bg-black text-white text-[10px] font-mono font-bold px-3 py-1 uppercase tracking-widest mb-3"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ ...springBouncy, delay: 0.15 }}
            >
              Weaviate Playground System v2.0.4
            </motion.div>
            <motion.h2
              className="text-4xl md:text-5xl font-black uppercase tracking-tighter italic leading-none"
              style={{ fontFamily: "var(--font-space-grotesk)" }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ ...spring, delay: 0.1 }}
            >
              Search Algorithm
              <br />
              Analysis Suite
            </motion.h2>
          </motion.header>

          {/* Search section */}
          <motion.div
            className="space-y-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.2 }}
          >
            <SearchBar
              query={query}
              setQuery={setQuery}
              dataset={dataset}
              setDataset={(d) => {
                setDataset(d);
                setResults(null);
              }}
              onSearch={handleSearch}
              loading={loading}
              datasetInfo={datasetInfoMap[dataset]}
            />
            <ExampleQueries dataset={dataset} onSelect={handleExampleSelect} />
          </motion.div>

          {/* Results */}
          <ResultsPanel results={results} loading={loading} error={error} />

          {/* Hybrid Search Panel */}
          <AnimatePresence>
            {results && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={spring}
              >
                <HybridSearchPanel query={results.query} collection={results.collection} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <motion.footer
        className="border-t-4 border-black bg-white mt-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ ...spring, delay: 0.6 }}
      >
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="font-mono text-[10px] opacity-40 uppercase tracking-wide">
            Build_Hash: 8f2a11b9c // Power_User_Mode: Active
          </span>
          <div className="flex items-center gap-2">
            {["#00ffff", "#ff00ff", "#ffff00", "#000000"].map((color, i) => (
              <motion.div
                key={color}
                className="w-4 h-4 border-2 border-black"
                style={{ backgroundColor: color }}
                initial={{ opacity: 0, scale: 0.4 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ ...springBouncy, delay: 0.65 + i * 0.07 }}
              />
            ))}
          </div>
        </div>
      </motion.footer>
    </>
  );
}
