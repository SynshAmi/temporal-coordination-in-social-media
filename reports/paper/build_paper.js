// Builds the IEEE A4 conference-format research paper (.docx).
// Template geometry and named styles reproduce IEEE "conference-template-a4".
// All tabulated numbers are read from the project's verified artifacts.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, SectionType, LevelFormat, LevelSuffix, TabStopType, BorderStyle,
  VerticalAlign, Math: OMath, MathRun, MathFraction, MathSubScript, MathSuperScript,
  MathSubSuperScript, MathSum, MathRadical, MathRoundBrackets,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const OUT = path.join(ROOT, "reports", "LEN_Small_Measurement_Validity_Audit_Research_Paper.docx");
const FIG = path.join(ROOT, "reports", "paper", "figures");

// Every reported number comes from the corrected run's verified results file.
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs/run_v2/paper_results.json"), "utf8"));
if (!R.source_run.endsWith("run_v2")) throw new Error("paper must be built from outputs/run_v2");

// ---- geometry (twips; 1 mm = 56.693 twips) -------------------------------
const mm = (v) => Math.round(v * 56.6929);
const PAGE = { width: 11906, height: 16838 }; // A4
const MARGIN = { top: mm(19), bottom: mm(43), left: mm(14.32), right: mm(14.32) };
const COL_GAP = mm(4.22);
const COL_W = mm(88.9); // single column width
const FULL_W = PAGE.width - MARGIN.left - MARGIN.right;

// ---- helpers ------------------------------------------------------------------
const f3 = (v) => (v == null ? "—" : Number(v).toFixed(3));
const fmtInt = (v) => Math.round(v).toLocaleString("en-US");

// Inline markup: *italic*, **bold**, ^sup^, ~sub~
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|\^[^^]+\^|~[^~]+~)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("*")) out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else if (t.startsWith("^")) out.push(new TextRun({ text: t.slice(1, -1), superScript: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), subScript: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (text) => new Paragraph({ style: "BodyText", children: runs(text) });
const H1 = (text) => new Paragraph({ style: "Heading1", numbering: { reference: "heads", level: 0 }, children: [new TextRun(text)] });
const H2 = (text) => new Paragraph({ style: "Heading2", numbering: { reference: "heads", level: 1 }, children: [new TextRun(text)] });
const bullet = (text) => new Paragraph({ style: "BulletList", numbering: { reference: "bullets", level: 0 }, children: runs(text) });

function figure(file, caption) {
  const buf = fs.readFileSync(path.join(FIG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); // PNG IHDR
  const widthPx = 330; // ~3.44 in at 96 dpi, fits the 3.5 in column
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: widthPx, height: Math.round((h / w) * widthPx) },
        altText: { title: caption.split(".")[0], description: caption, name: file } })],
    }),
    new Paragraph({ style: "figurecaption", children: runs(caption) }),
  ];
}

const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
function table(title, header, rows, widths, footnote) {
  const total = widths.reduce((a, b) => a + b, 0);
  const mk = (txt, opts = {}) => new TableCell({
    width: { size: widths[opts.i], type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 30, bottom: 30, left: 60, right: 60 },
    borders: { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder },
    children: [new Paragraph({ keepNext: true, keepLines: true, style: opts.head ? "tablecolhead" : "tablecopy", alignment: opts.align ?? (opts.i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER), children: runs(String(txt)) })],
  });
  const out = [
    new Paragraph({ style: "tablehead", keepNext: true, children: runs(title.replace("\t", " ")) }),
    new Table({
      width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
      rows: [
        new TableRow({ tableHeader: true, children: header.map((h, i) => mk(h, { i, head: true, align: AlignmentType.CENTER })) }),
        ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => mk(c, { i })) })),
      ],
    }),
  ];
  if (footnote) out.push(new Paragraph({ style: "tablefootnote", children: runs(footnote) }));
  else out.push(new Paragraph({ style: "BodyText", spacing: { after: 0 }, children: [] }));
  return out;
}

// Equation paragraph: centered math, number flush right (template convention)
// Equations are emitted as placeholders and converted into native Word
// equations (UnicodeMath build-up, numbered with #(n)) by finalize_equations.ps1.
const eq = (_unused, n) => new Paragraph({ style: "equation", alignment: AlignmentType.CENTER, children: [new TextRun(`[[EQ${n}]]`)] });
const mr = (t) => new MathRun(t);
const sub = (b, s) => new MathSubScript({ children: [mr(b)], subScript: [mr(s)] });
const sumN = (body) => new MathSum({ children: body, subScript: [mr("i=1")], superScript: [mr("n")] });

// ---- content (reports/paper/paper_content.js) -----------------------------------
const body = require("./paper_content.js")({ P, H1, H2, bullet, figure, table, eq, runs, Paragraph, TextRun }, R);

// ---- styles (IEEE conference template) ------------------------------------
const TNR = "Times New Roman";
const ps = (id, name, run, paragraph, extra = {}) => ({ id, name, basedOn: "Normal", quickFormat: true, run: { font: TNR, ...run }, paragraph, ...extra });
const styles = {
  default: { document: { run: { font: TNR, size: 20 } } },
  paragraphStyles: [
    ps("papertitle", "paper title", { size: 48 }, { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 120 } }),
    ps("Author", "Author", { size: 22 }, { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 } }),
    ps("AuthorItalic", "Author affiliation", { size: 20, italics: true }, { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 } }),
    ps("AuthorAffil", "Author details", { size: 20 }, { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 } }),
    ps("Abstract", "Abstract", { size: 18, bold: true }, { alignment: AlignmentType.JUSTIFIED, spacing: { after: 200 }, indent: { firstLine: 274 } }),
    ps("Keywords", "Keywords", { size: 18, bold: true, italics: true }, { alignment: AlignmentType.JUSTIFIED, spacing: { after: 200 }, indent: { firstLine: 274 } }),
    { ...ps("Heading1", "Heading 1", { size: 20, smallCaps: true }, { alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true, keepLines: true }), next: "BodyText" },
    { ...ps("Heading2", "Heading 2", { size: 20, italics: true }, { alignment: AlignmentType.LEFT, spacing: { before: 120, after: 60 }, keepNext: true, keepLines: true }), next: "BodyText" },
    { ...ps("Heading5", "Heading 5", { size: 20, smallCaps: true }, { alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true }), next: "references" },
    ps("BodyText", "Body Text", { size: 20 }, { alignment: AlignmentType.JUSTIFIED, spacing: { after: 120, line: 228, lineRule: "exact" }, indent: { firstLine: 288 } }),
    ps("BulletList", "bullet list", { size: 20 }, { alignment: AlignmentType.JUSTIFIED, spacing: { after: 60, line: 228, lineRule: "exact" } }),
    ps("equation", "equation", { size: 20 }, { spacing: { before: 60, after: 120 } }),
    ps("figurecaption", "figure caption", { size: 16 }, { alignment: AlignmentType.JUSTIFIED, spacing: { before: 80, after: 200 }, tabStops: [{ type: TabStopType.LEFT, position: 540 }] }),
    ps("tablehead", "table head", { size: 16, smallCaps: true }, { alignment: AlignmentType.CENTER, spacing: { before: 240, after: 120 } }),
    ps("tablecolhead", "table col head", { size: 15, bold: true }, { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 } }),
    ps("tablecopy", "table copy", { size: 15 }, { spacing: { before: 0, after: 0 } }),
    ps("tablefootnote", "table footnote", { size: 12 }, { alignment: AlignmentType.RIGHT, spacing: { before: 60, after: 160 } }),
    ps("references", "references", { size: 16 }, { alignment: AlignmentType.JUSTIFIED, spacing: { after: 50, line: 180, lineRule: "exact" } }),
  ],
};

const numbering = {
  config: [
    { reference: "heads", levels: [
      { level: 0, format: LevelFormat.UPPER_ROMAN, text: "%1.", suffix: LevelSuffix.SPACE, alignment: AlignmentType.CENTER, style: { paragraph: { indent: { left: 0, hanging: 0 } } } },
      { level: 1, format: LevelFormat.UPPER_LETTER, text: "%2.", suffix: LevelSuffix.SPACE, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 288, hanging: 288 } } } },
    ] },
    { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 354, hanging: 354 } } } }] },
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 288, hanging: 216 } } } }] },
  ],
};

const pageProps = { size: PAGE, margin: { ...MARGIN, header: mm(12.7), footer: mm(12.7) } };

// Two co-authors side by side (IEEE template convention: authors left to right).
const AUTHORS = [
  { name: "Suryansh Singh", reg: "Reg. No. 245816214" },
  { name: "Devansh Kewlani", reg: "Reg. No. 245816052" },
];
const DEPT = ["Department of Computer Science and Engineering", "(Data Science)"];
const INST = "Manipal Institute of Technology, Bengaluru, India";
function authorBlock() {
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const colW = Math.floor(FULL_W / 2);
  const line = (text, style, extra = {}) => new Paragraph({ style, spacing: { before: 0, after: 0 }, ...extra, children: [new TextRun(text)] });
  return new Table({
    width: { size: colW * 2, type: WidthType.DXA }, columnWidths: [colW, colW], alignment: AlignmentType.CENTER,
    borders: { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ children: AUTHORS.map((a) => new TableCell({
      width: { size: colW, type: WidthType.DXA },
      borders: { top: none, bottom: none, left: none, right: none },
      margins: { top: 0, bottom: 0, left: 80, right: 80 },
      children: [
        line(a.name, "Author", { spacing: { before: 120, after: 20 } }),
        line(DEPT[0], "AuthorItalic"),
        line(DEPT[1], "AuthorItalic"),
        line(INST, "AuthorAffil"),
        line(a.reg, "AuthorAffil"),
      ],
    })) })],
  });
}

const doc = new Document({
  creator: "Suryansh Singh; Devansh Kewlani",
  title: "What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs",
  description: "Predictive-information audit of the LEN-Small benchmark (corrected run_v2 results)",
  styles, numbering,
  sections: [
    {
      properties: { page: pageProps, column: { count: 1 } },
      children: [
        new Paragraph({ style: "papertitle", children: [new TextRun("What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs")] }),
        authorBlock(),
        new Paragraph({ style: "Author", spacing: { before: 0, after: 240 }, children: [] }),
      ],
    },
    {
      properties: { type: SectionType.CONTINUOUS, page: pageProps, column: { count: 2, space: COL_GAP, equalWidth: true } },
      children: body,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT, buf.length, "bytes"); });
