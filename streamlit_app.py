"""
The main web app interface.
"""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import carbon_calculation

__version__ = 0.1

## Layout

st.title("Net Zero Bridges Group - Embankments CO2e")
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

references.markdown(f"Tool Version = {__version__}")
references.markdown("Developed for the Net Zero Bridges Group. Author Sam Trueman (satr@cowi.com).")

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
        "Unre_label" : "Unreinforced Option",
        "Rein_label" : "Reinforced Option"
    }
)

actual_val = pd.DataFrame(
    {"x": [0, height, height], "y": [carb_rein[100, 1], carb_rein[100, 1], 0]}
)

## Chart setup

scorbs_vals = [250, 500, 1000, 1500, 2000]
SCORBS_names = ["A++","A+","A","B","C"]

SCORBS = pd.DataFrame(
    {"x": [0, h.max()]}|
    {k:[j, j] for k,j in zip(SCORBS_names,scorbs_vals)}|
    {f"{k}_lab":k for k in SCORBS_names}
)

# Assign line colors for chart
char_scale = alt.Scale(domain=['Unreinforced Option','Reinforced Option']+SCORBS_names, 
                       range=['Red','lightblue','darkgreen','green','yellow','orange'])

unre_line = alt.Chart(df).mark_line(strokeDash=(4, 4))
unre_line = unre_line.encode(
    x=alt.X("h").title("h (m)"),
    y=alt.Y("Unreinforced")
    .scale(domain=(0, df["Unreinforced"].max()))
    .title("CO2e (kgCO2e/m2)"),
    color=alt.Color("Unre_label", scale=char_scale).title(None)
)

geo_line = alt.Chart(df, height=450).mark_area(opacity=0.5)
geo_line = geo_line.encode(
    x="h",
    y=alt.Y("geo_low").scale(domain=(0, df["geo_high"].max())),
    y2="geo_high",
    color=alt.Color("Rein_label", scale=char_scale),
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

scorbs_scale = alt.Scale(domain=SCORBS_names,range=['darkgreen','green','yellow','orange'])

alt_chart = (
    unre_line
    + alt.Chart(df).mark_line(strokeDash=(4, 4)).encode(x="h", y="geo_mid")
    + geo_line
    + ramp_chart
    + alt.Chart(SCORBS).mark_rule(clip=True).encode(y="A++",color=alt.Color("A++_lab", scale=char_scale))
    + alt.Chart(SCORBS).mark_rule(clip=True).encode(y="A+",color=alt.Color("A+_lab", scale=char_scale))
    + alt.Chart(SCORBS).mark_rule(clip=True).encode(y="A",color=alt.Color("B_lab", scale=char_scale))
    + alt.Chart(SCORBS).mark_rule(clip=True).encode(y="B",color=alt.Color("C_lab", scale=char_scale))
)
outputs.altair_chart(alt_chart)

outputs.markdown(f"Embodied Carbon Value per FA (average reinforced soil) = **{val_to_print:.2f} kgCO2e/m2**")
scorbs_rating = np.searchsorted(scorbs_vals, val_to_print)
outputs.markdown(f"SCORBS rating of {SCORBS.keys()[scorbs_rating + 1]}")
outputs.subheader("Calculated Values")

if ramp == ramp_options[0]:
    outputs.markdown(f"Soil ECF = $({processing_factor} + {distance}\\times{carbon_per_km_per_m3}) = {ECF_soil:.2f}$ kgCO2e/m3")
    
    outputs.markdown(f"##### Reinforced")
    area_rein = carbon_calculation._calc_emb_area(height,path_width,slope_grad_reinforced)
    outputs.markdown(f"Crosssectional area = ${area_rein:.2f}$ m2")
    outputs.markdown(f"Total CO2e per m length = $({ECF_geo[1]}+{ECF_soil})\\times{area_rein:.2f} = {(ECF_geo[1]+ECF_soil)*area_rein:.2f}$ kgCO2e/m")
    
    outputs.markdown(f"##### Unreinforced")
    area_unre = carbon_calculation._calc_emb_area(height,path_width,slope_grad_unreinforced)
    outputs.markdown(f"Crosssectional area = ${area_unre:.2f}$ m2")
    outputs.markdown(f"Total CO2e per m length = ${ECF_soil}\\times{area_unre:.2f} = {ECF_soil*area_unre:.2f}$ kgCO2e/m")
    outputs.markdown(f"Embodied Carbon Value per FA = ${carb_unre[100,0]:.2f}$ kgCO2e/m2")
else:
    outputs.markdown(f"Soil ECF = $({processing_factor} + {distance}\\times{carbon_per_km_per_m3}) = {ECF_soil}$ kgCO2e/m3")
    
    outputs.markdown(f"Volume calculation assumes a 1:20 gradient, but value per FA is independent of slope")
    outputs.markdown(f"##### Reinforced")
    vol_rein = height**2*path_width/2/0.05 + height**3*slope_grad_reinforced/3/0.05
    outputs.markdown(f"Ramp volume = ${vol_rein:.2f}$ m3")
    outputs.markdown(f"Total CO2e = $({ECF_geo[1]}+{ECF_soil})\\times{vol_rein:.2f} = {(ECF_geo[1]+ECF_soil)*vol_rein:.0f}$ kgCO2e")
    
    outputs.markdown(f"##### Unreinforced")
    vol_unre = height**2*path_width/2/0.05 + height**3*slope_grad_unreinforced/3/0.05
    outputs.markdown(f"Ramp volume = ${vol_unre:.2f}$ m3")
    outputs.markdown(f"Total CO2e = ${ECF_soil}\\times{vol_unre:.2f} = {ECF_soil*vol_unre:.2f}$ kgCO2e")
    outputs.markdown(f"Embodied Carbon Value per FA = ${carb_unre[100,0]:.2f}$ kgCO2e/m2")
