import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import carbon_calculation

## Layout

st.title("Embankments CO2e")
st.set_page_config(layout="wide")
main_part = st.container()
inputs, outputs = main_part.columns(2)
references = st.container()
references.subheader("References")

## Inputs

height = inputs.number_input("Embankment Height, h (m)", value=5.0, step=0.5)
path_width = inputs.number_input("Path Width (m)", value=3.5, step=0.5)
inputs.image(r"images/embankment_structure.png")
distance = inputs.number_input("Soil Transportation Distance (km)", value=50)

more_in = inputs.expander("More Options")
more_in.markdown(
    "**Maximum Allowable Slope Gradient, x:1**",
)
_a, _b = more_in.columns(2)
slope_grad_reinforced = _a.number_input(
    "Reinforced Soil", value=1.00, min_value=0.01, max_value=5.00
)
slope_grad_unreinforced = _b.number_input(
    "Unreinforced Soil", value=2.00, min_value=0.01, max_value=5.00
)
more_in.caption("See image above for default geometry, derived from approximate rules")

more_in.markdown("**Soil Embodied Carbon Factors**")
processing_factor = more_in.number_input(
    "Soil processing factor for excavation/installation (kgCO2e/m3)",
    value=3.7 + 2.2,
    min_value=0.01,
)
more_in.caption("Default value taken from 2.2.4.4 of [1] as 5.9 = 3.7 + 2.2")

references.caption(
    r"[1] - https://www.netzerobridges.org/s/Carbon-Calculation-Guide-for-Bridges_v10.pdf"
)

carbon_per_km_per_m3 = more_in.number_input(
    "Transportation factor (kgCO2e/km/m3)", value=0.215 * 1.8, min_value=0.01
)
more_in.caption(r"Default value taken from 2.2.4.4 of [1] as 0.39 = 0.215 * 1.8t/m3")

more_in.markdown("**Geogrid carbon values per m3 of soil (kgCO2e)**")
low, mid, high = more_in.columns(3)
low_val = low.number_input(label="Min", value=1.88)
mid_val = mid.number_input(label="Average", value=2.88)
high_val = high.number_input(label="Max", value=5.01)
ECF_geo = np.array([low_val, mid_val, high_val])
more_in.caption(
    "Default values taken EPD's for Tensar geogrid products RE510, RE560 and RE580. See [2] for more."
)

references.caption(
    r"[2] - EPD values are taken from https://www.byggros.com/epd-oversigt. "
    + "The chosen range of Tensar products are taken as representative of those that might be "
    + "required for a vertical spacing of 1m and slope of 1:1. Products from other manufacturers "
    + "such as Stratagrid SGU 60, Maxaferri Paralink 300 and Huesker Fortrac T "
    + "are also found to be within this range. Geogrids typically form a small percentage of the "
    + "total embodied carbon compared to the transportation of the soil regardless."
)

## Calculation

ECF_soil = carbon_calculation.calc_ECF_from_distance(
    distance, carbon_per_km_per_m3, processing_factor
)

h = np.linspace(0, 1.5 * height, 151)

carb_rein = carbon_calculation.calc_carbon_per_FA(
    h, path_width, slope_grad_reinforced, ECF_soil, ECF_geogrid=ECF_geo
)
carb_unre = carbon_calculation.calc_carbon_per_FA(
    h, path_width, slope_grad_unreinforced, ECF_soil
)

df = pd.DataFrame(
    {
        "h": h,
        "Unreinforced": carb_unre[:, 0],
        "geo_low": carb_rein[:, 0],
        "geo_mid": carb_rein[:, 1],
        "geo_high": carb_rein[:, 2],
    }
)

actual_val = pd.DataFrame(
    {"x": [0, height, height], "y": [carb_rein[100, 1], carb_rein[100, 1], 0]}
)

## Chart setup

scorbs_vals = [250, 500, 1000, 1500, 2000]
SCORBS = pd.DataFrame(
    {
        "x": [0, h.max()],
        "A++": [scorbs_vals[0], scorbs_vals[0]],
        "A+": [scorbs_vals[1], scorbs_vals[1]],
        "A": [scorbs_vals[2], scorbs_vals[2]],
        "B": [scorbs_vals[3], scorbs_vals[3]],
        "C": [scorbs_vals[4], scorbs_vals[4]],
    }
)

unre_line = alt.Chart(df).mark_line(color="red", strokeDash=(4, 4))
unre_line = unre_line.encode(
    x=alt.X("h").title("h (m)"),
    y=alt.Y("Unreinforced")
    .scale(domain=(0, df["Unreinforced"].max()))
    .title("CO2e (kgCO2e/m2)"),
)

geo_line = alt.Chart(df, height=450).mark_area(opacity=0.5)
geo_line = geo_line.encode(
    x="h", y=alt.Y("geo_low").scale(domain=(0, df["geo_high"].max())), y2="geo_high"
)

lim_val = pd.DataFrame({"h": h[:101], "geo_mid": df["geo_mid"][:101]})
linear_sum = np.trapezoid(lim_val["geo_mid"], lim_val["h"]) / height
h_val = np.interp(linear_sum, df["geo_mid"], h)
lin_val = pd.DataFrame({"x": [0, h_val, h_val], "y": [linear_sum, linear_sum, 0]})

ramp_options = ["Constant height, h", "Linear increase, 0 to h"]
ramp = outputs.radio("Ramp Geometry:", options=ramp_options)

if ramp == ramp_options[0]:
    ramp_chart = alt.Chart(actual_val).mark_line(color="purple").encode(x="x", y="y")
    val_to_print = carb_rein[100, 1]
else:
    ramp_chart = alt.Chart(lin_val).mark_line(color="purple").encode(
        x="x", y="y"
    ) + alt.Chart(lim_val).mark_area(opacity=0.3, color="purple").encode(
        x="h", y="geo_mid"
    )
    val_to_print = linear_sum

alt_chart = (
    unre_line
    + alt.Chart(df).mark_line(strokeDash=(4, 4)).encode(x="h", y="geo_mid")
    + geo_line
    + ramp_chart
    + alt.Chart(SCORBS).mark_rule(color="darkgreen", clip=True).encode(y="A++")
    + alt.Chart(SCORBS).mark_rule(color="green", clip=True).encode(y="A+")
    + alt.Chart(SCORBS).mark_rule(color="yellow", clip=True).encode(y="A")
    + alt.Chart(SCORBS).mark_rule(color="orange", clip=True).encode(y="B")
)
outputs.altair_chart(alt_chart)
outputs.markdown(f"Embodied Carbon Value = **{val_to_print:.2f} kgCO2e/m2**")
scorbs_rating = np.searchsorted(scorbs_vals, val_to_print)
outputs.markdown(f"SCORBS rating of {SCORBS.keys()[scorbs_rating + 1]}")
