"use client";

interface Props {
  text: string;
  terms: string[];
  className?: string;
}

export function HighlightText({ text, terms, className }: Props) {
  if (!terms.length) {
    return <span className={className}>{text}</span>;
  }

  const escaped = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = text.split(pattern);

  return (
    <span className={className}>
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <mark
            key={i}
            className="px-0.5 font-bold"
            style={{ backgroundColor: "#00ffff", color: "#000" }}
          >
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </span>
  );
}
