import streamlit as st



st.title("About 🏠")

st.markdown("""
     This is a an in-built Pricing Engine to generate price for Home Care Products.     
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)



st.markdown("""    

    ### 👍 Advantages of using this Engine:
            
    - **Simple** - It's  simple to use.
    - **Convinient** -No need to format SAP tables. It can be used directly.
    - **Dynamic Pricing Dates** - It does not only calculate Live Prices. Prices can be calculated with any previous factor setting.
    - **Live Exploration** - Integrated interactive dashboard can be used to explore the final results.
    - **Download** - Results can be downloaded in a single click. Formatted SAP Tables can also be downloaded for further exploration in excel.
        
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)

st.markdown("""    

    ### ❓ How to use:
            
    1. Upload unformatted SAP Tables in the **Upload** Section
    2. Upload the risk input in **Calculate** Section. Pick the desired pricing date. Then validate and caluclate the prices.
    3. Explore your results in the dashboard in **Explore** Section. 
    4. Download all the necessary tables in **Download** Section.
        

""", unsafe_allow_html=True)

st.markdown("""    

    ### Notes:
            
    1. No value should be empty.
    2. Please fill the empty cells with 0 or any value.
    3. Upload the files in excel format.
        

""", unsafe_allow_html=True)

