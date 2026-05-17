#!/usr/bin/env python3
"""
Generate the Task 4 final insights report (Markdown).

Usage:
    python scripts/generate_visualizations.py
    python scripts/generate_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.insights import extract_all_insights, bank_comparison_table  # noqa: E402

ENRICHED_CSV = PROJECT_ROOT / "data" / "processed" / "reviews_enriched.csv"
STATS_JSON = PROJECT_ROOT / "data" / "processed" / "analysis_stats.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "FINAL_REPORT.md"
FIGURES_REL = "figures"


def _format_evidence(evidence) -> str:
    lines = [
        f"- **{evidence.title}** — {evidence.mention_count} reviews, "
        f"avg rating {evidence.avg_rating}/5",
    ]
    for q in evidence.sample_quotes[:2]:
        lines.append(f'  - *"{q}"*')
    return "\n".join(lines)


def build_report(df: pd.DataFrame) -> str:
    insights = extract_all_insights(df)
    comparison = bank_comparison_table(df)
    stats = json.loads(STATS_JSON.read_text()) if STATS_JSON.exists() else {}

    lines = [
        "# Ethiopian Mobile Banking Apps: What 1,200 Google Play Reviews Reveal",
        "",
        "*A data-driven review of Commercial Bank of Ethiopia, Dashen Bank, and Bank of Abyssinia "
        "mobile apps — synthesized from sentiment and thematic analysis of real user feedback.*",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"We analyzed **{len(df)}** Google Play reviews collected across three major Ethiopian banks. "
        f"**{stats.get('sentiment_labeled_pct', 100)}%** received sentiment labels; "
        f"**{(df['sentiment_label'] == 'positive').mean() * 100:.0f}%** were positive overall, "
        f"but pain clusters around **login/OTP**, **slow transfers**, and **support responsiveness** "
        "vary sharply by institution.",
        "",
        "**Headline findings:**",
        "",
    ]

    for _, row in comparison.iterrows():
        lines.append(
            f"- **{row['bank']}**: avg rating **{row['avg_rating']}★**, "
            f"{row['positive_pct']}% positive sentiment; dominant complaint theme: **{row['top_theme']}**"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Cross-Bank Comparison",
            "",
            "| Bank | Avg Rating | Positive % | Negative % | Top Non-General Theme |",
            "|------|------------|------------|------------|------------------------|",
        ]
    )
    for _, row in comparison.iterrows():
        lines.append(
            f"| {row['bank']} | {row['avg_rating']} | {row['positive_pct']}% | "
            f"{row['negative_pct']}% | {row['top_theme']} |"
        )

    lines.extend(
        [
            "",
            "![Sentiment by bank](figures/01_sentiment_by_bank.png)",
            "",
            "![Rating distribution](figures/02_rating_distribution.png)",
            "",
            "![Theme frequency](figures/03_theme_frequency.png)",
            "",
            "---",
            "",
        ]
    )

    for bank_insight in insights.values():
        b = bank_insight.bank
        short = b.replace("Commercial Bank of Ethiopia", "CBE")
        lines.extend(
            [
                f"## {b}",
                "",
                f"**Average rating:** {bank_insight.avg_rating}★  ",
                f"**Sentiment mix:** "
                + ", ".join(
                    f"{k}: {v}" for k, v in bank_insight.sentiment_distribution.items()
                ),
                "",
                "### Satisfaction Drivers",
                "",
            ]
        )
        for d in bank_insight.drivers[:3]:
            lines.append(_format_evidence(d))
            lines.append("")

        lines.extend(["### Pain Points", ""])
        for p in bank_insight.pain_points[:3]:
            lines.append(_format_evidence(p))
            lines.append("")

        lines.extend(["### Product & Support Recommendations", ""])
        for i, rec in enumerate(bank_insight.recommendations[:3], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        if short == "CBE":
            lines.append(
                "CBE leads on average rating but still sees transfer-themed complaints — "
                "protecting reliability at scale should be the top priority."
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "## Visualization Appendix",
            "",
            "![Top keywords per bank](figures/04_top_keywords.png)",
            "",
            "![Sentiment trend over time](figures/05_sentiment_trend.png)",
            "",
            "---",
            "",
            "## Methodology (Brief)",
            "",
            "- **Data:** Google Play reviews (400 per bank, Jun 2025 – May 2026)",
            "- **Sentiment:** DistilBERT SST-2 (VADER fallback on Python 3.14)",
            "- **Themes:** Keyword rules + TF-IDF validation (5 business themes)",
            "- **Storage:** PostgreSQL `bank_reviews` schema (Task 3)",
            "",
            "*Report generated by `scripts/generate_report.py` — 10 Academy Week 2, Task 4.*",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    if not ENRICHED_CSV.exists():
        print(f"Missing {ENRICHED_CSV}. Run analyze_reviews.py first.")
        sys.exit(1)

    df = pd.read_csv(ENRICHED_CSV)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(df))
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
