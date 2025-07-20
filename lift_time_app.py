#!/usr/bin/env python3
"""
lift_time_app.py

Drone Lift & Flight Time Explorer (Extended Catalog)

• Fixed payload = 10 kg  
• Select from a wide range of T-Motor & heavy-lift motors  
• Slider for battery energy (Wh)  
• Computes: total thrust (N), available payload (kg), flight time (min), T/W ratio  
• Enforces min T/W = 1.6, rec T/W = 2.0 (with warnings)  
• Tab: Flight-time vs. battery curves (all motors), with shading for T/W zones
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Drone Lift & Flight Time Explorer", layout="wide")

# ─── Constants ────────────────────────────────────────────────────────────────
g = 9.81                   # m/s²
empty_mass = 5.0           # kg (frame + electronics)
payload_fixed = 10.0       # kg
specific_energy = 200.0    # Wh/kg (battery energy density)
power_req_coeff = 200.0    # W/kg (hover power coefficient)
tw_min = 1.6               # minimum T/W
tw_rec = 2.0               # recommended T/W

# ─── Motor catalog ────────────────────────────────────────────────────────────
motors = {
    # Mini-multirotor Antigravity series
    "MN5008 KV170":   {"thrust_kg":  4.0,  "motor_mass_kg": 0.32},
    "MN6007II KV320": {"thrust_kg":  5.5,  "motor_mass_kg": 0.30},
    "MN7005 KV115":   {"thrust_kg":  7.0,  "motor_mass_kg": 0.33},
    "MN7005 KV230":   {"thrust_kg":  6.0,  "motor_mass_kg": 0.28},
    "MN8012 KV100":   {"thrust_kg": 11.8,  "motor_mass_kg": 0.351},
    "MN8014 KV100":   {"thrust_kg": 13.9,  "motor_mass_kg": 0.392},
    "MN8017 KV120":   {"thrust_kg": 16.8,  "motor_mass_kg": 0.453},
    # Heavy-lift T-Motor series
    "U15II KV80":     {"thrust_kg": 36.5,  "motor_mass_kg": 1.74},
    "U15L KV43":      {"thrust_kg": 61.2,  "motor_mass_kg": 3.60},
    "U15XXL KV29":    {"thrust_kg":102.3,  "motor_mass_kg": 5.13},
    # Other examples
    "LIGPOWER U12II KV120": {"thrust_kg": 20.0,  "motor_mass_kg": 0.50},
    "SUPER-E S150":         {"thrust_kg": 90.0,  "motor_mass_kg": 9.10},
}

# ─── Sidebar inputs ────────────────────────────────────────────────────────────
motor_options = [
    f"{name} ({data['thrust_kg']} kgf)" for name, data in motors.items()
]
sel = st.sidebar.selectbox("Motor", motor_options)

# Fix: split on the last " (" so we recover the full key
motor_name = sel.rsplit(" (", 1)[0]
specs = motors[motor_name]

st.sidebar.markdown("**Motor Specs:**")
st.sidebar.write(f"- Max Thrust: **{specs['thrust_kg']} kgf**")
st.sidebar.write(f"- Motor Mass: **{specs['motor_mass_kg']} kg**")
st.sidebar.write(f"- Motor T/W: **{specs['thrust_kg']/specs['motor_mass_kg']:.1f}:1**")

battery_Wh = st.sidebar.slider(
    "Battery Energy (Wh)",
    min_value=500, max_value=40000, value=6000, step=100
)

# ─── Core calculations ─────────────────────────────────────────────────────────
battery_mass = battery_Wh / specific_energy

motor_thrust = specs["thrust_kg"]
# 8 motors: 4 @100% + 4 @70%
total_thrust_kgf = motor_thrust * (4 + 4 * 0.7)
total_thrust_N   = total_thrust_kgf * g

available_extra = total_thrust_kgf - (empty_mass + battery_mass + payload_fixed)
available_extra = max(0.0, available_extra)

total_mass = empty_mass + battery_mass + payload_fixed

P_hover = total_mass * power_req_coeff
flight_time_h   = battery_Wh / P_hover if P_hover>0 else 0.0
flight_time_min = flight_time_h * 60

T_W_ratio = total_thrust_kgf / total_mass if total_mass>0 else 0.0

# battery thresholds for shading
bat_mass_min = total_thrust_kgf/tw_min - empty_mass - payload_fixed
bat_mass_rec = total_thrust_kgf/tw_rec - empty_mass - payload_fixed
bat_Wh_min = max(0.0, bat_mass_min * specific_energy)
bat_Wh_rec = max(0.0, bat_mass_rec * specific_energy)

# ─── UI: Summary & Alerts ──────────────────────────────────────────────────────
st.title("Bramer Drone Lift & Flight Time Calculator")

st.markdown("### 📌 System Constants")
c1, c2, c3 = st.columns(3)
c1.metric("Empty Frame Mass", f"{empty_mass:.1f} kg")
c2.metric("Fixed Payload",    f"{payload_fixed:.1f} kg")
c3.metric("Hover Power Coeff.", f"{power_req_coeff:.0f} W/kg")

st.markdown("### 🔄 Intermediate Values")
c4, c5, c6, c7 = st.columns(4)
c4.metric("Battery Mass",        f"{battery_mass:.2f} kg")
c5.metric("Max Thrust Capability", f"{total_thrust_kgf:.2f} kgf")
c6.metric("Total Take-off Mass",   f"{total_mass:.2f} kg")
c7.metric("Total Thrust",          f"{total_thrust_N:.0f} N")

st.markdown("### 📊 Results")
r1, r2, r3 = st.columns(3)
r1.metric("Flight Time",          f"{flight_time_min:.1f} min")
r2.metric("Available Extra Payload", f"{available_extra:.2f} kg")
r3.metric("T/W Ratio",            f"{T_W_ratio:.2f}:1")

# T/W alerts
if T_W_ratio < tw_min:
    st.error(f"T/W {T_W_ratio:.2f} below min {tw_min:.1f}")
elif T_W_ratio < tw_rec:
    st.warning(f"T/W {T_W_ratio:.2f} ≥ min, below rec {tw_rec:.1f}")
else:
    st.success(f"T/W {T_W_ratio:.2f} ≥ recommended {tw_rec:.1f}")

# ─── Tabs: Flight Time Curves ─────────────────────────────────────────────────
tabs = st.tabs(["Overview", "Flight Time Curves","Time Ceiling Explanation"])
with tabs[1]:
    st.subheader("🔋 Flight Time vs. Battery for All Motors")
    fig, ax = plt.subplots(figsize=(8,5))
    bat_range = np.linspace(1000, 20000, 200)

    # collect all curves so we can scale Y
    all_times = []

    for name, data in motors.items():
        mt = data["thrust_kg"]
        tot_th = mt * (4 + 4*0.7)
        times = []
        for b in bat_range:
            bm = b / specific_energy
            tm = empty_mass + bm + payload_fixed
            ph = tm * power_req_coeff
            fh = (b / ph * 60) if ph>0 else 0
            times.append(fh)
        ax.plot(bat_range, times, label=f"{name} ({mt} kgf)")
        all_times += times

    # axis limits
    x0, x1 = bat_range[0], bat_range[-1]
    y_max = max(all_times)*1.05
    ax.set_xlim(x0, x1)
    ax.set_ylim(0, y_max)

    # thresholds (Wh) for T/W zones
    # battery mass thresholds -> Wh
    t_rec = bat_Wh_rec
    t_min = bat_Wh_min

    # 1) Safe zone (T/W ≥ 2.0): green from x0 up to t_rec
    ax.axvspan(x0, min(t_rec, x1), color="green", alpha=0.2, label="T/W ≥ 2.0")

    # 2) Warning zone (1.6 ≤ T/W < 2.0): yellow between t_rec and t_min
    if t_rec < x1 and t_rec < t_min:
        ax.axvspan(max(x0, t_rec), min(t_min, x1),
                   color="yellow", alpha=0.2, label="1.6 ≤ T/W < 2.0")

    # 3) Critical zone (T/W < 1.6): red above t_min
    if t_min < x1:
        ax.axvspan(max(x0, t_min), x1,
                   color="red", alpha=0.2, label="T/W < 1.6")

    # selected battery marker
    ax.axvline(battery_Wh, color="black", ls="--", label="Selected Battery")

    # labels, grid, legend
    ax.set_xlabel("Battery Energy (Wh)")
    ax.set_ylabel("Flight Time (min)")
    ax.set_title("Flight Time vs. Battery Energy")
    ax.legend(loc="upper right", fontsize="small", ncol=1)
    ax.grid(True, ls="--", alpha=0.5)
    fig.tight_layout()
    st.pyplot(fig)
with tabs[2]:
    st.subheader("🛑 Flight Time Ceiling")

    st.markdown(r"""
    $$
    \begin{aligned}
      &\underline{\textbf{1. Flight Time Formula:}}\\[4pt]
      &t_{\mathrm{hover}}
      = \frac{E_{\mathrm{batt}}}{P_{\mathrm{hover}}}
      = \frac{m_{\mathrm{batt}}\,E_d}{c\,\bigl(m_{\mathrm{fixed}} + m_{\mathrm{batt}}\bigr)}\\[8pt]

      &\underline{\textbf{2. Limit as }m_{\mathrm{batt}}\to\infty:}\\[4pt]
      &\lim_{m_{\mathrm{batt}}\to\infty} t_{\mathrm{hover}}
      = \lim_{m_{\mathrm{batt}}\to\infty}
        \frac{m_{\mathrm{batt}}\,E_d}{c\,\bigl(m_{\mathrm{fixed}} + m_{\mathrm{batt}}\bigr)}
      = \frac{E_d}{c}\\[8pt]

      &\text{With typical values }E_d = 200\;\mathrm{Wh/kg},\;c = 200\;\mathrm{W/kg}:\\[4pt]
      &\quad t_{\mathrm{hover}} = \frac{200}{200} = 1\;\mathrm{h}\\[8pt]

      &\underline{\textbf{3. Breaking the 1 h Ceiling:}}\quad
      \begin{cases}
        \text{Increase }E_d,\\
        \text{Decrease }c,\\
        \text{Reduce }m_{\mathrm{fixed}}.
      \end{cases}
    \end{aligned}
    $$
    """, unsafe_allow_html=True)
