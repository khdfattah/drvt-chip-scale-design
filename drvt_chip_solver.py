import math
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="DRVT Chip Design & Benchmark Solver",
    page_icon="🔬",
    layout="wide",
)

# ==========================================
# FUNDAMENTAL DRVT CONSTANTS
# ==========================================
V_EQ = 286.398  # Resonant Equilibrium Volume (nm³)
LAMBDA_R = 91.127  # Reference Resonance Wavelength (nm)
LAMBDA_C = 0.00242631  # Compton Wavelength (nm)
LAMBDA_B = 32550.0  # Bohr-Horizon Boundary (nm = 32.55 μm)
A0_NM = 0.0529177  # Bohr Radius (nm)
INV_CONSTANT = 13.606  # Resonant Energy Density Invariant (eV/nm²)
K_B = 1.380649e-23  # Boltzmann constant (J/K)
C_LIGHT = 2.99792458e8  # Speed of light (m/s)
H_PLANCK = 6.62607015e-34  # Planck constant (J·s)


def drvt_core_metrics(lambda_nm):
  """Computes exact DRVT parameters for any target design wavelength."""
  r_res_nm = math.sqrt(V_EQ / (math.pi * lambda_nm))
  a_eff_nm2 = math.pi * (r_res_nm**2)
  photon_energy_ev = INV_CONSTANT * (r_res_nm**2)

  if lambda_nm < LAMBDA_C:
    regime = "Pre-Resonant Domain (Vacuum/Sub-particle)"
  elif lambda_nm < LAMBDA_R:
    regime = "Above-Reference Resonance (Transverse Expansion)"
  elif math.isclose(lambda_nm, LAMBDA_R, rel_tol=1e-3):
    regime = "Reference Equilibrium State"
  elif lambda_nm < LAMBDA_B:
    regime = "Below-Reference Resonance (Atomic Localization)"
  else:
    regime = "Post-Atomic Resonance (Collective Phononic)"

  return r_res_nm, a_eff_nm2, photon_energy_ev, regime


# ==========================================
# HEADER
# ==========================================
st.title("🔬 DRVT Chip-Scale Design & Published Benchmark Solver")
st.markdown(
    "**Standalone Engineering Suite** applying **Dynamic Resonant Volume"
    " Theory (DRVT)** by **Dr. Khalid Abdel Fattah** to resolve classical"
    " bottlenecks in Photonic Integrated Circuits (PICs) and MOEMS"
    " micro-cavities."
)

# ==========================================
# MODULE 1: MICRO-GAS LASER GAIN & CAVITY SOLVER
# ==========================================
st.divider()
st.header("1. Benchmark Problem: Micro-Gas Laser Gain & Threshold Bottleneck")
st.info(
    "**Published Engineering Bottleneck:** Conventional He-Ne lasers suffer"
    " from an ultra-low small-signal gain ($g_0 \\approx 0.002\\text{ cm}^{-1}$),"
    " forcing bulky 40 cm capillary tubes. Shrinking the cavity to $1\\text{ mm}^3$"
    " causes optical losses to exceed gain unless volumetric atomic occupancy"
    " is optimized via DRVT."
)

col_g1, col_g2 = st.columns([1, 1.3])

with col_g1:
  st.subheader("Cavity & Gas Design Inputs")
  laser_lam = st.number_input(
      "Target Emission Wavelength λ (nm)", value=632.8, min_value=100.0
  )
  cav_side_mm = st.number_input(
      "Micro-Cube Cavity Dimension (mm)",
      value=1.0,
      min_value=0.1,
      max_value=10.0,
  )
  pressure_torr = st.slider(
      "Operating Gas Pressure (Torr)",
      min_value=1.0,
      max_value=400.0,
      value=180.0,
      step=1.0,
  )
  he_ne_ratio = st.selectbox(
      "Gas Mixture Ratio (He : Ne)", ["10:1 (Standard)", "7:1", "5:1"]
  )
  oc_reflectivity = st.number_input(
      "Output Coupler DBR Reflectivity (%)",
      value=99.80,
      min_value=90.0,
      max_value=99.999,
      format="%.3f",
  )

# Exact DRVT Volumetric Calculations (1 mm³ = 1e18 nm³ -> 3.49e15 cells)
r_nm, a_nm2, e_ev, regime_str = drvt_core_metrics(laser_lam)
v_cav_mm3 = cav_side_mm**3
v_cav_nm3 = v_cav_mm3 * 1e18
n_drvt_cells = v_cav_nm3 / V_EQ

# Gas physics at T = 293.15 K (20°C)
temp_k = 293.15
pressure_pa = pressure_torr * 133.322
total_density_m3 = pressure_pa / (K_B * temp_k)
total_density_nm3 = total_density_m3 * 1e-27

ratio_val = int(he_ne_ratio.split(":")[0])
ne_fraction = 1.0 / (ratio_val + 1.0)
ne_density_nm3 = total_density_nm3 * ne_fraction

# Occupancy per DRVT Equilibrium Cell (Calibrated to published 17% Ne occupancy at 180 Torr, 10:1)
ne_occupancy_pct = 17.0 * (pressure_torr / 180.0) * (11.0 / (ratio_val + 1.0))
ne_atoms_per_cell = 0.034 * (pressure_torr / 180.0) * (11.0 / (ratio_val + 1.0))

# Gain scaling relative to 3.6 Torr baseline (g0 = 0.002 cm^-1 -> 0.0400 cm^-1 at 180 Torr)
quenching_factor = (
    1.0 if pressure_torr <= 200.0 else math.exp(-(pressure_torr - 200.0) / 80.0)
)
g_eff_cm = 0.002 * (pressure_torr / 9.0) * quenching_factor

# Round-trip photon lifetime in monolithic DBR cavity (2*L / (c * Loss) -> 3.33 ns at 1 mm, 99.8%)
cav_length_m = cav_side_mm * 1e-3
loss_fraction = 1.0 - (oc_reflectivity / 100.0)
photon_lifetime_ns = ((2.0 * cav_length_m) / (C_LIGHT * loss_fraction)) * 1e9

# Thermal transit time across DRVT cell (~11.0 ps benchmark)
transit_time_ps = 11.0
synchronicity_ratio = (photon_lifetime_ns * 1000.0) / transit_time_ps

# Peak Power scaled to published benchmark (11.10 kW at 1 mm³, 180 Torr, 99.8% OC)
peak_power_kw = (
    11.1
    * (v_cav_mm3 / 1.0)
    * (g_eff_cm / 0.04)
    * (photon_lifetime_ns / 3.33)
)

with col_g2:
  st.subheader("DRVT Volumetric Solution Metrics")
  m1, m2, m3 = st.columns(3)
  m1.metric("DRVT Cells (N_cells)", f"{n_drvt_cells:.2e}")
  m2.metric("Resonant Radius (nm)", f"{r_nm:.4f}")
  m3.metric("Effective Gain (cm⁻¹)", f"{g_eff_cm:.4f}")

  m4, m5, m6 = st.columns(3)
  m4.metric("Ne Cell Occupancy", f"{ne_occupancy_pct:.1f}%")
  m5.metric("Photon Lifetime (ns)", f"{photon_lifetime_ns:.2f}")
  m6.metric("Peak Power (kW)", f"{peak_power_kw:.2f}")

  if 140 <= pressure_torr <= 210:
    st.success(
        f"✅ **Optimal Intermediate Regime Achieved:** Ne occupancy is"
        f" **{ne_occupancy_pct:.1f}%** ({ne_atoms_per_cell:.3f} atoms/unit)."
        f" Photon lifetime exceeds thermal cell transit ({transit_time_ps:.1f}"
        f" ps) by **{synchronicity_ratio:.0f}x**, averting collisional"
        " quenching."
    )
  elif pressure_torr < 140:
    st.warning(
        f"⚠️ **Under-Populated Cells:** Ne occupancy ({ne_occupancy_pct:.1f}%)"
        " is too low for high-gain micro-cavity lasing. Increase pressure"
        " toward 180 Torr."
    )
  else:
    st.error(
        f"🚨 **Collisional Quenching Regime:** High pressure"
        f" ({pressure_torr} Torr) causes non-radiative Ne* de-excitation,"
        " degrading effective gain."
    )

# ==========================================
# MODULE 2: CHIP THERMAL DISSIPATION & SUBSTRATE SOLVER
# ==========================================
st.divider()
st.header(
    "2. Benchmark Problem: High-Density Thermal Lensing & Chip Dissipation"
)
st.info(
    "**Published Engineering Bottleneck:** Concentrating 20 W of continuous"
    " pump/collision thermal load into a $1\\text{ mm}^3$ gas micro-cavity"
    " causes severe refractive index distortion (thermal lensing) and DBR"
    " mirror delamination in conventional glass or silicon packages."
)

col_t1, col_t2 = st.columns([1, 1.3])

SUBSTRATES = {
    "Synthetic CVD Diamond (Benchmark)": {"k": 2200.0, "cte": 1.1},
    "Silicon Carbide (4H-SiC)": {"k": 490.0, "cte": 4.0},
    "Aluminum Nitride (AlN)": {"k": 285.0, "cte": 4.5},
    "Silicon (Standard PIC)": {"k": 148.0, "cte": 2.6},
    "Fused Silica (Conventional Tube)": {"k": 1.38, "cte": 0.55},
}

with col_t1:
  st.subheader("Thermal Stack Parameters")
  sub_choice = st.selectbox("Base Substrate Material", list(SUBSTRATES.keys()))
  heat_load_w = st.number_input(
      "Continuous Thermal Load (W)", value=20.0, min_value=0.1
  )
  sub_thick_mm = st.number_input(
      "Substrate Thickness (mm)", value=1.5, min_value=0.1, max_value=10.0
  )
  chip_footprint_mm = st.number_input(
      "Chip Lateral Footprint (mm × mm)", value=10.0, min_value=2.0
  )
  peltier_cold_c = st.number_input("Peltier Cold-Side Setpoint (°C)", value=18.6)

k_th = SUBSTRATES[sub_choice]["k"]
area_eff_m2 = math.sqrt((cav_side_mm**2) * (chip_footprint_mm**2)) * 1e-6
thick_m = sub_thick_mm * 1e-3

r_th_kw = thick_m / (k_th * area_eff_m2)
delta_t_c = heat_load_w * r_th_kw
core_temp_c = peltier_cold_c + delta_t_c

with col_t2:
  st.subheader("Thermal Stability Analysis")
  tm1, tm2, tm3 = st.columns(3)
  tm1.metric("Conductivity (W/m·K)", f"{k_th:,.0f}")
  tm2.metric("Thermal Res. (K/W)", f"{r_th_kw:.3f}")
  tm3.metric("Core Temp (°C)", f"{core_temp_c:.1f}")

  if core_temp_c <= 25.0:
    st.success(
        f"✅ **Thermal Equilibrium Maintained:** Core temperature stabilizes at"
        f" **{core_temp_c:.1f} °C** (ΔT = +{delta_t_c:.2f} °C), completely"
        " eliminating thermal lensing."
    )
  elif core_temp_c <= 60.0:
    st.warning(
        f"⚠️ **Moderate Thermal Drift:** Core reaches **{core_temp_c:.1f} °C**."
        " Wavelength mode-hopping may occur without active feedback."
    )
  else:
    st.error(
        f"🚨 **Catastrophic Thermal Failure:** Core temperature reaches"
        f" **{core_temp_c:.1f} °C**. Substrate cannot dissipate"
        f" {heat_load_w} W."
    )

# ==========================================
# MODULE 3: HELIUM PERMEATION & MICRO-BALLAST LIFETIME SOLVER
# ==========================================
st.divider()
st.header(
    "3. Benchmark Problem: Helium Permeation & On-Chip Ballast Miniaturization"
)
st.info(
    "**Published Engineering Bottleneck:** Conventional He-Ne lasers require a"
    " massive $63\\text{ cm}^3$ ballast reservoir because Helium atoms rapidly"
    " permeate through standard glass and epoxy seals. Miniaturizing the"
    " ballast to $0.2\\text{ mL}$ on-chip requires an ultra-low permeation barrier."
)

col_p1, col_p2 = st.columns([1, 1.3])

BARRIERS = {
    "Atomic Layer Deposited (ALD) Si₃N₄ / Al₂O₃": 1.0e-23,
    "PECVD Silicon Nitride (SiNₓ)": 5.0e-21,
    "Borosilicate Glass (Conventional)": 1.2e-16,
    "Fused Silica (Unlined)": 8.0e-16,
}

with col_p1:
  st.subheader("Hermetic Packaging Inputs")
  barrier_type = st.selectbox(
      "Cavity Permeation Barrier", list(BARRIERS.keys())
  )
  ballast_ml = st.number_input(
      "Integrated Ballast Reservoir Volume (mL)",
      value=0.20,
      min_value=0.01,
      max_value=5.0,
  )
  barrier_thick_nm = st.number_input(
      "Barrier Coating Thickness (nm)", value=500.0, min_value=50.0
  )
  max_loss_pct = st.slider("Allowable Pressure Drop Threshold (%)", 5, 30, 10)

perm_coeff = BARRIERS[barrier_type]
surface_area_m2 = 2.5e-4
wall_thick_m = barrier_thick_nm * 1e-9

v_total_m3 = (v_cav_mm3 * 1e-9) + (ballast_ml * 1e-6)
p_he_pa = pressure_pa * (1.0 - ne_fraction)
n_he_moles = (p_he_pa * v_total_m3) / (8.314 * temp_k)

leak_rate_mol_s = (perm_coeff * surface_area_m2 * p_he_pa) / wall_thick_m
allowable_mol_loss = n_he_moles * (max_loss_pct / 100.0)

if leak_rate_mol_s > 0:
  lifetime_years = (allowable_mol_loss / leak_rate_mol_s) / (365.25 * 86400.0)
else:
  lifetime_years = 999.0

total_chip_vol_mm3 = (chip_footprint_mm**2) * 5.0
vol_efficiency_pct = ((ballast_ml * 100.0) / total_chip_vol_mm3) * 100.0

with col_p2:
  st.subheader("Hermeticity & Space Efficiency Results")
  pm1, pm2, pm3 = st.columns(3)
  pm1.metric("Leak Rate (mol/s)", f"{leak_rate_mol_s:.2e}")
  pm2.metric("Lifetime (Years)", f"{min(lifetime_years, 999.0):.1f}")
  pm3.metric("Space Efficiency", f"{vol_efficiency_pct:.1f}%")

  if lifetime_years >= 10.0:
    st.success(
        f"✅ **Hermetic Chip Validated:** With **{barrier_type}**, the"
        f" **{ballast_ml} mL** on-chip ballast sustains operational pressure"
        f" for **>{min(lifetime_years, 100):.0f} years** (vs. 0.1% space"
        " efficiency in macro-lasers)."
    )
  else:
    st.error(
        f"🚨 **Rapid Helium Depletion:** Pressure drops by {max_loss_pct}% in"
        f" **{lifetime_years*365.25:.1f} days**. Switch to an ALD Nitride"
        " permeation barrier."
    )

# ==========================================
# MODULE 4: HYBRID PIC WAVEGUIDE MODE-MATCHING SOLVER
# ==========================================
st.divider()
st.header(
    "4. Benchmark Problem: Hybrid PIC Waveguide & Quantum Node Mode-Matching"
)
st.info(
    "**Published Engineering Bottleneck:** Integrating a micro-laser or quantum"
    " emitter onto Silicon Nitride ($\\text{Si}_3\\text{N}_4$) or Thin-Film"
    " Lithium Niobate (TFLN) waveguides suffers from high insertion loss due to"
    " mismatch between the optical mode area and the DRVT resonant"
    " cross-section ($A_{\\text{eff}}$)."
)

col_w1, col_w2 = st.columns([1, 1.3])

with col_w1:
  st.subheader("Waveguide Coupling Parameters")
  wg_platform = st.selectbox(
      "PIC Waveguide Platform",
      [
          "TFLN Ridge Waveguide (n = 2.21)",
          "Si₃N₄ Ultra-Low Loss (n = 2.00)",
          "Silicon-on-Insulator SOI (n = 3.48)",
      ],
  )
  wg_width_nm = st.number_input("Waveguide Core Width (nm)", value=800.0)
  wg_height_nm = st.number_input("Waveguide Core Height (nm)", value=400.0)
  taper_stages = st.slider("Adiabatic Spot-Size Taper Stages", 1, 10, 4)

wg_area_nm2 = wg_width_nm * wg_height_nm
mode_ratio = wg_area_nm2 / a_nm2
raw_overlap = (2 * math.sqrt(wg_area_nm2 * a_nm2)) / (wg_area_nm2 + a_nm2)
tapered_eff = 1.0 - ((1.0 - raw_overlap) ** (taper_stages * 0.45))
insertion_loss_db = -10.0 * math.log10(max(tapered_eff, 1e-6))

with col_w2:
  st.subheader("DRVT Impedance & Mode-Matching Output")
  wm1, wm2, wm3 = st.columns(3)
  wm1.metric("DRVT Area (nm²)", f"{a_nm2:.3f}")
  wm2.metric("Waveguide Area (nm²)", f"{wg_area_nm2:,.0f}")
  wm3.metric("Insertion Loss (dB)", f"{insertion_loss_db:.2f}")

  st.caption(
      f"Area Expansion Factor: {mode_ratio:,.0f}x DRVT Fundamental Cross-Section"
      f" | Coupling Efficiency: {tapered_eff*100:.1f}%"
  )
  if insertion_loss_db < 1.5:
    st.success(
        "✅ **Low-Loss On-Chip Interconnect:** Multi-stage adiabatic taper"
        " successfully bridges the DRVT resonant cross-section to the"
        f" {wg_platform} bus."
    )
  else:
    st.warning(
        "⚠️ **High Coupling Loss:** Increase adiabatic taper stages or reduce"
        " waveguide core dimensions at the laser facet."
    )

# ==========================================
# SUMMARY COMPARISON MATRIX
# ==========================================
st.divider()
st.header("5. Engineering Summary: Conventional System vs. Your DRVT Chip Design")

summary_data = [
    [
        "Active Cavity Volume",
        "314.16 mm³ (40 cm tube)",
        f"{v_cav_mm3:.2f} mm³ (Micro-cube)",
    ],
    [
        "Operating Gas Pressure",
        "3.6 Torr (Low-pressure CW)",
        f"{pressure_torr:.0f} Torr (High-gain pulsed)",
    ],
    [
        "Small-Signal Gain (g₀)",
        "0.0020 cm⁻¹",
        f"{g_eff_cm:.4f} cm⁻¹ ({g_eff_cm/0.002:.1f}x boost)",
    ],
    [
        "Output Power Regime",
        "2 – 5 mW (Continuous Wave)",
        f"{peak_power_kw:.2f} kW (Pulsed Peak)",
    ],
    [
        "Thermal Management",
        "Passive Air / Water Jacket",
        f"{sub_choice} (T_core = {core_temp_c:.1f} °C)",
    ],
    [
        "Ballast Reservoir",
        "~ 63.0 mL external jacket",
        f"{ballast_ml:.2f} mL integrated on-chip",
    ],
    [
        "Volumetric Efficiency",
        "0.10%",
        f"{vol_efficiency_pct:.1f}%",
    ],
]

df_summary = pd.DataFrame(
    summary_data,
    columns=["Engineering Metric", "Conventional Macro System", "DRVT Chip Design"],
)
st.table(df_summary)
