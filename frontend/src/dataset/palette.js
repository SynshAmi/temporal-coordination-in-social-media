// Visual encoding for the network canvases (dark slate ground, the site's muted red and blue).
//
// sigma.js blends with (ONE, ONE_MINUS_SRC_ALPHA) without premultiplying colours, so on a dark
// background overlapping translucent edges add up to white. Every colour here is therefore opaque:
// translucent tones are pre-blended with the canvas background.
export const BACKGROUND = "#12223a"; // keep in sync with .graph-canvas in index.css

function over(hex, alpha, bg = BACKGROUND) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [a, b] = [p(hex), p(bg)];
  return "#" + a.map((c, i) => Math.round(b[i] + alpha * (c - b[i])).toString(16).padStart(2, "0")).join("");
}

const SLATE = "#98acc6";
export const CANVAS = {
  campaign: "#c8665d", // muted red: events labelled campaign by the dataset
  comparison: "#6f9cc8", // muted blue: events labelled comparison by the dataset
  selected: "#f4efe6", // cream
  neighbour: "#e9dcc2",
  hub: "#d9a35b", // the site's amber accent
  dim: "#2a3a51",
  ghost: "#33445c", // nodes not in the current observation
  edge: over(SLATE, 0.32),
  edgeDense: over(SLATE, 0.22),
  edgeFaint: over(SLATE, 0.08),
  edgeDropped: over("#c8665d", 0.2),
  edgeObserved: over("#e9dcc2", 0.8),
  edgeHub: over("#d9a35b", 0.45),
  edgeOut: "#f1e6d0",
  edgeIn: "#d9a35b",
  label: "#e9e4d8",
};

export const LABEL_COLOR = { 1: CANVAS.campaign, 0: CANVAS.comparison };
export const LABEL_TEXT = { 1: "Campaign", 0: "Comparison" };
// Same hues on the light page (charts, badges)
export const PAGE = { campaign: "#8f2626", comparison: "#23527c", ink: "#15263a", muted: "#757065" };
