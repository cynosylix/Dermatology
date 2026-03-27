"""
Generate a client-shareable PNG of the DFD summary tables.

Output: static/dfd-summary-tables-client.png
"""
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "static" / "dfd-summary-tables-client.png"


def main() -> None:
    fig = plt.figure(figsize=(18, 10.2))
    fig.patch.set_facecolor("#f4f6f8")

    fig.suptitle(
        "ClearDerm — Data Flow Diagram (DFD) Summary",
        fontsize=18,
        fontweight="bold",
        color="#0f172a",
        y=0.985,
    )
    fig.text(
        0.5,
        0.958,
        "Dermatology Diagnosis and Consultation System · Levels 0–2",
        ha="center",
        fontsize=12,
        color="#475569",
    )
    fig.text(
        0.5,
        0.94,
        "Client copy: table-style DFD reference",
        ha="center",
        fontsize=10,
        color="#64748b",
    )

    gs = gridspec.GridSpec(
        2,
        1,
        figure=fig,
        left=0.04,
        right=0.96,
        top=0.89,
        bottom=0.09,
        hspace=0.30,
        height_ratios=[0.56, 0.44],
    )

    # --- Table 1 ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis("off")

    headers1 = [
        "DFD level",
        "Figure file (static/)",
        "Report §",
        "What the diagram shows",
        "Main symbols",
    ]
    rows1 = [
        [
            "0",
            "dfd-level-0.png",
            "§10.1",
            "Context: one system ClearDerm (P0) with Patient, Doctor, Hospital, Email SMTP, and SQLite / Media / ML stores",
            "P0, E1–E4, D1–D3",
        ],
        [
            "1",
            "dfd-level-1.png",
            "§10.2",
            "P0 decomposed: Patient / Doctor / Hospital portals, Auth session, Chatbot ML, Notification, data stores",
            "P1–P6, E1–E4, D1–D3",
        ],
        [
            "2",
            "dfd-level-2.png",
            "§10.3",
            "Detail: Patient ↔ Patient Portal ↔ Chatbot ML → Database, Media, ML models",
            "E1, P1, P5, D1–D3",
        ],
    ]

    tbl1 = ax1.table(
        cellText=rows1,
        colLabels=headers1,
        loc="upper center",
        cellLoc="left",
        colWidths=[0.06, 0.18, 0.08, 0.48, 0.18],
    )
    tbl1.auto_set_font_size(False)
    tbl1.set_fontsize(10)
    tbl1.scale(1, 1.9)

    for (row, col), cell in tbl1.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1e40af")
            cell.set_text_props(color="white", fontweight="bold", fontsize=10)
            cell.set_height(0.11)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#e2e8f0")
            cell.set_edgecolor("#cbd5e1")
            cell.PAD = 0.09

    ax1.text(
        0,
        1.06,
        "DFD summary (quick reference)",
        transform=ax1.transAxes,
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
    )

    # --- Table 2 ---
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.axis("off")

    headers2 = ["Label often used on PNG", "ID in technical report"]
    rows2 = [
        ["ClearDerm", "P0 (Level 0 only)"],
        ["Patient / Doctor / Hospital", "E1, E2, E3"],
        ["Email SMTP", "E4"],
        ["SQLite / SQLite DB / Database", "D1"],
        ["Media / Media storage", "D2"],
        ["ML / ML models / ML artifacts", "D3"],
        ["Patient portal", "P1 (Levels 1–2)"],
        ["Chatbot ML", "P5"],
    ]

    tbl2 = ax2.table(
        cellText=rows2,
        colLabels=headers2,
        loc="upper center",
        cellLoc="left",
        colWidths=[0.52, 0.48],
    )
    tbl2.auto_set_font_size(False)
    tbl2.set_fontsize(10)
    tbl2.scale(1, 1.4)

    for (row, col), cell in tbl2.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1e40af")
            cell.set_text_props(color="white", fontweight="bold", fontsize=10)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#e2e8f0")
            cell.set_edgecolor("#cbd5e1")
            cell.PAD = 0.10

    ax2.text(
        0,
        1.08,
        "Diagram labels vs report IDs (same meaning, different wording on figures)",
        transform=ax2.transAxes,
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
    )

    fig.text(
        0.5,
        0.035,
        "E = external entity | P = process | D = data store",
        ha="center",
        fontsize=9,
        color="#64748b",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
