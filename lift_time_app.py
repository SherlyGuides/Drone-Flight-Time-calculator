#!/usr/bin/env python3
"""
lift_time_app.py

Drone Lift & Flight Time Explorer

Select a T-Motor Antigravity motor and battery size to see:
  • Fixed payload = 10 kg
  • Flight time (min)
  • Available extra payload (kg)
  • Thrust-to-Weight ratio
  • Total thrust (N)
  • All key intermediate values + motor specs
"""

import streamlit as st

# ─── Constants ────────────────────────────────────────────────────────────────
g = 9.81                 # m/s²
empty_mass = 5.0         # kg (frame + electronics)
payload_fixed = 10.0     # kg
specific_energy = 200.0  # Wh/kg (battery energy density)
power_req_coeff = 200.0  # W/kg (hover power coefficient)

# ─── Motor Catalog ───────────────────────────────────────────────────────────
motors = {
    "MN5008 KV170":   {"thrust_kg":  4.0, "motor_mass_kg": 0.32},
    "MN6007II KV320": {"thrust_kg":  5.5, "motor_mass_kg": 0.30},
    "MN7005 KV115":   {"thrust_kg":  7.0, "motor_mass_kg": 0.33},
    "MN7005 KV230":   {"thrust_kg":  6.0, "motor_mass_kg": 0.28},
    "MN8012 KV100":   {"thrust_kg": 11.8, "motor_mass_kg": 0.351},
}

st.sidebar.header("🔧 Select Motor & Battery")

motor_name = st.sidebar.selectbox("T-Motor Antigravity catalog", list(motors.keys()))
specs = motors[motor_name]

# Show motor characteristics
st.sidebar.markdown("**Motor Specs:**")
st.sidebar.write(f"- Max Thrust: **{specs['thrust_kg']} kgf**")
st.sidebar.write(f"- Motor Mass: **{specs['motor_mass_kg']} kg**")
st.sidebar.write(f"- Thrust-to-Weight: **{specs['thrust_kg']/specs['motor_mass_kg']:.1f}:1**")

battery_Wh = st.sidebar.slider(
    "Battery Energy Capacity (Wh)",
    min_value=1000, max_value=20000, value=6000, step=100
)

# ─── Calculations ─────────────────────────────────────────────────────────────
battery_mass = battery_Wh / specific_energy         # kg

# Per-motor thrust (kgf) and total thrust from 8 motors:
motor_thrust = specs["thrust_kg"]                   # kgf per motor
# 4 at 100% + 4 at 70% (30% less)
total_thrust_kgf = motor_thrust * (4 + 4 * 0.7)     # kgf
total_thrust_N = total_thrust_kgf * g               # N

# Available extra payload beyond frame+batt+fixed payload
available_extra = total_thrust_kgf - (empty_mass + battery_mass + payload_fixed)
available_extra = max(0.0, available_extra)

# Total mass carrying fixed payload
total_mass = empty_mass + battery_mass + payload_fixed

# Flight time at fixed payload
P_hover = total_mass * power_req_coeff              # W
flight_time_h = battery_Wh / P_hover if P_hover>0 else 0.0
flight_time_min = flight_time_h * 60                # minutes

# Thrust-to-weight ratio
T_W_ratio = total_thrust_kgf / total_mass if total_mass>0 else 0.0

# ─── UI Display ───────────────────────────────────────────────────────────────
st.title("Bramer Drone Lift & Flight Time Calculator")

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
r2.metric("Avail. Extra Payload",   f"{available_extra:.2f} kg")
r3.metric("Thrust-to-Weight Ratio", f"{T_W_ratio:.2f}:1")

st.markdown("""
---
Adjust **motor selection** and **battery Wh** on the left to instantly see
how your **fixed 10 kg** payload, frame and battery interact with thrust.
""")
