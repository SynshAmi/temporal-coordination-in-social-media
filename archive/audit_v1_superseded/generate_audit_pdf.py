"""
generate_audit_pdf.py
---------------------
Generates a publication-quality PDF version of the methodology audit:
frontend/public/LEN-Small_Methodology_Audit.pdf

Uses ReportLab (pure Python, zero native DLL dependencies).
"""

import sys
import json
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

sys.stdout.reconfigure(encoding="utf-8")


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and page numbers to each page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#757065"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                54, 750,
                "LEN-Small Benchmark Audit — Methodological Integrity & Robustness"
            )
            self.drawRightString(612 - 54, 750, "Independent Audit Report")
            self.setStrokeColor(colors.HexColor("#dcd7ca"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(54, 38, "Independent methodological audit • LEN-Small benchmark • Reproducibility archive")
        self.drawRightString(612 - 54, 38, page_str)
        self.setStrokeColor(colors.HexColor("#dcd7ca"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)

        self.restoreState()


def build_pdf(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    metrics = json.loads(Path("outputs/run_final/metrics.json").read_text(encoding="utf-8"))
    diag = json.loads(Path("data/manifests/matching_diagnostics.json").read_text(encoding="utf-8"))

    # Custom styles
    primary_navy = colors.HexColor("#15263a")
    accent_burgundy = colors.HexColor("#8f2626")
    body_charcoal = colors.HexColor("#2a2825")
    muted_gray = colors.HexColor("#6b6862")
    border_sand = colors.HexColor("#dcd7ca")

    doc_label_style = ParagraphStyle(
        "DocLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=accent_burgundy,
        textTransform="uppercase",
        spaceAfter=4,
    )

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_navy,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=11,
        leading=15,
        textColor=muted_gray,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_navy,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=primary_navy,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13.5,
        textColor=body_charcoal,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    callout_style = ParagraphStyle(
        "DocCallout",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=12.5,
        textColor=primary_navy,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=body_charcoal,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=primary_navy,
    )

    verdict_badge_style = ParagraphStyle(
        "VerdictBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.white,
        alignment=1,  # Centered
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph("Independent Methodological Verification Report", doc_label_style))
    story.append(Paragraph("Auditing Measurement Validity in Campaign Classification on LEN-Small", title_style))
    story.append(Paragraph("A Rigorous Evaluation of Size Confounding, Nearest-Neighbor Matching, and Restricted-Observation Transferability", subtitle_style))

    # Meta bar
    meta_data = [
        [
            Paragraph("<b>Document:</b> reports/methodology_audit.md", table_cell_style),
            Paragraph("<b>Target Dataset:</b> LEN-Small (103 Canonical Events)", table_cell_style),
            Paragraph("<b>Validation Status:</b> VERIFIED & REPRODUCIBLE", table_cell_bold),
        ],
        [
            Paragraph("<b>Protocol:</b> 5-Fold Stratified Cross-Validation", table_cell_style),
            Paragraph("<b>Evaluated Models:</b> LogReg (L2), HGBT Trees", table_cell_style),
            Paragraph("<b>Audit Date:</b> October 2026", table_cell_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[170, 180, 154])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f6f3eb")),
        ('BOX', (0, 0), (-1, -1), 0.5, border_sand),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e8e3d5")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section 1
    story.append(Paragraph("1. Executive Summary & Audit Verdict", h1_style))
    story.append(Paragraph(
        "This independent methodological audit verifies the experimental pipeline, mathematical claims, data handling integrity, and statistical boundaries of the study <i>'Beyond Graph Scale: Auditing Size Confounding and Retained-Observation Robustness in Campaign Classification on LEN-Small'</i>.",
        body_style
    ))
    story.append(Paragraph(
        "The core research finding is confirmed: <b>unconstrained campaign classification on LEN-Small is predominantly driven by graph scale</b> (log node count alone yields 0.8739 Balanced Accuracy, 95% CI: [0.805, 0.932]). However, size matching and observation budget restrictions reveal critical nuances that require precise methodological demarcation.",
        body_style
    ))

    # Findings Table
    findings_data = [
        [
            Paragraph("Dimension", table_header_style),
            Paragraph("Initial Guide Assumption", table_header_style),
            Paragraph("Verified Empirical Reality", table_header_style),
            Paragraph("Audit Verdict", table_header_style),
        ],
        [
            Paragraph("<b>Archive Format</b>", table_cell_style),
            Paragraph("ZIP archive with edgelists + CSV", table_cell_style),
            Paragraph("Single tar archive (<code>small_encoder_final.tar</code>) with 104 JSONs.", table_cell_style),
            Paragraph("<b>CORRECTED</b>", table_cell_bold),
        ],
        [
            Paragraph("<b>Cohort Size & Labels</b>", table_cell_style),
            Paragraph("100 events, standalone CSV", table_cell_style),
            Paragraph("103 canonical events (1 duplicate removed via SHA-256). Labels in filenames.", table_cell_style),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("<b>Size Distribution</b>", table_cell_style),
            Paragraph("Campaign assumed larger than comparison", table_cell_style),
            Paragraph("Inverted: Comparison is ~5x larger (median 3,227 vs 506 nodes).", table_cell_style),
            Paragraph("<b>AUDITED</b>", table_cell_bold),
        ],
        [
            Paragraph("<b>Scale Baseline</b>", table_cell_style),
            Paragraph("Assumed secondary to topology", table_cell_style),
            Paragraph("Dominant: Log node count achieves 0.8739 BA (95% CI [0.805, 0.932]).", table_cell_style),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("<b>Size Matching</b>", table_cell_style),
            Paragraph("Caliper matching on log node count", table_cell_style),
            Paragraph("16 pairs (n=32); |SMD| drops from 2.24 to 0.10 (signed: -2.24 to -0.10). Non-scale features retain 0.750 BA.", table_cell_style),
            Paragraph("<b>VERIFIED*</b>", table_cell_bold),
        ],
        [
            Paragraph("<b>Edge Budget (K=2000)</b>", table_cell_style),
            Paragraph("Feasible across all K in {250,500,1000,2000}", table_cell_style),
            Paragraph("Infeasible: Only 4 campaign graphs have >=2000 edges. 5-fold CV invalid.", table_cell_style),
            Paragraph("<b>EXCLUDED</b>", table_cell_bold),
        ],
        [
            Paragraph("<b>D1 vs D2 Observation</b>", table_cell_style),
            Paragraph("Retrained models called 'approximations'", table_cell_style),
            Paragraph("Fold-aligned frozen structural models (D1: 0.598 / 0.725 / 0.746 BA) vs retrained all-feature models (D2: 0.941 / 0.938 / 0.906). Not like-for-like.", table_cell_style),
            Paragraph("<b>CORRECTED</b>", table_cell_bold),
        ],
    ]
    findings_table = Table(findings_data, colWidths=[80, 130, 214, 80])
    findings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_navy),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#faf8f5"), colors.HexColor("#f0ede4")]),
        ('BOX', (0, 0), (-1, -1), 0.5, primary_navy),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_sand),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(findings_table)
    story.append(Spacer(1, 10))

    # Section 2
    story.append(Paragraph("2. Ingestion, Duplicate Handling & Leakage Prevention", h1_style))
    story.append(Paragraph(
        "<b>A. Canonical Deduplication:</b> During archive extraction, an exact binary duplicate was identified: <code>#SesimiziDuyanVarM[dotless i]___2023-03-23_campaign_fulldata.json</code> and its ASCII equivalent <code>...VarMi...</code> had identical SHA-256 hash (<code>57da6c194213...</code>). Ingestion script <code>src/ingest_len.py</code> logged the duplicate and retained exactly one canonical entry, establishing 103 verified event graphs.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>B. Feature Leakage Prevention:</b> Heavy 772-dim <code>node_attr</code> and 776-dim <code>edge_attr</code> continuous embeddings in the raw JSON files were discarded during ingestion. Feature matrices contain purely topological properties and aggregated text dispersion metrics. Event IDs, labels, fold IDs, and account usernames are strictly excluded from input tensors.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>C. Partitioning & Inner Tuning:</b> 5-fold cross-validation is partitioned strictly at the event level. Hyperparameter tuning for Logistic Regression regularization (C in {0.01, 0.1, 1.0, 10.0}) is performed via an inner 3-fold CV loop on the training fold only, avoiding optimistic bias.",
        bullet_style
    ))

    # Section 3
    story.append(Paragraph("3. Size Matching: Calibration & Statistical Limits", h1_style))
    story.append(Paragraph(
        "To evaluate whether non-scale topological indicators (degree Gini, reciprocity, coreness) possess predictive utility beyond graph size, 1:1 nearest-neighbor matching without replacement was performed on log(1 + N) with a caliper of 0.25 x SD (0.2859).",
        body_style
    ))
    story.append(Paragraph(
        f"<b>Verification Results:</b> The signed standardised mean difference (campaign minus comparison, pooled SD) moved from <b>{diag['smd_before']}</b> to <b>{diag['smd_after']}</b>, i.e. |SMD| {abs(diag['smd_before']):.2f} to {abs(diag['smd_after']):.2f}, across 16 matched pairs (32 total events). On this balanced cohort:",
        body_style
    ))
    story.append(Paragraph("• The scale model (log N + log E) drops from 0.8837 BA on the full cohort down to <b>0.5938 BA</b> (95% CI: [0.417, 0.753]), statistically overlapping random guessing (0.50).", bullet_style))
    story.append(Paragraph("• Structural features retain <b>0.6875 BA</b> (95% CI: [0.524, 0.857]), and content features retain <b>0.7500 BA</b> (95% CI: [0.598, 0.906]); these are exploratory results on 32 events.", bullet_style))
    story.append(Paragraph("• <i>Statistical Limitation:</i> Because N = 32, bootstrap 95% confidence intervals are broad (about +/-0.15). Matching acts as a diagnostic sensitivity stress-test rather than a definitive causal proof.", bullet_style))

    # Section 4
    story.append(Paragraph("4. Observation-Budget Robustness & Infeasibility at K=2000", h1_style))
    story.append(Paragraph(
        "Observation-budget sampling evaluated classifier resilience when only K in {250, 500, 1000} edges are observed:",
        body_style
    ))
    story.append(Paragraph("• <b>D2 (Retrained Models):</b> Classifiers trained and tested on sparse views remain accurate (BA >= 0.90 at every feasible budget). They use all 12 features recomputed on each sampled view.", bullet_style))
    d1 = {k: metrics[f"D1_K{k}_frozen"] for k in (250, 500, 1000)}
    story.append(Paragraph("• <b>D1 (Frozen Full-Graph Models):</b> The structural-group models from Exp A (7 features) are applied without retraining; each event is scored only by the fold model that held it out. BA: "
        + "; ".join(f"K={k}: <b>{v['balanced_accuracy']:.4f}</b> [{v['ba_ci_lower']:.3f}, {v['ba_ci_upper']:.3f}] vs {v['full_graph_reference_balanced_accuracy']:.4f} on complete graphs" for k, v in d1.items())
        + ". D1 and D2 use different feature sets, so their gap is not a controlled estimate of retraining. An earlier misaligned evaluation (superseded values 0.7558 and 0.8282 at K=500/1000) has been corrected.", bullet_style))
    story.append(Paragraph("• <b>K=2000 Infeasibility:</b> Only 4 campaign graphs have >= 2,000 edges. Partitioning 4 positive events into 5 cross-validation folds is mathematically impossible without producing empty positive test strata. K = 2000 was excluded from valid benchmark evaluation to avoid reporting distorted, unstratified metrics.", bullet_style))

    # Section 5: Verification Table
    story.append(Paragraph("5. Benchmark Metrics Verification Matrix", h1_style))
    matrix_rows = [
        ("B0a_log_node_logreg", "Scale: log N (full cohort)"),
        ("B0b_log_node_edge_logreg", "Scale: log N + log E (full cohort)"),
        ("A_combined_logreg", "All 12 features (full cohort)"),
        ("C_matched_scale_logreg", "Scale: log N + log E (matched)"),
        ("C_matched_structure_logreg", "Structure (matched)"),
        ("C_matched_content_logreg", "Content (matched)"),
        ("D2_K250", "D2 retrained, K=250 (12 features)"),
        ("D2_K500", "D2 retrained, K=500 (12 features)"),
        ("D2_K1000", "D2 retrained, K=1000 (12 features)"),
        ("D1_K250_frozen", "D1 frozen, K=250 (7 structural)"),
        ("D1_K500_frozen", "D1 frozen, K=500 (7 structural)"),
        ("D1_K1000_frozen", "D1 frozen, K=1000 (7 structural)"),
    ]
    metrics_summary_data = [[
        Paragraph("Experiment ID", table_header_style),
        Paragraph("Feature Set / Protocol", table_header_style),
        Paragraph("N", table_header_style),
        Paragraph("Bal. Acc (95% CI)", table_header_style),
        Paragraph("Macro-F1", table_header_style),
        Paragraph("ROC-AUC", table_header_style),
    ]]
    for key, label in matrix_rows:
        m = metrics[key]
        metrics_summary_data.append([
            Paragraph(f"<b>{key}</b>", table_cell_style),
            Paragraph(label, table_cell_style),
            Paragraph(str(m["n_events"]), table_cell_style),
            Paragraph(f"{m['balanced_accuracy']:.4f} [{m['ba_ci_lower']:.3f}, {m['ba_ci_upper']:.3f}]", table_cell_style),
            Paragraph(f"{m['macro_f1']:.4f}", table_cell_style),
            Paragraph(f"{m['roc_auc']:.4f}" if m.get("roc_auc") is not None else "-", table_cell_style),
        ])
    metrics_table = Table(metrics_summary_data, colWidths=[118, 150, 28, 110, 48, 50])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_navy),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#faf8f5"), colors.HexColor("#f0ede4")]),
        ('BOX', (0, 0), (-1, -1), 0.5, primary_navy),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_sand),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # Section 6: Audit Sign-off
    story.append(Paragraph("6. Audit Sign-Off & Methodological Verdict", h1_style))
    story.append(Paragraph(
        "<b>VERDICT: REPRODUCIBLE, WITH BOUNDED CLAIMS.</b> The pipeline is deterministic when seeded. A fold-alignment error in the frozen-model (D1) evaluation was found during the audit and corrected; the values above are the corrected results. Remaining limitations: 103 events (32 after matching); percentile-bootstrap intervals over fixed out-of-fold predictions that ignore refitting, fold-split, matched-pair and shared-account dependence; an unexplained difference between the analysed archive (104 files) and the documented LEN-Small release (100 graphs); and temporal features excluded because timestamp semantics are unverified.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF -> {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    out_pdf = Path("frontend/public/LEN-Small_Methodology_Audit.pdf")
    build_pdf(out_pdf)

    # Also copy markdown version for convenience
    out_md = Path("frontend/public/LEN-Small_Methodology_Audit.md")
    shutil.copy("reports/methodology_audit.md", out_md)
    print(f"Copied Markdown -> {out_md}")
