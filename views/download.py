import streamlit as st
import pandas as pd



st.title("Download your results here⬇️")

st.markdown("""    

<hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)


premium_file = st.session_state.premium_file

file_labels = [
"Base_Price",
"Boiler_Type",
"Appl_Make",
"Boiler_Age",
"Rads",
"Spl_Rads",
"Claims",
"Ratearea_Boilertype",
"Ratarea_Rads",
"Rads_Claims",
"Claims_Boilertype",
"Claims_load",
"Asv_price",
"Exp_Claim_load",
"Exp_Asv_load",
"Flat_Load",
"Multi_bund_margin",
"Cap_n_Collar",
"PRD_GROUP",
"geo_pschal",
"GEO_FACHAL",
"Absolute_Capping",
"Minimum_Capping",
"Flat_Bundle_Margin"
]

col1, col2 = st.columns(2)
with col1:
    st.write("Click below to download the pricing file")
    st.download_button(
    label="Download final premium file",
    data=premium_file.to_csv(index=False),
    file_name="premium_file.csv",
    mime="text/csv"
)


with col2:
    table_name = st.selectbox("Choose SAP table to download in transformed format", options=file_labels)
    if table_name is not None:
            df = st.session_state.processed_data[table_name]
            st.download_button(
            label=f"Download {table_name} file",
            data=df.to_csv(index=False),
            file_name=f"{table_name}.csv",
            mime="text/csv"
            )