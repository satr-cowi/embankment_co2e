import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import carbon_calculation

st.title('Embankments CO2e')

height = st.number_input("Height")
path_width = st.number_input("Path")
slope_grad = st.number_input("Slope Gradient")
ECF_soil = st.number_input("Soil ECF")


h = np.linspace(0,2*height,101)
carb = carbon_calculation.calc_carbon_per_FA(h,path_width,slope_grad,ECF_soil)

df = pd.DataFrame({'h':h,
                   'Unreinforced':carb[:,0],
                   'geo_low':carb[:,1],
                   'geo_mid':carb[:,2],
                   'geo_high':carb[:,3]})

alt_chart = (alt.Chart(df).mark_line().encode(x='h',y='Unreinforced') + 
             alt.Chart(df).mark_line().encode(x='h',y='geo_mid') +
             alt.Chart(df).mark_area().encode(x='h',y='geo_low',y2='geo_high'))
st.altair_chart(alt_chart)