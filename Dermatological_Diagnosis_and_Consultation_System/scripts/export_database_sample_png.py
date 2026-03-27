"""
Generate a client-shareable PNG of key database tables for ClearDerm (this repo).
Matches Django default table names: auth_user, patient_patient, doctor_doctor, hospital_hospital.

Output: static/database-design-clearerm-client.png
"""
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "static" / "database-design-clearerm-client.png"

HEADER = ["Fieldname", "Datatype", "Key / notes"]

# Condensed but accurate vs models.py + Django User
TABLES = [
    (
        "auth_user (Django built-in login)",
        [
            ["id", "integer", "Primary key"],
            ["username", "varchar(150)", "unique"],
            ["email", "varchar(254)", ""],
            ["password", "varchar(128)", "hashed"],
            ["first_name", "varchar(150)", ""],
            ["last_name", "varchar(150)", ""],
            ["is_active", "boolean", ""],
            ["date_joined", "datetime", ""],
        ],
    ),
    (
        "patient_patient",
        [
            ["id", "integer", "Primary key"],
            ["user_id", "integer", "OneToOne → auth_user"],
            ["age", "integer", ""],
            ["gender", "varchar(1)", "M / F / O"],
            ["phone_number", "varchar(15)", "nullable"],
            ["date_of_birth", "date", "nullable"],
            ["address", "text", "nullable"],
            ["created_at", "datetime", "auto"],
        ],
    ),
    (
        "doctor_doctor",
        [
            ["id", "integer", "Primary key"],
            ["user_id", "integer", "OneToOne → auth_user"],
            ["license_number", "varchar(50)", "unique"],
            ["specialization", "varchar(50)", ""],
            ["phone_number", "varchar(15)", ""],
            ["years_of_experience", "integer", ""],
            ["hospital_id", "integer", "FK → hospital_hospital, nullable"],
            ["created_by_hospital", "boolean", ""],
            ["created_at", "datetime", "auto"],
        ],
    ),
    (
        "hospital_hospital",
        [
            ["id", "integer", "Primary key"],
            ["user_id", "integer", "OneToOne → auth_user"],
            ["hospital_name", "varchar(200)", ""],
            ["registration_number", "varchar(50)", "unique"],
            ["address", "text", ""],
            ["phone_number", "varchar(15)", ""],
            ["email", "varchar(254)", ""],
            ["total_beds", "integer", ""],
            ["created_at", "datetime", "auto"],
        ],
    ),
]


def style_table(tbl) -> None:
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1e40af")
            cell.set_text_props(color="white", fontweight="bold", fontsize=10)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#e2e8f0")
            cell.set_edgecolor("#cbd5e1")
            cell.set_text_props(fontsize=9)
            cell.PAD = 0.10


def main() -> None:
    fig = plt.figure(figsize=(17.5, 20))
    fig.patch.set_facecolor("#f4f6f8")

    fig.suptitle(
        "Database Design — Key Tables (ClearDerm)",
        fontsize=18,
        fontweight="bold",
        color="#0f172a",
        y=0.988,
    )
    fig.text(
        0.5,
        0.964,
        "Django ORM · SQLite (default) · Table names match migrate output",
        ha="center",
        fontsize=11,
        color="#475569",
    )
    fig.text(
        0.5,
        0.947,
        "Core profiles only; other tables include patient_appointment, patient_chatmessage, doctor_appointmentschedule, patient_prescription, etc.",
        ha="center",
        fontsize=9,
        color="#64748b",
    )

    heights = [8.5, 8.5, 9.5, 9.5]
    gs = gridspec.GridSpec(
        4,
        1,
        figure=fig,
        left=0.06,
        right=0.94,
        top=0.91,
        bottom=0.055,
        hspace=0.32,
        height_ratios=heights,
    )

    for idx, (title, rows) in enumerate(TABLES):
        ax = fig.add_subplot(gs[idx, 0])
        ax.axis("off")
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color="#0f172a", pad=10)

        tbl = ax.table(
            cellText=rows,
            colLabels=HEADER,
            loc="upper center",
            cellLoc="left",
            colWidths=[0.22, 0.18, 0.58],
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1, 1.55)
        style_table(tbl)

    fig.text(
        0.5,
        0.02,
        "PK = Primary key | FK = Foreign key | OneToOne enforces one profile row per User",
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
