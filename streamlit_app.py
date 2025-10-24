import numpy as np
import pandas as pd
import streamlit as st
import carbon_calculation

st.title('Embankments CO2e')

height = st.number_input("Height")
path_width = st.number_input("Path")
slope_grad = st.number_input("Slope Gradient")
ECF_soil = st.number_input("Soil ECF")


h = np.linspace(0,2*height,100)
carb = carbon_calculation.calc_carbon_per_FA(h,path_width,slope_grad,ECF_soil)

df = pd.DataFrame({'x':h,'y':carb})
st.line_chart(df,x='x',y='y')




