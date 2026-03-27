import streamlit as st
import pandas as pd



st.title("Validate and Generate Prices 📱")

st.markdown("""   
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)

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
"Cap_n_Collar"
]


#retrieve the files from upload page. #change this to list comprehension. no need to read individually except geo_pschal_df.
base_price_df  = st.session_state.processed_data['Base_Price']
boiler_Type_df  = st.session_state.processed_data['Boiler_Type']
appl_make_df = st.session_state.processed_data['Appl_Make']
PRD_GROUP_df = st.session_state.processed_data['PRD_GROUP']
geo_pschal_df = st.session_state.geo_pschal
geo_fachal_df = st.session_state.processed_data['GEO_FACHAL']
boiler_age_df  = st.session_state.processed_data['Boiler_Age']
rads_df  = st.session_state.processed_data['Rads']
spl_rads_df = st.session_state.processed_data['Spl_Rads']
Claims_df = st.session_state.processed_data['Claims'] 
ratearea_boilertype_df = st.session_state.processed_data['Ratearea_Boilertype']
ratarea_rads_df = st.session_state.processed_data['Ratarea_Rads']
rads_claims_df = st.session_state.processed_data['Rads_Claims']  
claims_boilertype_df = st.session_state.processed_data['Claims_Boilertype']
claims_load_df = st.session_state.processed_data['Claims_load']
asv_df = st.session_state.processed_data['Asv_price'] 
exp_claim_df = st.session_state.processed_data['Exp_Claim_load']
exp_asv_load = st.session_state.processed_data['Exp_Asv_load']
flat_load_df = st.session_state.processed_data['Flat_Load']  
multi_margin_df = st.session_state.processed_data['Multi_bund_margin']
cap_collar_df = st.session_state.processed_data['Cap_n_Collar']
cap_collar_df['change_in_circumstan'] = cap_collar_df['change_in_circumstan'].apply(lambda x: x.upper() if isinstance(x, str) else x)



# First row (2 questions)
col1, col2 = st.columns(2)
with col1:
    #capturing the uploaded file
    uploaded_file = st.file_uploader(label='Upload your input table', help='Upload your data', label_visibility="visible")

    if uploaded_file is not None:
        input_risk = pd.read_excel(uploaded_file)

with col2:
    pricing_date = st.date_input(label = 'Generate Prices as on',help = "Prices will be calculated as per the factors active on this date",max_value="today")

    pricing_date = pd.to_datetime(pricing_date, errors='coerce').date()


# #cpturing the uploaded file
# uploaded_file = st.file_uploader(label='Upload your input table', help='Upload your data', label_visibility="visible")

# if uploaded_file is not None:
#     input_risk = pd.read_excel(uploaded_file)


# pricing_date = st.date_input(label = 'Generate Prices as on')

# pricing_date = pd.to_datetime(pricing_date, errors='coerce').date()

#st.write(pricing_date)



def lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and price_group == @row["price_group"] and exec_rule == @row["exec_rule"]')
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 0  # Default value if no match is found
    
def combi_boiler_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and price_group == @row["price_group"] and exec_rule == @row["exec_rule"] and is_combi_boiler == @row["is_combi_boiler"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found
    
def appl_make_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and price_group == @row["price_group"] and exec_rule == @row["exec_rule"] and manufacturer_code == @row["manufacturer_code"]')
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found
    
def geo_group_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"]')
    if not result.empty:
        return result[value_to_return].values[0]
    else:
        return "G0001"  # Default value if no match is found

def geo_code_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'geo_groupid == @row["geo_groupid"] and post_sector == @row["post_sector"] and price_group == @row["price_group"] and exec_rule == @row["exec_rule"]')
    if not result.empty:
        return str(result[value_to_return].values[0])
    else:
        if row["price_group"] == 51:
            return "ZZ"
        elif row["price_group"] == 50:
            return "ZY"
        return "1"  # Default value if no match is found

def geo_factor_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and geo_code == @row["geo_code"]')
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found

def boiler_age_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and boiler_age == @row["boiler_age"]')
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found

def radiators_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and radiators == @row["radiators"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found
    
def spl_radiators_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and spl_radiators == @row["spl_radiators"]')
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found


def claims_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and jobs_completed == @row["jobs_completed"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found

def ratarea_boilertype_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and is_combi_boiler == @row["is_combi_boiler"] and geo_region == @row["geo_code"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found

def ratarea_rads_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and radiators == @row["radiators"] and geo_region == @row["geo_code"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found

def rads_claims_lookup_value(row, value_to_return, pricing_date, lookup_table):

    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and radiators == @row["radiators"] and jobs_completed == @row["jobs_completed"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found

def claims_boilertype_lookup_value(row, value_to_return, pricing_date, lookup_table):
    result = lookup_table.query(
        'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and price_group == @row["price_group"] and is_combi_boiler == @row["is_combi_boiler"] and jobs_completed == @row["jobs_completed"]'
    )
    if not result.empty:
        return float(result[value_to_return].values[0])
    else:
        return 1  # Default value if no match is found
    

def cap_collar_lookup_value(row, value_to_return, pricing_date, lookup_table):
    if row["price_group"] == 51:
        result = lookup_table.query(
            'pricing_key == @row["pricing_key"] and exec_rule == @row["exec_rule"] and boiler_age == @row["boiler_age"] and jobs_completed == @row["jobs_completed"] and change_in_circumstan == @row["change_in_circumstan"]'
        )
        if not result.empty:
            return float(result[value_to_return].values)
        else:
            return 100  # Default value if no match is found
    else:
        return 100  # Default value for price group other than 51

     
def calculate_prices(uploaded_file):

        # Apply the lookup function to each row in the main DataFrame
        input_risk['f_base_price'] = input_risk.apply(lambda row: lookup_value(row, 'base_price_claims', pricing_date,base_price_df), axis=1)
        input_risk['f_boiler_type'] = input_risk.apply(lambda row: combi_boiler_lookup_value(row, 'factor', pricing_date,boiler_Type_df), axis=1)
        input_risk['f_appl_make'] = input_risk.apply(lambda row: appl_make_lookup_value(row, 'factor', pricing_date,appl_make_df), axis=1)
        input_risk['geo_groupid'] = input_risk.apply(lambda row: geo_group_lookup_value(row, 'geo_groupid', pricing_date,PRD_GROUP_df), axis=1)
        input_risk['geo_code'] = input_risk.apply(lambda row: geo_code_lookup_value(row, 'geo_code', pricing_date,geo_pschal_df), axis=1)
        input_risk['f_geo_factor'] = input_risk.apply(lambda row: geo_factor_lookup_value(row, 'factor', pricing_date,geo_fachal_df), axis=1)
        input_risk['f_boiler_age'] = input_risk.apply(lambda row: boiler_age_lookup_value(row, 'boiler_age_factor', pricing_date,boiler_age_df), axis=1)
        input_risk['f_rads'] = input_risk.apply(lambda row: radiators_lookup_value(row, 'factor', pricing_date,rads_df), axis=1)
        input_risk['f_spl_rads'] = input_risk.apply(lambda row: spl_radiators_lookup_value(row, 'factor', pricing_date,spl_rads_df), axis=1)
        input_risk['f_claims'] = input_risk.apply(lambda row: claims_lookup_value(row, 'claims_tenure_factor', pricing_date,Claims_df), axis=1)
        input_risk['f_int_geo_boiler'] = input_risk.apply(lambda row: ratarea_boilertype_lookup_value(row, 'factor', pricing_date,ratearea_boilertype_df), axis=1)
        input_risk['f_int_geo_rads'] = input_risk.apply(lambda row: ratarea_rads_lookup_value(row, 'factor', pricing_date,ratarea_rads_df), axis=1)
        input_risk['f_int_rads_claims'] = input_risk.apply(lambda row: rads_claims_lookup_value(row, 'factor', pricing_date,rads_claims_df), axis=1)
        input_risk['f_int_claims_boiler'] = input_risk.apply(lambda row: claims_boilertype_lookup_value(row, 'factor', pricing_date,claims_boilertype_df), axis=1)
        input_risk['f_Claims_load'] = input_risk.apply(lambda row: lookup_value(row, 'factor', pricing_date,claims_load_df), axis=1)
        input_risk['f_Asv_price'] = input_risk.apply(lambda row: lookup_value(row, 'asv_base_price', pricing_date,asv_df), axis=1)
        input_risk['f_Exp_Claim_load'] = input_risk.apply(lambda row: lookup_value(row, 'expense_claims_load', pricing_date,exp_claim_df), axis=1)
        input_risk['f_Exp_Asv_load'] = input_risk.apply(lambda row: lookup_value(row, 'expense_asv_load', pricing_date,exp_asv_load), axis=1)
        input_risk['f_Flat_Load'] = input_risk.apply(lambda row: lookup_value(row, 'flat_load_expense', pricing_date,flat_load_df), axis=1)
        input_risk['f_Multi_bund_margin'] = input_risk.apply(lambda row: lookup_value(row, 'factor', pricing_date,multi_margin_df), axis=1)
        input_risk['f_Cap'] = input_risk.apply(lambda row: cap_collar_lookup_value(row, 'cap_percentage_value', pricing_date,cap_collar_df), axis=1)
        input_risk['f_Collar'] = input_risk.apply(lambda row: cap_collar_lookup_value(row, 'col_percentage_value', pricing_date,cap_collar_df), axis=1)
        input_risk['c_Risk_Premium'] =  input_risk['f_base_price']*input_risk['f_boiler_type']*input_risk['f_appl_make']*input_risk['f_geo_factor']*input_risk['f_boiler_age']*input_risk['f_rads']*input_risk['f_spl_rads']*input_risk['f_claims']*input_risk['f_int_geo_boiler']*input_risk['f_int_geo_rads']*input_risk['f_int_rads_claims']*input_risk['f_int_claims_boiler']*input_risk['f_Claims_load']
        input_risk['c_ASV_Premium'] = input_risk['f_Asv_price']
        input_risk['c_Expense_Premium'] = (input_risk['f_Exp_Claim_load']*input_risk['c_Risk_Premium'])+(input_risk['f_Exp_Asv_load']*input_risk['c_ASV_Premium'])+input_risk['f_Flat_Load']
        input_risk['Pre_Margin_Premium'] = input_risk['c_Risk_Premium'] + input_risk['c_ASV_Premium'] + input_risk['c_Expense_Premium']
        input_risk['Margin'] = input_risk['Pre_Margin_Premium']*input_risk['f_Multi_bund_margin']
        input_risk['Pre_Cap_Premium'] = input_risk['Pre_Margin_Premium']+input_risk['Margin']
        input_risk['Min_Premium'] = input_risk['LY_Price']*(input_risk['f_Collar']/100)
        input_risk['Max_Premium'] = input_risk['LY_Price']*(input_risk['f_Cap']/100)
        input_risk['Final_Premium'] = input_risk.apply(lambda row: min(max(row['Min_Premium'], row['Pre_Cap_Premium']), row['Max_Premium']),axis=1)
        return input_risk

if uploaded_file and pricing_date is not None:
    if st.button('Validate'):
        try:
            input_risk = pd.read_excel(uploaded_file)
            #st.session_state.input_risk = input_risk  # Store in session state          
            # Display statistics
            st.write(f"**Number of rows in your file**: {input_risk.shape[0]}")
            st.write(f"**Number of columns in your file**: {input_risk.shape[1]}")
            st.header("Check your uploaded File:")
            st.write(input_risk.head())
        except Exception as e:
            st.error(f"Error validating the file: {e}")



# Check if input_risk is in session state before displaying the Calculate button
if st.button('Calculate'):
    try:
        #input_risk['helper1'] = input_risk['pricing_key']+input_risk['price_group'].astype(str)
        premium_file = calculate_prices(input_risk)
        st.session_state.premium_file = premium_file
        st.success("Prices calculated successfully!!")
        st.header("Sample Output:")
        st.write(premium_file.head())
    except Exception as e:
        st.error(f"Error calculating prices: {e}")


# if st.button('Calculate'): 
#     premium_file = calculate_prices(uploaded_file)
#     st.session_state.premium_file = premium_file  # Store in session state
#     st.success("Prices calculated successfully!!")
#     st.header("Sample Output:")
#     st.write(premium_file.head())

        










# var1 = 'G0002'
# var2 = 50
# var3 = 14
# var4 = 'AL140'
# var5 = pricing_date

# result = geo_pschal_df.query(
#         'geo_groupid == @var1 and price_group == @var2 and exec_rule == @var3 and post_sector == @var4 and pricing_date_start <= @var5 and pricing_date_end >= @var5'
#     )
# if not result.empty:
#     st.write(result['geo_code'].values)
# else:
#     if var2 == 51:
#         st.write("ZZ")
#     elif var2 == 50:
#         st.write("ZY")
#     else:
#         st.write(1)

#st.write(result['geo_code'].values)  



