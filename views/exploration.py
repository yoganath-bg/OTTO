import streamlit as st
import pandas as pd
import seaborn as sns
import re
import plotly.express as px
import plotly.graph_objects as go



st.title("Exploration📊")
st.header("Analyse your results here")

st.markdown("""   
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)

premium_file = st.session_state.premium_file


#st.write(premium_file)


col1, col2 = st.columns(2)
with col1:
    st.header("Expected Retention Probability (Placeholder)")
    fig1 = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = 95,
    number = {'suffix': "%"},
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Retention"},
     gauge = {
        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
        # 'steps': [
        #     {'range': [0, 85], 'color': 'red'},
        #     {'range': [85, 100], 'color': 'green'} ]
        }))

    st.plotly_chart(fig1)

with col2:
    st.header("Expected Claims Rate Probability (Placeholder)")
    fig2 = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = 70,
    number = {'suffix': "%"},
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Claims Rate"},
     gauge = {
        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
        #'needle': {'color': "red"}  # This adds a needle
        # 'steps': [
        #     {'range': [0, 85], 'color': 'red'},
        #     {'range': [85, 100], 'color': 'green'} ]
        }))

    st.plotly_chart(fig2)

st.markdown("""   
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)

columns_list = ['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'post_sector', 'manufacturer_code', 'boiler_age', 'radiators', 'spl_radiators', 'jobs_completed', 'change_in_circumstan']

# Streamlit app
st.header("Interactive Chart for Final Prices Distribution")

# User input for x-axis selection
#x_axis = st.selectbox("Select X-axis", options=columns_list)

column_name = st.selectbox("Select a factor", options=columns_list)
factor = st.selectbox("Pick a value",options = premium_file[column_name].unique())

filtered_premium_file = premium_file[premium_file[column_name]==factor]

avg_ly_price = filtered_premium_file['LY_Price'].mean()
avg_renewal_price = filtered_premium_file['Final_Premium'].mean()

delta = round(((avg_renewal_price-avg_ly_price)/avg_ly_price)*100,2)





col1, col2 = st.columns(2)
with col1:
    st.metric(label = 'Last Year Price', value = "£{:,.2f}".format(avg_ly_price))

with col2:
    st.metric(label = 'Calculated Renewal Price', value = "£{:,.2f}".format(avg_renewal_price),delta = f"{delta}%")

# Create interactive plot
fig = px.histogram(filtered_premium_file,  x='Final_Premium', title='Distribution of Final Prices')
#fig = sns.histplot(x='Final_Premium',data=filtered_premium_file)

trace1 = go.Histogram(x=filtered_premium_file['Final_Premium'], name='Renewal Price', opacity=0.75,marker_color='blue')
trace2 = go.Histogram(x=filtered_premium_file['LY_Price'], name='LY Price', opacity=0.20,marker_color='red')


# Create the figure
fig = go.Figure(data=[trace1, trace2])

# Update layout for better visualization
fig.update_layout(
    title='Distrubution of LY Price and Renewal Price',
    xaxis_title='Premium',
    yaxis_title='Volume',
    barmode='overlay'
)


# Display plot
st.plotly_chart(fig)


