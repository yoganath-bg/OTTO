import streamlit as st
import pandas as pd
import numpy as np
import base64


st.set_page_config(
    page_title="Welcome to the Pricing World",
    page_icon="BG_Flame_Big.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)




# Add custom CSS for styling the white background
st.markdown(
    """
    <div style="display: flex; align-items: center; background-color: white; padding: 10px;">
        <div style="flex: 1; margin-left: 10px;">
            <img src="https://www.britishgas.co.uk/nucleus/images/logo.svg" style="width:100px;">
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


st.empty()

# === List of Tabs Layout ===
tabs = st.tabs([
    "Know How",
    "🎛️ Kitchen Appliance Cover",
    "Boiler and Central Heating Cover",
    "Plumbing and Drains Cover",
    "Home Electrical Cover"
])



#Loading Tables 
@st.cache_data
def load_sap_tables(file_path):
    appl_lookup = pd.read_excel(file_path,sheet_name = 'appl_lookup')
    key_lookup = pd.read_excel(file_path,sheet_name = 'key_lookup')
    base_price = pd.read_excel(file_path,sheet_name = 'base_price')
    bundle_tenure = pd.read_excel(file_path,sheet_name = 'bundle_tenure')
    acq_geo_code = pd.read_excel(file_path,sheet_name = 'acq_geo_code')
    ren_geo_code = pd.read_excel(file_path,sheet_name = 'ren_geo_code')
    rads = pd.read_excel(file_path,sheet_name = 'rads')
    rads['Number'] = rads['Number'].astype(str)
    spl_rads = pd.read_excel(file_path,sheet_name = 'spl_rads')
    spl_rads['Number'] = spl_rads['Number'].astype(str)
    flat_expense = pd.read_excel(file_path,sheet_name = 'flat_expense')
    claims_load = pd.read_excel(file_path,sheet_name = 'claims_load') 
    flat_margin = pd.read_excel(file_path,sheet_name = 'flat_margin')
    multi_margin = pd.read_excel(file_path,sheet_name = 'multi_margin')

    return (appl_lookup, key_lookup, base_price, bundle_tenure, acq_geo_code, ren_geo_code, rads, spl_rads, flat_expense, claims_load, flat_margin, multi_margin)

(appl_lookup, key_lookup, base_price, bundle_tenure, acq_geo_code, 
 ren_geo_code, rads, spl_rads, flat_expense, claims_load, 
 flat_margin, multi_margin) = load_sap_tables("KAC_Tables.xlsx")




## === First Tab ===
with tabs[0]:
    st.title("Pricing Calculator - How to use?")

    st.markdown("""
        Welcome to the **Protection Pricing World**. Here you can learn everything about what's going in the Pricing World. 
        This platform is aimed at explaing how the risk pricing works for the Home Care Products and also to get a deeper insights.""")

                
## === Second Tab ===
with tabs[1]:
    st.title("🎛️ Kitchen Appliance Cover")
    

# First row (2 questions)
    col1, col2, col3 = st.columns(3)
    with col1:
        question1 = st.selectbox(
            'Select the level of Excess',
            ('0xs', '60xs'),index = None, placeholder="Select excess level...")
    with col2:
        question3 = st.selectbox(
        'Select level of home care',
        ("HC1(BCC)","HC2(CHC)","HC3(CHC+PAD)","HC4(CHC+PAD+HEC)","No Homecare"),index = None, placeholder="Select homecare...")
        
    #Second row (2 questions) 
    
    with col3:
        question2 = st.selectbox(
            'Select your appliance',
            ("Dishwasher","Fridge-Freezer","Electric Tumble Dryer","Electric Oven","Washer Dryer","Gas Cooker & Electric","Electric Cooker","Gas Cooker",
            "Gas Hob","Fridge","Freezer","Microwave","Electric Hob","Microwave Oven","Gas Oven","Washing Machine Old","Gas Tumble Dryer","Washing Machine",
            "Hob Gas & Electric","Spin Dryer","Washing Machine Twin Tub"),index = None, placeholder="Select appliance...")

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

    st.write("You selected")
    st.write(question1, ",", question2, ",", question3, ",", question4, ",", question5, ",", question6)




    if question1 and question2 and question3 and question4 and question5 and question6:

        proceed_button = st.button("Calculate Prices")


        if proceed_button:

            st.markdown("""
            ### **Here is your result**

            <hr style="border: 1px solid #0490d7; margin: 20px 0;">
        """, unsafe_allow_html=True)
            
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


        ## == Calculation Stages_subtotals == 
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



        ## == Renewal_Calculation Stages_subtotals == 
            ren_claims_base_price_st = ren_base_price_value
            ren_bundle_tenure_st = round((ren_base_price_value*bundle_tenure_value),2)
            ren_rating_area_st = round((ren_base_price_value*bundle_tenure_value*ren_geo_value),2)  
            ren_radiator_st = round((ren_base_price_value*bundle_tenure_value*ren_geo_value*ren_rads),2) 
            ren_spl_rads_st = round((ren_base_price_value*bundle_tenure_value*ren_geo_value*ren_rads*ren_spl_rads),2) 
            ren_initial_breakdown_st = round((ren_base_price_value*bundle_tenure_value*ren_geo_value*ren_rads*ren_spl_rads*initial_breakdown),2) 
            ren_claims_premium = round((ren_base_price_value*bundle_tenure_value*ren_geo_value*ren_rads*ren_spl_rads*initial_breakdown),2)
            ren_flat_expense_st = ren_flat_expense_value
            ren_claims_load_st = round((ren_claims_load_value*ren_claims_premium),2) 
            ren_expense_premium_st = round((ren_flat_expense_st+ren_claims_load_st),2)
            ren_technical_premium_st = round((ren_claims_premium+ren_expense_premium_st),2)
            ren_flat_margin_st = ren_flat_margin_value
            ren_multi_margin_st = round((ren_technical_premium_st*ren_multi_margin_value),2)
            ren_pre_cap_margin_st = round((ren_flat_margin_st+ren_multi_margin_st),2)
            ren_pre_cap_premium_st = round((ren_technical_premium_st+ren_pre_cap_margin_st),2)
            ren_capping_adj_st = 0
            ren_collar_adj_st = 0
            ren_minimum_cap_adj_st = 0
            ren_final_premium_st = round((ren_pre_cap_premium_st+ren_capping_adj_st+ren_collar_adj_st+ren_minimum_cap_adj_st),2)

            ##   == Renewal Calculator ==
            ren_table = {
            'Component': ['Claims Base Price', 'Bundle x Tenure', 'Rating Area', 'Radiator','Special Rads',
                        'Initial Breakdown', 'Claims Premium','Flat Expense','Claims Load','Expense Premium',
                        'Technical Premium','Flat Margin','Multiplicative Margin','Pre-cap Margin','Pre-cap Premium',
                        'Capping Adjustment','Collar Adjustment','Minimum Cap Adjustment','Final Premium'],
            'Factor': [ren_base_price_value, bundle_tenure_value, ren_geo_value, ren_rads, ren_spl_rads,
                    initial_breakdown, ' ',ren_flat_expense_value,ren_claims_load_value, ' ',
                    ' ',ren_flat_margin_value,ren_multi_margin_value,' ',' ',
                    'WIP','WIP','WIP',' '],
            'Subtotal': [ren_claims_base_price_st,ren_bundle_tenure_st,ren_rating_area_st,ren_radiator_st,ren_spl_rads_st,
                        ren_initial_breakdown_st,ren_claims_premium,ren_flat_expense_st,ren_claims_load_st,ren_expense_premium_st,
                        ren_technical_premium_st,ren_flat_margin_st,ren_multi_margin_st,ren_pre_cap_margin_st,ren_pre_cap_premium_st,
                        'WIP','WIP','WIP',ren_final_premium_st]  
            }


            acq_df = pd.DataFrame(acq_table)
            ren_df = pd.DataFrame(ren_table)
            delta = round(final_premium_st - ren_final_premium_st,2)
            delta2 = round(ren_final_premium_st - final_premium_st,2)

            
            acq_df = pd.DataFrame(acq_table)
            ren_df = pd.DataFrame(ren_table)
            delta = round(final_premium_st - ren_final_premium_st,2)
            delta2 = round(ren_final_premium_st - final_premium_st,2)



            col1, col2 = st.columns(2)
            with col1:
                st.metric(label = 'Acquisition Technical Price', value = "£{:,.2f}".format(final_premium_st),delta=delta)
                col1.table(acq_df)
            with col2:
                st.metric(label = 'Renewal Technical Price', value = "£{:,.2f}".format(ren_final_premium_st),delta = delta2)
                col2.table(ren_df)
        else:
            st.stop()
    else:
        st.warning("Please fill the inputs")
