import React, { useLayoutEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

/**
 * Tex
 * ---
 * Renders a trusted, author-written TeX string with KaTeX's DOM API
 * (no innerHTML injection). Display equations scroll horizontally on
 * narrow screens instead of overflowing the page.
 */
export default function Tex({ children, display = false, className = "" }) {
  const ref = useRef(null);

  useLayoutEffect(() => {
    if (!ref.current) return;
    katex.render(String(children), ref.current, {
      displayMode: display,
      throwOnError: false,
      trust: false,
      strict: "warn",
    });
  }, [children, display]);

  return display ? (
    <div ref={ref} className={`tex-display ${className}`} />
  ) : (
    <span ref={ref} className={className} />
  );
}
