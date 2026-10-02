import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import io

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Enterprise Structural Studio",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Enterprise Structural Studio & Multi-Storey Simulator")
st.write(
    "Multi-parametric structural calculator for load distribution, "
    "stress, simplified buckling analysis, analytics, and PDF export."
)


# ============================================================
# 2. MATERIAL DATABASE
# ============================================================

material_database = {
    "Concrete M20": {
        "E": 22.3e9,
        "strength": 20.0,
        "density": 2400,
        "cost_per_unit": 5000,
        "category": "Concrete"
    },
    "Concrete M25": {
        "E": 25.0e9,
        "strength": 25.0,
        "density": 2400,
        "cost_per_unit": 5500,
        "category": "Concrete"
    },
    "Concrete M30": {
        "E": 27.3e9,
        "strength": 30.0,
        "density": 2500,
        "cost_per_unit": 6200,
        "category": "Concrete"
    },
    "Concrete M40": {
        "E": 31.6e9,
        "strength": 40.0,
        "density": 2500,
        "cost_per_unit": 7500,
        "category": "Concrete"
    },
    "Concrete M50": {
        "E": 35.3e9,
        "strength": 50.0,
        "density": 2550,
        "cost_per_unit": 9000,
        "category": "Concrete"
    },
    "Structural Steel (Fe 415)": {
        "E": 200.0e9,
        "strength": 250.0,
        "density": 7850,
        "cost_per_unit": 480000,
        "category": "Steel"
    },
    "Structural Steel (Fe 500)": {
        "E": 200.0e9,
        "strength": 300.0,
        "density": 7850,
        "cost_per_unit": 520000,
        "category": "Steel"
    },
    "Structural Steel (Fe 550)": {
        "E": 200.0e9,
        "strength": 350.0,
        "density": 7850,
        "cost_per_unit": 560000,
        "category": "Steel"
    },
    "Teak Wood (Sagwan)": {
        "E": 11.0e9,
        "strength": 15.0,
        "density": 720,
        "cost_per_unit": 85000,
        "category": "Timber"
    },
    "Granite Stone Masonry": {
        "E": 45.0e9,
        "strength": 60.0,
        "density": 2650,
        "cost_per_unit": 12000,
        "category": "Rocks / Stones"
    }
}


# ============================================================
# 3. SIDEBAR CONTROLS
# ============================================================

st.sidebar.header("1. Material Specification")

selected_material = st.sidebar.selectbox(
    "Material Type",
    list(material_database.keys())
)

material = material_database[selected_material]

E = material["E"]
yield_strength = material["strength"]
density = material["density"]
cost_per_m3 = material["cost_per_unit"]
category = material["category"]


st.sidebar.header("2. Building Multi-Storey Setup")

floors = st.sidebar.slider(
    "Number of Floors (Storeys)",
    min_value=1,
    max_value=20,
    value=3,
    step=1
)

floor_load_kN = st.sidebar.slider(
    "Average Load Per Floor (kN)",
    min_value=50,
    max_value=1500,
    value=400,
    step=50
)


st.sidebar.header("3. Main Column Geometry")

height = st.sidebar.slider(
    "Total Column Height (meters)",
    min_value=1.0,
    max_value=20.0,
    value=5.0,
    step=0.5
)

thickness = st.sidebar.slider(
    "Cross-Section Thickness (meters)",
    min_value=0.05,
    max_value=2.0,
    value=0.45,
    step=0.05
)


# ============================================================
# 4. STRUCTURAL CALCULATIONS
# ============================================================

# Square column cross-sectional area
area = thickness ** 2

# Column volume
volume = area * height

# Mass
self_weight_kg = volume * density

# Self-weight converted to kN
self_weight_kN = (self_weight_kg * 9.81) / 1000.0

# Applied building load
applied_building_load_kN = floors * floor_load_kN

# Total axial load
total_load_kN = applied_building_load_kN + self_weight_kN


# ------------------------------------------------------------
# Compressive stress
# ------------------------------------------------------------

compressive_stress = (
    (total_load_kN * 1000.0) / area
) / 1e6


# ------------------------------------------------------------
# Simplified Euler buckling
# ------------------------------------------------------------

I = (thickness ** 4) / 12.0

P_critical_kN = (
    (np.pi ** 2 * E * I) / (height ** 2)
) / 1000.0


# Factor of safety
if total_load_kN > 0:
    fos = P_critical_kN / total_load_kN
else:
    fos = float("inf")


# ============================================================
# 5. COST CALCULATION
# ============================================================

total_cost_inr = volume * cost_per_m3


# ============================================================
# 6. UTILIZATION
# ============================================================

if yield_strength > 0:
    stress_utilization = (
        compressive_stress / yield_strength
    ) * 100.0
else:
    stress_utilization = 0.0


if P_critical_kN > 0:
    buckling_utilization = (
        total_load_kN / P_critical_kN
    ) * 100.0
else:
    buckling_utilization = float("inf")


stress_utilization = min(float(stress_utilization), 200.0)
buckling_utilization = min(float(buckling_utilization), 200.0)

max_utilization = max(
    stress_utilization,
    buckling_utilization
)


# ============================================================
# 7. SAFETY CHECK
# ============================================================

stress_ok = compressive_stress < yield_strength
buckling_ok = total_load_kN < P_critical_kN

is_safe = stress_ok and buckling_ok

if is_safe:
    fail_mode = "None"
elif not stress_ok:
    fail_mode = "Crushing"
else:
    fail_mode = "Buckling"


# ============================================================
# 8. MAIN DASHBOARD
# ============================================================

d_col1, d_col2 = st.columns([3, 2])


# ============================================================
# LEFT COLUMN
# ============================================================

with d_col1:

    st.subheader("📊 Analytical Performance Dashboard")

    if is_safe:
        st.success(
            f"🟢 **SIMPLIFIED CHECK PASSED:** "
            f"The calculated load is below the simplified "
            f"stress and Euler buckling limits for the "
            f"{floors}-storey input."
        )
    else:
        st.error(
            f"🔴 **SIMPLIFIED CHECK FAILED:** "
            f"The calculated governing condition is {fail_mode}."
        )


    # --------------------------------------------------------
    # Dashboard Row 1
    # --------------------------------------------------------

    gr1_c1, gr1_c2, gr1_c3 = st.columns(3)

    gr1_c1.metric(
        "Total Load on Base",
        f"{total_load_kN:.1f} kN",
        f"Building: {applied_building_load_kN:.1f} kN"
    )

    gr1_c2.metric(
        "Total Material Mass",
        f"{self_weight_kg:,.1f} kg",
        f"Volume: {volume:.3f} m³"
    )

    gr1_c3.metric(
        "Estimated Material Cost",
        f"₹ {total_cost_inr:,.2f}"
    )


    # --------------------------------------------------------
    # Dashboard Row 2
    # --------------------------------------------------------

    gr2_c1, gr2_c2, gr2_c3 = st.columns(3)

    gr2_c1.metric(
        "Calculated Stress",
        f"{compressive_stress:.2f} MPa",
        f"Limit: {yield_strength:.1f} MPa",
        delta_color="inverse"
    )

    gr2_c2.metric(
        "Critical Buckling Load",
        f"{P_critical_kN:,.1f} kN",
        f"Factor of Safety: {fos:.2f}x"
    )

    gr2_c3.metric(
        "Maximum Utilization",
        f"{max_utilization:.1f}%"
    )


    # ========================================================
    # 9. OPTIMIZATION ADVISORY
    # ========================================================

    st.markdown("### 💡 Design Optimization Advisory")

    if is_safe:

        if max_utilization < 15.0:

            st.warning(
                "Material utilization is relatively low under "
                "the simplified model. A smaller section may be "
                "possible, but actual structural design requires "
                "code-based checks before changing dimensions."
            )

        else:

            st.info(
                "The simplified stress and buckling calculations "
                "are within the configured limits."
            )

    else:

        # Required thickness based on compressive stress
        req_thick_stress = np.sqrt(
            (total_load_kN * 1000.0)
            / (yield_strength * 1e6)
        )

        # Required thickness based on Euler buckling
        req_thick_buckle = (
            (
                total_load_kN
                * 1000.0
                * height ** 2
                * 12.0
            )
            / (np.pi ** 2 * E)
        ) ** 0.25

        recommended_t = max(
            req_thick_stress,
            req_thick_buckle
        )

        st.error(
            f"Calculated minimum thickness under this simplified "
            f"model: approximately **{recommended_t:.2f} m**."
        )


    # ========================================================
    # 10. PDF GENERATION
    # ========================================================

    def generate_pdf_report():

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter
        )

        styles = getSampleStyleSheet()

        story = []

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=12
        )

        text_style = ParagraphStyle(
            "TextStyle",
            parent=styles["Normal"],
            spaceAfter=8,
            fontSize=11
        )

        story.append(
            Paragraph(
                "<b>STRUCTURAL STABILITY "
                "& VERIFICATION REPORT</b>",
                title_style
            )
        )

        story.append(Spacer(1, 10))

        if is_safe:
            status_text = (
                "<b>STATUS: SIMPLIFIED CHECK PASSED</b>"
            )
        else:
            status_text = (
                f"<b>STATUS: SIMPLIFIED CHECK FAILED "
                f"({fail_mode})</b>"
            )

        story.append(
            Paragraph(
                status_text,
                text_style
            )
        )

        story.append(Spacer(1, 10))


        data = [
            ["Parameter", "Configured / Calculated Value"],
            ["Selected Material", selected_material],
            ["Material Category", category],
            ["Number of Storeys", f"{floors} Floors"],
            ["Average Floor Load", f"{floor_load_kN:.1f} kN"],
            ["Total Height", f"{height:.2f} m"],
            ["Column Thickness", f"{thickness:.2f} m"],
            ["Column Area", f"{area:.4f} m²"],
            ["Column Volume", f"{volume:.3f} m³"],
            ["Column Mass", f"{self_weight_kg:,.1f} kg"],
            ["Total Base Load", f"{total_load_kN:.1f} kN"],
            ["Calculated Stress", f"{compressive_stress:.2f} MPa"],
            ["Material Strength Input", f"{yield_strength:.1f} MPa"],
            ["Euler Buckling Threshold", f"{P_critical_kN:.1f} kN"],
            ["Factor of Safety", f"{fos:.2f}x"],
            ["Estimated Material Cost", f"INR {total_cost_inr:,.2f}"]
        ]


        table = Table(
            data,
            colWidths=[200, 250]
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1A365D")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT"
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    8
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.HexColor("#F7FAFC")
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10
                )
            ])
        )

        story.append(table)

        story.append(Spacer(1, 15))

        story.append(
            Paragraph(
                "<b>Important:</b> This report is generated "
                "from a simplified educational structural model. "
                "It is not a professional structural-engineering "
                "certificate and does not replace analysis according "
                "to applicable building codes, load combinations, "
                "reinforcement requirements, connections, foundations, "
                "wind, seismic, fire, or serviceability checks.",
                text_style
            )
        )

        doc.build(story)

        buffer.seek(0)

        return buffer


    # ========================================================
    # 11. PDF EXPORT
    # ========================================================

    st.write("### 🖨️ Export Design Dossier")

    pdf_data = generate_pdf_report()

    st.download_button(
        label="📥 Download PDF Stability Report",
        data=pdf_data,
        file_name="Structural_Stability_Report.pdf",
        mime="application/pdf"
    )


# ============================================================
# RIGHT COLUMN
# ============================================================

with d_col2:

    st.subheader("📐 Physical Deflection & Matrix Previews")


    # --------------------------------------------------------
    # Deflection profile
    # --------------------------------------------------------

    z = np.linspace(
        0,
        height,
        100
    )

    if not is_safe and fail_mode == "Buckling":

        x = (
            0.18
            * np.sin(
                np.pi * z / height
            )
        )

    else:

        x = np.zeros_like(z)


    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(4, 8.5),
        gridspec_kw={
            "height_ratios": [2, 1]
        }
    )


    # --------------------------------------------------------
    # Chart 1
    # --------------------------------------------------------

    line_color = (
        "blue"
        if is_safe
        else "red"
    )

    ax1.plot(
        x,
        z,
        label="Axis Matrix",
        color=line_color,
        linewidth=4
    )

    ax1.fill_betweenx(
        z,
        x - thickness / 2.0,
        x + thickness / 2.0,
        color="gray",
        alpha=0.35
    )

    ax1.set_xlim(
        -1.0,
        1.0
    )

    ax1.set_ylim(
        0,
        height + 0.5
    )

    ax1.set_ylabel(
        "Height Vector (m)"
    )

    ax1.set_title(
        "Structural Bending Node Profile"
    )

    ax1.grid(
        True,
        linestyle="--",
        alpha=0.4
    )


    # --------------------------------------------------------
    # Chart 2
    # --------------------------------------------------------

    bar_labels = [
        "Total Load",
        "Buckling Cap"
    ]

    bar_values = [
        total_load_kN,
        P_critical_kN
    ]

    bar_colors = [
        "#E53E3E" if not is_safe else "#3182CE",
        "#38A169"
    ]

    ax2.bar(
        bar_labels,
        bar_values,
        color=bar_colors
    )

    ax2.set_ylabel(
        "Force Scale (kN)"
    )

    ax2.set_title(
        "Load Metrics vs System Capacity"
    )

    ax2.grid(
        True,
        linestyle="--",
        alpha=0.3
    )


    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)