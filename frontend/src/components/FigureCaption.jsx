import React, { useState } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";

/**
 * FigureCaption
 * -------------
 * Provides a two-level publication caption:
 * - Level 1 (always visible): Figure number, title, and 1-2 sentence core takeaway.
 * - Level 2 (expandable): Detailed interpretation, confidence intervals, and caveats.
 */
export default function FigureCaption({
  figNumber = "FIG. 1",
  title,
  takeaway,
  details,
  defaultExpanded = false,
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="mt-6 pt-5 border-t border-[#e5e0d4] text-[16px] font-sans text-[#2f2d2a] leading-relaxed">
      {/* Primary visible caption level */}
      <p className="max-w-[80ch]">
        <strong className="font-mono text-[#15263a] mr-2 font-semibold text-[15px]">
          {figNumber}.
        </strong>
        {title && <span className="font-semibold text-[#15263a] mr-1.5">{title}.</span>}
        <span className="text-[#3c3a37]">{takeaway}</span>
      </p>

      {details && (
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          className="mt-3 inline-flex items-center gap-1.5 text-[14px] font-mono text-[#23527c] hover:text-[#15263a] transition-colors underline decoration-[#23527c]/40 underline-offset-4 hover:decoration-[#15263a] py-1"
        >
          <span>{isExpanded ? "Hide detailed notes" : "Statistical notes & caveats"}</span>
          {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      )}

      {/* Expandable level 2 notes */}
      {details && isExpanded && (
        <div className="mt-3 border border-dashed border-[#dcd7ca] bg-[#f9f7f2] p-5 text-[15px] text-[#4a4740] space-y-3 rounded-none font-sans leading-relaxed">
          <div className="flex items-center gap-2 text-[#15263a] font-mono font-semibold text-[13px]">
            <Info size={13} className="text-[#23527c]" />
            <span>Methodological Details & Statistical Parameters</span>
          </div>
          <div className="text-[#3c3a37] leading-relaxed">{details}</div>
        </div>
      )}
    </div>
  );
}
