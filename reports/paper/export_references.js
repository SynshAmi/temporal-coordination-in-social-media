// Writes the paper's reference list, in citation order, to the website
// (frontend/src/lib/references.json) so both use the same references.
// Usage: node reports/paper/export_references.js [output path]
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs/run_v2/paper_results.json"), "utf8"));
const buildContent = require("./paper_content.js");

// Minimal stand-ins for the docx helpers: only the reference paragraphs are kept.
class Paragraph { constructor(o) { Object.assign(this, o); } }
class TextRun { constructor(o) { this.o = o; } }
const stub = () => [];
const body = buildContent({
  P: () => ({}), H1: () => ({}), H2: () => ({}), bullet: () => ({}), figure: stub, table: stub, eq: () => ({}),
  runs: (text) => [text], Paragraph, TextRun,
}, R);

const refs = body.filter((p) => p instanceof Paragraph && p.style === "references").map((p) => p.children[0]);
const out = process.argv[2] ? path.resolve(process.argv[2]) : path.join(ROOT, "frontend/src/lib/references.json");
fs.writeFileSync(out, JSON.stringify(refs, null, 2) + "\n", "utf8");
console.log(`${refs.length} references -> ${path.relative(ROOT, out)}`);
