import streamlit as st
import pandas as pd
import numpy as np


st.set_page_config(
    page_title="Welcome to the Pricing World",
    page_icon="pound.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)
# === List of Tabs Layout ===
tabs = st.tabs([
    "📚 User Guide",
    "🎛️ Kitchen Appliance Cover",
    "Boiler and Central Heating Cover",
    "Plumbing and Drains Cover",
    "Home Electrical Cover"
])

## === First Tab ===
with tabs[0]:
    st.title("📚 User Guide: Pricing Calculator")

    st.markdown("""
        Welcome to the **Protection Pricing World**. Here you can learn everything about what's going in the Pricing World. 
        This platform is aimed at explaing how the risk pricing works for the Home Care Products and also to get a deeper insights.""")

                
## === Second Tab ===
with tabs[1]:
    st.title("🎛️ Kitchen Appliance Cover")

    # First row (3 questions)
    col1, col2, col3 = st.columns(3)
    with col1:
        question1 = col1.selectbox(
            'Select the level of Excess',
            ('0xs', '60xs'),index = None, placeholder="Select excess level...")
    with col2:
        question2 = col2.selectbox(
            'Select your appliance',
            ("Dishwasher","Fridge-Freezer","Electric Tumble Dryer","Electric Oven","Washer Dryer","Gas Cooker & Electric","Electric Cooker","Gas Cooker",
            "Gas Hob","Fridge","Freezer","Microwave","Electric Hob","Microwave Oven","Gas Oven","Washing Machine Old","Gas Tumble Dryer","Washing Machine",
            "Hob Gas & Electric","Spin Dryer","Washing Machine Twin Tub"),index = None, placeholder="Select excess level...")
    with col3:
        question3 = col3.selectbox(
        'Select level of home care',
        ("HC1(BCC)","HC2(CHC)","HC3(CHC+PAD)","HC4(CHC+PAD+HEC)","No Homecare",),index = None, placeholder="Select your homecare bundle...")
    
    
    #Second row (3 questions)    
    col1, col2, col3 = st.columns(3)
    with col1:
        question4 = st.selectbox('Enter postcode Sector', ("AB101","AB106","AB107","AB115","AB116","AB117","AB118","AB119","AB123","AB124","AB125",
                                "AB130","AB140","AB154","AB155","AB156","AB157","AB158","AB159","AB16","AB165","AB166","AB167","AB210","AB217","AB219","AB228",
                                "AB238","AB241","AB242","AB243","AB244","AB245","AB251","AB252","AB253","AB254","AB301","AB313","AB314","AB315","AB316","AB326",
                                "AB327","AB338","AB344","AB345"),index = None, placeholder="Select your postcode sector...")
    with col2:
        question5 = st.selectbox('Select No of Radiators', ("0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16",
                                "17","18","19","20","21","22-98","99"),index = None, placeholder="Select no of radiators...")
    with col3:
        question6 = st.selectbox('Select No of Spl Radiators', ("0","1","2","3","3+"),index = None, placeholder="Select no of spl radiators...")

    ##Loading Tables (move to top)
    appl_lookup = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'appl_code')
    key_lookup = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'key_lookup')
    base_price = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'Baseprice')
    bundle_tenure = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'bundle')
    acq_geo_code = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'acq_geo_code')
    ren_geo_code = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'ren_geo_code')
    rads = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'rads')
    rads['Number'] = rads['Number'].astype(str)
    spl_rads = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'spl_rads')
    spl_rads['Number'] = spl_rads['Number'].astype(str)
    flat_expense = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'flat_expense')
    claims_load = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'Claims_Load') 
    flat_margin = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'Flat_Margin')
    multi_margin = pd.read_excel("KAC_Tables.xlsx",sheet_name = 'multi_margin')
    



    ##Creating lookup values from the inputs
    appl_code = appl_lookup.loc[appl_lookup['Appliance'] == question2]['Code'].iloc[0]
    pricing_key = key_lookup.loc[key_lookup['Excess'] == question1]['Pricing Key'].iloc[0]
    acq_pkey_appl_lookup = "50"+pricing_key+appl_code
    ren_pkey_appl_lookup = "51"+pricing_key+appl_code
    acq_pkey_lookup= "50"+pricing_key
    ren_pkey_lookup= "51"+pricing_key


    ##Looking up values from the input tables
    acq_base_price_value = base_price.loc[base_price['Helper'] == acq_pkey_appl_lookup]['Factor'].iloc[0]
    ren_base_price_value = base_price.loc[base_price['Helper'] == ren_pkey_appl_lookup]['Factor'].iloc[0]
    bundle_tenure_value = bundle_tenure.loc[bundle_tenure['Home Care Bundle'] == question3]['Factor'].iloc[0]
    acq_geo_value = acq_geo_code.loc[acq_geo_code['POST_SECTOR'] == question4]['Factor'].iloc[0]
    ren_geo_value = ren_geo_code.loc[ren_geo_code['POST_SECTOR'] == question4]['Factor'].iloc[0]
    acq_rads = 1
    ren_rads = rads.loc[rads['Number'] == question5]['Factor'].iloc[0]
    acq_spl_rads = 1
    ren_spl_rads = spl_rads.loc[spl_rads['Number'] == question6]['Factor'].iloc[0]
    initial_breakdown = 1 ##placeholder for future factor 
    acq_flat_expense_value = flat_expense.loc[flat_expense['Helper'] == acq_pkey_lookup]['Factor'].iloc[0]
    ren_flat_expense_value = flat_expense.loc[flat_expense['Helper'] == ren_pkey_lookup]['Factor'].iloc[0]
    acq_claims_load_value = claims_load.loc[claims_load['Helper'] == acq_pkey_appl_lookup]['Factor'].iloc[0]
    ren_claims_load_value = claims_load.loc[claims_load['Helper'] == ren_pkey_appl_lookup]['Factor'].iloc[0]
    acq_flat_margin_value = flat_margin.loc[flat_margin['Helper'] == acq_pkey_appl_lookup]['Factor'].iloc[0]
    ren_flat_margin_value = flat_margin.loc[flat_margin['Helper'] == ren_pkey_appl_lookup]['Factor'].iloc[0]
    acq_multi_margin_value = multi_margin.loc[multi_margin['Helper'] == acq_pkey_appl_lookup]['Factor'].iloc[0]
    ren_multi_margin_value = multi_margin.loc[multi_margin['Helper'] == ren_pkey_appl_lookup]['Factor'].iloc[0]


## == Calculation Stages == 
    claims_base_price_st = acq_base_price_value
    bundle_tenure_st = round((acq_base_price_value*bundle_tenure_value),2)
    rating_area_st = round((acq_base_price_value*bundle_tenure_value*acq_geo_value),2)  
    radiator_st = round((acq_base_price_value*bundle_tenure_value*acq_geo_value*acq_rads),2) 
    spl_rads_st = round((acq_base_price_value*bundle_tenure_value*acq_geo_value*acq_rads,acq_spl_rads)[0],2) 
    initial_breakdown_st = round((acq_base_price_value*bundle_tenure_value*acq_geo_value*acq_rads,acq_spl_rads*initial_breakdown)[0],2) 
    claims_premium = round((acq_base_price_value*bundle_tenure_value*acq_geo_value*acq_rads,acq_spl_rads*initial_breakdown)[0],2)
    flat_expense_st = acq_flat_expense_value
    claims_load_st = round((acq_claims_load_value*claims_premium),2) 
    expense_premium_st = round((flat_expense_st+claims_load_st),2)
    technical_premium_st = round((claims_premium+expense_premium_st),2)
    flat_margin_st = acq_flat_margin_value
    multi_margin_st = round((technical_premium_st*acq_multi_margin_value),2)
    pre_cap_margin_st = round((flat_margin_st+multi_margin_st),2)
    pre_cap_premium_st = round((technical_premium_st+pre_cap_margin_st),2)
    capping_adj_st = 0
    collar_adj_st = 0
    minimum_cap_adj_st = 0
    final_premium_st = round((pre_cap_premium_st+capping_adj_st+collar_adj_st+minimum_cap_adj_st),2)

##   == Acquistion Calculator ==
    acq_table = {
    'Component': ['Claims Base Price', 'Bundle x Tenure', 'Rating Area', 'Radiator','Special Rads',
                  'Initial Breakdown', 'Claims Premium','Flat Expense','Claims Load','Expense Premium',
                  'Technical Premium','Flat Margin','Multiplicative Margin','Pre-cap Margin','Pre-cap Premium',
                  'Capping Adjustment','Collar Adjustment','Minimum Cap Adjustment','Final Premium'],
    'Factor': [acq_base_price_value, bundle_tenure_value, acq_geo_value, acq_rads, acq_spl_rads,
               initial_breakdown, ' ',acq_flat_expense_value,acq_claims_load_value, ' ',
               ' ',acq_flat_margin_value,acq_multi_margin_value,' ',' ',
               'Not Applicable','Not Applicable','Not Applicable',' '
               ],
    'Subtotal': [claims_base_price_st,bundle_tenure_st,rating_area_st,radiator_st,spl_rads_st,
                 initial_breakdown_st,claims_premium,flat_expense_st,claims_load_st,expense_premium_st,
                 technical_premium_st,flat_margin_st,multi_margin_st,pre_cap_margin_st,pre_cap_premium_st,
                 ' ',' ',' ',final_premium_st]  
    }

    st.markdown("""
        ### **Here is your result**

        <hr style="border: 1px solid #0490d7; margin: 20px 0;">
    """, unsafe_allow_html=True)


    st.metric(label = 'Customer Technical Price', value = final_premium_st)

    df = pd.DataFrame(acq_table)


    st.table(df)    

    # st.write(acq_pkey_appl_lookup)
    # st.write(ren_pkey_appl_lookup)
    # st.write(acq_pkey_lookup)
    # st.write(ren_pkey_lookup)
    # st.write(acq_base_price_value)
    # st.write(ren_base_price_value)
    # st.write(bundle_tenure_value)
    # st.write(acq_geo_value)
    # st.write(ren_geo_value)
    # st.write(acq_rads)
    # st.write(ren_rads)
    # st.write(acq_spl_rads)
    # st.write(ren_spl_rads)
    # st.write(acq_flat_expense_value)
    # st.write(ren_flat_expense_value)
    # st.write(acq_claims_load_value)
    # st.write(ren_claims_load_value)
    # st.write(acq_flat_margin_value)
    # st.write(ren_flat_margin_value)
    # st.write(acq_multi_margin_value)
    # st.write(final_premium_st)

   