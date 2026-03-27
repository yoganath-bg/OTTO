import streamlit as st
import pandas as pd
import numpy as np

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
"Cap_n_Collar",
"Absolute_Capping",
"Minimum_Capping"
]


#retrieve the files from upload page. #change this to list comprehension. no need to read individually except geo_pschal_df.
base_price_df  = st.session_state.processed_data['Base_Price'].rename(columns={'base_price_claims': 'f_base_price'})
boiler_Type_df  = st.session_state.processed_data['Boiler_Type'].rename(columns={'factor': 'f_boiler_type'})
appl_make_df = st.session_state.processed_data['Appl_Make'].rename(columns={'factor': 'f_appl_make'})
PRD_GROUP_df = st.session_state.processed_data['PRD_GROUP']
geo_pschal_df = st.session_state.geo_pschal
geo_fachal_df = st.session_state.processed_data['GEO_FACHAL'].rename(columns={'factor': 'f_geo_factor'})
boiler_age_df  = st.session_state.processed_data['Boiler_Age'].rename(columns={'boiler_age_factor': 'f_boiler_age'})
rads_df  = st.session_state.processed_data['Rads'].rename(columns={'factor': 'f_rads'})
spl_rads_df = st.session_state.processed_data['Spl_Rads'].rename(columns={'factor': 'f_spl_rads'})
Claims_df = st.session_state.processed_data['Claims'].rename(columns={'claims_tenure_factor': 'f_claims'})
ratearea_boilertype_df = st.session_state.processed_data['Ratearea_Boilertype'].rename(columns={'geo_region': 'geo_code', 'factor': 'f_int_geo_boiler'})
ratarea_rads_df = st.session_state.processed_data['Ratarea_Rads'].rename(columns={'geo_region': 'geo_code', 'factor': 'f_int_geo_rads'})
rads_claims_df = st.session_state.processed_data['Rads_Claims'].rename(columns={'factor': 'f_int_rads_claims'})
claims_boilertype_df = st.session_state.processed_data['Claims_Boilertype'].rename(columns={'factor': 'f_int_claims_boiler'})
claims_load_df = st.session_state.processed_data['Claims_load'].rename(columns={'factor': 'f_Claims_load'})
asv_df = st.session_state.processed_data['Asv_price'].rename(columns={'asv_base_price': 'f_Asv_price'})
exp_claim_df = st.session_state.processed_data['Exp_Claim_load'].rename(columns={'expense_claims_load': 'f_Exp_Claim_load'})
exp_asv_load = st.session_state.processed_data['Exp_Asv_load'].rename(columns={'expense_asv_load': 'f_Exp_Asv_load'})
flat_load_df = st.session_state.processed_data['Flat_Load'].rename(columns={'flat_load_expense': 'f_Flat_Load'})
multi_margin_df = st.session_state.processed_data['Multi_bund_margin'].rename(columns={'factor': 'f_Multi_bund_margin'})
cap_collar_df = st.session_state.processed_data['Cap_n_Collar'].rename(columns={'cap_percentage_value': 'f_Cap', 'col_percentage_value': 'f_Collar'})
cap_collar_df['change_in_circumstan'] = cap_collar_df['change_in_circumstan'].apply(lambda x: x.upper() if isinstance(x, str) else x)
absolute_capping_df = st.session_state.processed_data['Absolute_Capping'].rename(columns={'absolute_cap_amount': 'absolute_Max_Premium'})
minimum_capping_df = st.session_state.processed_data['Minimum_Capping'].rename(columns={'price': 'absolute_Min_Premium'})



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

def merge_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df

def merge_combi_boiler_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df
    
def merge_appl_make_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'manufacturer_code', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'manufacturer_code'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'manufacturer_code']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_geo_group_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key'],  # Columns from the main DataFrame
        right_on=['pricing_key']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].fillna('G0001')
    return df

def merge_geo_code_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['geo_groupid', 'post_sector', 'price_group', 'exec_rule', value_to_return]],
        how='left',  # Keep all rows from the main DataFrame
        left_on=['geo_groupid', 'post_sector', 'price_group', 'exec_rule'],  # Match keys in main DataFrame
        right_on=['geo_groupid', 'post_sector', 'price_group', 'exec_rule']  # Match keys in lookup table
    )

    df[value_to_return] = df[value_to_return].astype(str)  # Ensure the column is a string type
    df[value_to_return] = df[value_to_return].fillna(
        df['price_group'].map({51: "ZZ", 50: "ZY"}).fillna("1")
    )
    
    return df

def merge_geo_factor_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'exec_rule', 'geo_code', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'exec_rule', 'geo_code'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'exec_rule', 'geo_code']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_boiler_age_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'boiler_age', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'boiler_age'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'boiler_age']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_radiators_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'radiators', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'radiators'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'radiators']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_spl_radiators_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'spl_radiators', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'spl_radiators'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'spl_radiators']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_claims_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'jobs_completed', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'jobs_completed'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'jobs_completed']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_ratarea_boilertype_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'geo_code', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'geo_code'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'geo_code']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_ratarea_rads_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'radiators', 'geo_code', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'geo_code'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'geo_code']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_rads_claims_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'radiators', 'jobs_completed', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'jobs_completed'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'radiators', 'jobs_completed']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_claims_boilertype_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'jobs_completed', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'jobs_completed'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'price_group', 'exec_rule', 'is_combi_boiler', 'jobs_completed']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(1)
    return df

def merge_cap_collar_lookup_value(df, value_to_return, pricing_date, lookup_table):
    df = df.merge(
        lookup_table[['pricing_key', 'exec_rule', 'boiler_age', 'jobs_completed', 'change_in_circumstan', value_to_return]],
        how='left',
        left_on=['pricing_key', 'exec_rule', 'boiler_age', 'jobs_completed', 'change_in_circumstan'],
        right_on=['pricing_key', 'exec_rule', 'boiler_age', 'jobs_completed', 'change_in_circumstan']
    )

    df[value_to_return] = df.apply(
        lambda row: float(row[value_to_return]) if row['price_group'] == 51 and not pd.isna(row[value_to_return]) else 100,
        axis=1
    )
    
    return df


def merge_absolute_cap(df, value_to_return, pricing_date, lookup_table):
    lookup_table = lookup_table.drop_duplicates(subset=['pricing_key'])
    df = df.merge(
        lookup_table[['pricing_key', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key'],  # Columns from the main DataFrame
        right_on=['pricing_key']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df


def merge_minimum_cap(df, value_to_return, pricing_date, lookup_table):
    lookup_table = lookup_table.drop_duplicates(subset=['pricing_key', 'exec_rule'])
    df = df.merge(
        lookup_table[['pricing_key', 'exec_rule', value_to_return]],
        how='left',  # Use 'left' join to keep all rows from the main DataFrame
        left_on=['pricing_key', 'exec_rule'],  # Columns from the main DataFrame
        right_on=['pricing_key', 'exec_rule']  # Columns from the lookup table
    )
    df[value_to_return] = df[value_to_return].astype(float).fillna(0)
    return df



def calculate_prices(input_risk):
    input_risk = merge_lookup_value(input_risk, 'f_base_price', pricing_date, base_price_df)
    input_risk = merge_combi_boiler_lookup_value(input_risk, 'f_boiler_type', pricing_date, boiler_Type_df)
    input_risk = merge_appl_make_lookup_value(input_risk, 'f_appl_make', pricing_date, appl_make_df)
    input_risk = merge_geo_group_lookup_value(input_risk, 'geo_groupid', pricing_date, PRD_GROUP_df)
    input_risk = merge_geo_code_lookup_value(input_risk, 'geo_code', pricing_date, geo_pschal_df)
    input_risk = merge_geo_factor_lookup_value(input_risk, 'f_geo_factor', pricing_date, geo_fachal_df)
    input_risk = merge_boiler_age_lookup_value(input_risk, 'f_boiler_age', pricing_date, boiler_age_df)
    input_risk = merge_radiators_lookup_value(input_risk, 'f_rads', pricing_date, rads_df)
    input_risk = merge_spl_radiators_lookup_value(input_risk, 'f_spl_rads', pricing_date, spl_rads_df)
    input_risk = merge_claims_lookup_value(input_risk, 'f_claims', pricing_date, Claims_df)
    input_risk = merge_ratarea_boilertype_lookup_value(input_risk, 'f_int_geo_boiler', pricing_date, ratearea_boilertype_df)
    input_risk = merge_ratarea_rads_lookup_value(input_risk, 'f_int_geo_rads', pricing_date, ratarea_rads_df)
    input_risk = merge_rads_claims_lookup_value(input_risk, 'f_int_rads_claims', pricing_date, rads_claims_df)
    input_risk = merge_claims_boilertype_lookup_value(input_risk, 'f_int_claims_boiler', pricing_date, claims_boilertype_df)
    input_risk = merge_lookup_value(input_risk, 'f_Claims_load', pricing_date, claims_load_df)
    input_risk = merge_lookup_value(input_risk, 'f_Asv_price', pricing_date, asv_df)
    input_risk = merge_lookup_value(input_risk, 'f_Exp_Claim_load', pricing_date, exp_claim_df)
    input_risk = merge_lookup_value(input_risk, 'f_Exp_Asv_load', pricing_date, exp_asv_load)
    input_risk = merge_lookup_value(input_risk, 'f_Flat_Load', pricing_date, flat_load_df)
    input_risk = merge_lookup_value(input_risk, 'f_Multi_bund_margin', pricing_date, multi_margin_df)
    input_risk = merge_cap_collar_lookup_value(input_risk, 'f_Cap', pricing_date, cap_collar_df)
    input_risk = merge_cap_collar_lookup_value(input_risk, 'f_Collar', pricing_date, cap_collar_df)
    #input_risk = merge_absolute_cap(input_risk, 'absolute_Max_Premium', pricing_date, absolute_capping_df)
    #input_risk = merge_minimum_cap(input_risk, 'absolute_Min_Premium', pricing_date, minimum_capping_df)




    input_risk['c_Risk_Premium'] =  input_risk['f_base_price']*input_risk['f_boiler_type']*input_risk['f_appl_make']*input_risk['f_geo_factor']*input_risk['f_boiler_age']*input_risk['f_rads']*input_risk['f_spl_rads']*input_risk['f_claims']*input_risk['f_int_geo_boiler']*input_risk['f_int_geo_rads']*input_risk['f_int_rads_claims']*input_risk['f_int_claims_boiler']*input_risk['f_Claims_load']
    input_risk['c_ASV_Premium'] = input_risk['f_Asv_price']
    input_risk['c_Expense_Premium'] = (input_risk['f_Exp_Claim_load']*input_risk['c_Risk_Premium'])+(input_risk['f_Exp_Asv_load']*input_risk['c_ASV_Premium'])+input_risk['f_Flat_Load']
    input_risk['Pre_Margin_Premium'] = input_risk['c_Risk_Premium'] + input_risk['c_ASV_Premium'] + input_risk['c_Expense_Premium']
    input_risk['Margin'] = input_risk['Pre_Margin_Premium']*input_risk['f_Multi_bund_margin']
    input_risk['Pre_Cap_Premium'] = input_risk['Pre_Margin_Premium']+input_risk['Margin']
    input_risk['Min_Premium'] = input_risk['LY_Price']*(input_risk['f_Collar']/100)
    input_risk['Max_Premium'] = input_risk['LY_Price']*(input_risk['f_Cap']/100)
    input_risk['Capped_Premium'] = input_risk.apply(lambda row: min(max(row['Min_Premium'], row['Pre_Cap_Premium']), row['Max_Premium']),axis=1)
    input_risk = merge_absolute_cap(input_risk, 'absolute_Max_Premium', pricing_date, absolute_capping_df)
    input_risk = merge_minimum_cap(input_risk, 'absolute_Min_Premium', pricing_date, minimum_capping_df)
    input_risk['Final_Premium'] = input_risk.apply(lambda row: min(max(row['absolute_Min_Premium'], row['Capped_Premium']), row['absolute_Max_Premium']),axis=1)
    
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



