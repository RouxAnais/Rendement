import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import tempfile

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ---------------- CONFIG ----------------

st.title("Efficiency Analysis")
st.write("Diversification - NTN Europe")

uploaded_files = st.file_uploader(
    "Upload your CSV files",
    type=["csv"],
    accept_multiple_files=True
)


# ---------------- FUNCTIONS ----------------

def load_file(uploaded_file):

    raw_df = pd.read_csv(
        uploaded_file,
        sep=";",
        decimal=",",
        header=None,
        dtype=str
    )

    time_row = raw_df[raw_df[0] == "Temps"].index

    if len(time_row) == 0:
        return None

    uploaded_file.seek(0)

    df = pd.read_csv(
        uploaded_file,
        sep=";",
        decimal=",",
        skiprows=time_row[0]
    )

    df.columns = [
        "Time",
        "Torque_0_5",
        "Torque_0_50",
        "Force",
        "Displacement",
        "Raw_upward_efficiency",
        "Raw_downward_efficiency",
        "Upward",
        "Downward",
        "Upward_efficiency_stats",
        "Downward_efficiency_stats"
    ]

    df.columns = df.columns.str.strip()

    for col in ["Time", "Upward", "Downward"]:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.loc[df["Upward"] > 1, "Upward"] = None
    df.loc[df["Downward"] > 1, "Downward"] = None

    return df


def calculate_stats(df):

    q_low = df["Upward"].quantile(0.05)
    q_high = df["Upward"].quantile(0.95)
    df_up_clean = df[
        (df["Upward"] >= q_low) &
        (df["Upward"] <= q_high)
    ]

    q_low = df["Downward"].quantile(0.05)
    q_high = df["Downward"].quantile(0.95)
    df_down_clean = df[
        (df["Downward"] >= q_low) &
        (df["Downward"] <= q_high)
    ]

    average_upward = df_up_clean["Upward"].mean() * 100
    average_downward = df_down_clean["Downward"].mean() * 100

    return average_upward, average_downward


if uploaded_files:

    st.success(f"{len(uploaded_files)} file(s) uploaded")

    results = []
    files_data = []

    tabs = st.tabs([f"File {i+1}" for i in range(len(uploaded_files))])

    for i, file in enumerate(uploaded_files):

        df = load_file(file)

        if df is None:
            tabs[i].error("Unable to read this file.")
            continue

        average_upward, average_downward = calculate_stats(df)

        fig = px.line(
            df,
            x="Time",
            y=["Upward", "Downward"],
            labels={
                "value": "Efficiency",
                "variable": "Direction"
            },
            title=file.name,
            color_discrete_map={
                "Upward": "#A0AEC0",
                "Downward": "#E53935"
            }
        )

        tabs[i].plotly_chart(fig, use_container_width=True)

        tabs[i].subheader("Efficiency")

        col1, col2 = tabs[i].columns(2)

        col1.metric(
            label="Average upward efficiency",
            value=f"{average_upward:.2f} %"
        )

        col2.markdown(
            f"""
            Average downward efficiency  
            <span style='color:red; font-size:32px; font-weight:bold;'>
            {average_downward:.2f} %
            </span>
            """,
            unsafe_allow_html=True
        )

      
        results.append({
            "File": file.name,
            "Average upward efficiency (%)": round(average_upward, 2),
            "Average downward efficiency (%)": round(average_downward, 2)
        })

        files_data.append({
            "name": file.name,
            "df": df,
            "fig": fig,
            "average_upward": average_upward,
            "average_downward": average_downward
        })

    results_df = pd.DataFrame(results)

    st.subheader("Summary table")
    st.dataframe(results_df)

    # ---------------- EXCEL EXPORT ----------------

    excel_buffer = BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        results_df.to_excel(
            writer,
            index=False,
            sheet_name="Results"
        )

    st.download_button(
        label="📥 Download Excel summary",
        data=excel_buffer.getvalue(),
        file_name="efficiency_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------- PDF EXPORT ----------------

    pdf_buffer = BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#1f77b4"),
        fontSize=22,
        leading=26,
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#555555"),
        fontSize=12,
        leading=16,
        alignment=1
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#1f77b4"),
        fontSize=14,
        leading=18
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12
    )

    elements = []
  

    elements.append(
        Paragraph("Efficiency Analysis Report", title_style)
    )

    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(
            "Comparison of upward and downward efficiency",
            subtitle_style
        )
    )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            f"Number of files analyzed: <b>{len(results_df)}</b>",
            body_style
        )
    )

    elements.append(Spacer(1, 12))

    # Summary table
    table_data = [
        [
            "File",
            "DOWNWARD efficiency (%)",
            "Upward efficiency (%)"
        ]
    ]

    for _, row in results_df.iterrows():
        table_data.append([
            row["File"],
            row["Average downward efficiency (%)"],
            row["Average upward efficiency (%)"]
        ])

    table = Table(
        table_data,
        colWidths=[230, 150, 150]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f8fb")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),

        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Compact charts in portrait format
    for index, item in enumerate(files_data):

        chart_block = []

        chart_block.append(
            Paragraph(item["name"], heading_style)
        )

        chart_block.append(Spacer(1, 5))

        stats_table_data = [
            ["Indicator", "Value"],
            [
                "DOWNWARD efficiency",
                f"{item['average_downward']:.2f} %"
            ],
            [
                "Upward efficiency",
                f"{item['average_upward']:.2f} %"
            ]
        ]

        stats_table = Table(
            stats_table_data,
            colWidths=[260, 120]
        )

        stats_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f8fb")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),

            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),

            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),

            ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor("#E53935")),
            ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (1, 1), (1, 1), 11),
        ]))

        chart_block.append(stats_table)
        chart_block.append(Spacer(1, 8))

        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as tmpfile:

            item["fig"].write_image(
                tmpfile.name,
                width=900,
                height=430,
                scale=2
            )

            image_path = tmpfile.name

        img = Image(image_path)
        img.drawWidth = 520
        img.drawHeight = 250

        chart_block.append(img)
        chart_block.append(Spacer(1, 10))

        elements.append(KeepTogether(chart_block))

        # Si beaucoup de graphiques, on force une nouvelle page tous les 2 graphiques
        if (index + 1) % 2 == 0 and index != len(files_data) - 1:
            elements.append(PageBreak())

    doc.build(elements)

    st.download_button(
        label="📄 Download full PDF report",
        data=pdf_buffer.getvalue(),
        file_name="efficiency_analysis_report.pdf",
        mime="application/pdf"
    )

else:
    st.info("Upload one or more CSV files to start the analysis.")