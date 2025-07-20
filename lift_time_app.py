#!/usr/bin/env python3
"""
lift_time_app.py

Drone Lift & Flight Time Explorer

Select a T-Motor Antigravity motor and battery size to see:
  • Fixed payload = 10 kg
  • Flight time (min)
  • Available extra payload (kg)
  • Thrust-to-Weight ratio (with min=1.6, rec=2.0)
  • Total thrust (N)
  • Flight-time curves for every motor, with shading where T/W is below thresholds
  • All key intermediate values + motor specs
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
tw_min = 1.6               # minimum T/W ratio
tw_rec = 2.0               # recommended T/W ratio

# ─── Motor catalog ────────────────────────────────────────────────────────────
motors = {
    "MN5008 KV170":   {"thrust_kg":  4.0,  "motor_mass_kg": 0.32},
    "MN6007II KV320": {"thrust_kg":  5.5,  "motor_mass_kg": 0.30},
    "MN7005 KV115":   {"thrust_kg":  7.0,  "motor_mass_kg": 0.33},
    "MN7005 KV230":   {"thrust_kg":  6.0,  "motor_mass_kg": 0.28},
    "MN8017 KV120":   {"thrust_kg": 16.8,  "motor_mass_kg": 0.453},
    "MN8012 KV100":   {"thrust_kg": 11.8,  "motor_mass_kg": 0.351},
    "MN8014 KV100":   {"thrust_kg": 13.9,  "motor_mass_kg": 0.392},
}

# ─── Sidebar inputs ────────────────────────────────────────────────────────────
st.sidebar.header("🔧 Select Motor & Battery")

motor_name = st.sidebar.selectbox("Motor", list(motors.keys()))
specs = motors[motor_name]

st.sidebar.markdown("**Specs:**")
st.sidebar.write(f"- Max Thrust: **{specs['thrust_kg']} kgf**")
st.sidebar.write(f"- Motor Mass: **{specs['motor_mass_kg']} kg**")
st.sidebar.write(
    f"- Thrust-to-Weight (motor): **"
    f"{specs['thrust_kg']/specs['motor_mass_kg']:.1f}:1**"
)

battery_Wh = st.sidebar.slider(
    "Battery Energy (Wh)", min_value=1000, max_value=20000, value=6000, step=100
)

# ─── Core calculations ─────────────────────────────────────────────────────────
battery_mass = battery_Wh / specific_energy

# total thrust from 8 motors: 4 @100% + 4 @70%
motor_thrust = specs["thrust_kg"]
total_thrust_kgf = motor_thrust * (4 + 4 * 0.7)
total_thrust_N = total_thrust_kgf * g

# available extra payload beyond frame, batt, fixed payload
available_extra = total_thrust_kgf - (empty_mass + battery_mass + payload_fixed)
available_extra = max(0.0, available_extra)

# total mass lifting fixed payload
total_mass = empty_mass + battery_mass + payload_fixed

# hover power & flight time
P_hover = total_mass * power_req_coeff
flight_time_h = battery_Wh / P_hover if P_hover > 0 else 0.0
flight_time_min = flight_time_h * 60

# thrust-to-weight ratio
T_W_ratio = total_thrust_kgf / total_mass if total_mass > 0 else 0.0

# compute battery thresholds for T/W limits
# battery_mass_limit = total_thrust_kgf/tw - empty_mass - payload_fixed
bat_mass_min = total_thrust_kgf/tw_min - empty_mass - payload_fixed
bat_mass_rec = total_thrust_kgf/tw_rec - empty_mass - payload_fixed
# convert to Wh
bat_Wh_min = max(0.0, bat_mass_min * specific_energy)
bat_Wh_rec = max(0.0, bat_mass_rec * specific_energy)

# ─── UI: Metrics & thresholds ─────────────────────────────────────────────────
st.title("🚁 Drone Lift & Flight Time Explorer")

st.markdown("### 📌 System Constants")
c1, c2, c3 = st.columns(3)
c1.metric("Empty Frame Mass", f"{empty_mass:.1f} kg")
c2.metric("Fixed Payload",    f"{payload_fixed:.1f} kg")
c3.metric("Hover Power Coeff.", f"{power_req_coeff:.0f} W/kg")

st.markdown("### 🔄 Intermediate Values")
c4, c5, c6, c7 = st.columns(4)
c4.metric("Battery Mass",        f"{battery_mass:.2f} kg")
c5.metric("Max Lift Capability", f"{total_thrust_kgf:.2f} kgf")
c6.metric("Total Take-off Mass", f"{total_mass:.2f} kg")
c7.metric("Total Thrust",        f"{total_thrust_N:.0f} N")

st.markdown("### 📊 Results")
r1, r2, r3 = st.columns(3)
r1.metric("Flight Time",            f"{flight_time_min:.1f} min")
r2.metric("Available Extra Payload", f"{available_extra:.2f} kg")
r3.metric("T/W Ratio",              f"{T_W_ratio:.2f}:1")

# threshold feedback
if T_W_ratio < tw_min:
    st.error(f"T/W ratio {T_W_ratio:.2f} below minimum {tw_min:.1f}")
elif T_W_ratio < tw_rec:
    st.warning(f"T/W ratio {T_W_ratio:.2f} ≥ minimum, below recommended {tw_rec:.1f}")
else:
    st.success(f"T/W ratio {T_W_ratio:.2f} ≥ recommended {tw_rec:.1f}")

# ─── Tab for flight-time curves ────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Overview", "Flight Time Curves"])

with tab2:
    st.subheader("🔋 Flight Time vs. Battery for All Motors")
    fig, ax = plt.subplots(figsize=(8, 5))
    bat_range = np.linspace(1000, 20000, 200)
    for name, m in motors.items():
        mt = m["thrust_kg"]
        total_thrust = mt * (4 + 4 * 0.7)
        times = []
        for b in bat_range:
            bm = b / specific_energy
            tm = empty_mass + bm + payload_fixed
            ph = tm * power_req_coeff
            fh = b / ph if ph > 0 else 0
            times.append(fh * 60)
        ax.plot(bat_range, times, label=name)

    # shading regions for selected motor
    ax.axvspan(bat_Wh_rec, bat_Wh_min, color="yellow", alpha=0.2,
               label="T/W between 1.6–2.0")
    ax.axvspan(bat_Wh_min, bat_range.max(), color="red", alpha=0.2,
               label="T/W below 1.6")

    ax.axvline(battery_Wh, color="black", ls="--", label="Selected Battery")
    ax.set_xlabel("Battery Energy (Wh)")
    ax.set_ylabel("Flight Time (min)")
    ax.set_title("Flight Time vs. Battery Energy")
    ax.legend(loc="upper right")
    ax.grid(True, ls="--", alpha=0.5)
    st.pyplot(fig)
