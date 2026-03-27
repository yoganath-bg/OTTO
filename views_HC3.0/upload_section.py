import pandas as pd
from datetime import datetime
import streamlit as st
import re


st.title("Upload your Tables ⬆️")

st.markdown("""   
    <hr style="border: 1px solid #0093f5; margin: 20px 0;">
""", unsafe_allow_html=True)

@st.cache_data
def process_dataframe(df):

    # Rename main columns
    col_dict = {
        'Services Pricing : Execution Rule': 'exec_rule',
        'Pricing Exec Rule': 'exec_rule',
        'PRICING_EXEC_RULE': 'exec_rule',
        'PRICE_KEY': 'pricing_key',
        'Current Product Key' : 'pricing_key',
        'Pricing Date': 'pricing_date',
        'Price Date':'pricing_date',
        'PRICE_DT_FR': 'pricing_date_start',
        'PRICE_DT_TO': 'pricing_date_end',
        'Boiler Age': 'boiler_age',
        'SPRC : RADS': 'radiators',
        'No. Spec. Radiators': 'spl_radiators',
        'No. of Jobs Complete': 'jobs_completed',
    }
    df.rename(columns=col_dict, inplace=True)

    # Basic formatting

    #df.replace({r'(?<!>)=': ''}, regex=True, inplace=True)
    df.replace({' ': ''}, regex=True, inplace=True)  # replace random spaces
    df.columns = df.columns.str.replace(': ', '', regex=False).str.replace('- ', '', regex=False).str.lower().str.replace('  ', '', regex=False).str.replace(' ', '_', regex=False)

        # Claims, Rads and Spl Rads Expand & Explode Function
    def cleaned_lists(s):
        if pd.isna(s):
            return []
        if isinstance(s, int):
            return [s]
        if '=' in s:
            if '>=' in s:
                start_value = int(s[2:])
                return list(range(start_value, 16))
            elif '<=' in s:
                return int(s[2:])  # Handle case where input is '<=0'
            elif '>' in s:
                start_value = int(s[1:])
                return list(range(start_value + 1, 16))
            elif re.match(r'(\d+\s*;\s*)+\d+', s):
                numbers = re.findall(r'\d+', s)  # Extract only valid numbers
                return [int(x) for x in numbers]
            else:
            # Handle cases like '1;=2;=3;=4' by removing '=' and splitting by ';'
                numbers = s.replace('=', '').split(';')
                return [int(x) for x in numbers]
            # else:
            #     return [int(s)]
        if '>' in s:
            start_value = int(s[1:])
            return list(range(start_value+1, 16))
        elif re.match(r'\[\d+\.\.\d+\]', s):
            match = re.match(r'\[(\d+)\.\.(\d+)\]', s)
            if match:
                start, end = map(int, match.groups())
                return list(range(start, end + 1))
        elif re.match(r'(\d+\s*;\s*)+\d+', s):
            return [int(x) for x in s.split(';')]
        elif re.match(r'^\d+$', s):
            return [int(s)]
        return []
    


    # Boiler Age Explosion Function
    def cleaned_boiler(s):
        if pd.isna(s):
            return []
        if isinstance(s, int):
            return [s]
        if '>' in s:
            start_value = int(s[1:])
            return list(range(start_value, 41))
        elif re.match(r'\[\d+\.\.\d+\]', s):
            match = re.match(r'\[(\d+)\.\.(\d+)\]', s)
            if match:
                start, end = map(int, match.groups())
                return list(range(start, end + 1))
        elif re.match(r'(\d+\s*;\s*)+\d+', s):
            return [int(x) for x in s.split(';')]
        elif re.match(r'^\d+$', s):
            return [int(s)]
        return []
        


    # Applying cleaned age function to radiators column
    if 'radiators' in df.columns:
        df['radiators'] = df['radiators'].apply(cleaned_lists)
        df = df.explode('radiators').reset_index(drop=True)

    # Applying cleaned age function to spl_radiators column
    if 'spl_radiators' in df.columns:
        df['spl_radiators'] = df['spl_radiators'].apply(cleaned_lists)
        df = df.explode('spl_radiators').reset_index(drop=True)

    # Applying cleaned age function to jobs_completed column
    if 'jobs_completed' in df.columns:
        df['jobs_completed'] = df['jobs_completed'].apply(cleaned_lists)
        df = df.explode('jobs_completed').reset_index(drop=True)
    
    df.replace({'=': ''}, regex=True, inplace=True)  # replace "=" signs

        # Applying cleaned age function to Boiler age column
    if 'boiler_age' in df.columns:
        df['boiler_age'] = df['boiler_age'].apply(cleaned_boiler)
        df = df.explode('boiler_age').reset_index(drop=True)

    # Pricing key explosion
    if 'pricing_key' in df.columns:
        df['pricing_key'] = df['pricing_key'].str.split(";")
        df = df.explode('pricing_key', ignore_index=True)

    # Pricing group explosion
    if 'price_group' in df.columns:
        df['price_group'] = df['price_group'].str.split(";")
        df = df.explode('price_group', ignore_index=True)

    # Appliance Type explosion
    if 'appliance_type' in df.columns:
        df['appliance_type'] = df['appliance_type'].apply(lambda x: x.split(";") if pd.notna(x) else x)
        df = df.explode('appliance_type', ignore_index=True)

    

    # Pricing date formatting
    if 'pricing_date' in df.columns:
        df['pricing_date'] = df['pricing_date'].str.replace('[', '')
        df['pricing_date'] = df['pricing_date'].str.replace(']', '')
        df[['pricing_date_start', 'pricing_date_end']] = df['pricing_date'].str.replace('..', ',').str.split(",", expand=True)
        df.drop(['pricing_date'], axis=1, inplace=True)
        df['pricing_date_start'] = df['pricing_date_start'].str.replace('.', '-')
        #df['pricing_date_start'] = pd.to_datetime(df['pricing_date_start'], errors='coerce').dt.date
        df['pricing_date_end'] = df['pricing_date_end'].str.replace('.', '-')
        #df['pricing_date_end'] = df['pricing_date_end'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
        
    #df['pricing_date_start'] = pd.to_datetime(df['pricing_date_start'], errors='coerce').dt.date
    #df['pricing_date_end'] = df['pricing_date_end'].apply(lambda x: x.date() if isinstance(x, datetime) else x)
    #df['pricing_date_end'] = df['pricing_date_end'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d') if isinstance(x, str) else x)


    #Change exec_rule, price_group to integer
    for i in ['exec_rule', 'price_group']:
        if i in df.columns:
            df[i] = df[i].astype(int)

    ## filter only for latest rules and price rule 14. No exec rule is available in PRD_Group
    if "exec_rule" in df.columns:
        df = df[df['exec_rule'] == 14]

    hc_list = ["BNI1","BNI2","CNI1","CNI2","DNI1","DNI2","HNI1","HNI2",
                "2SIS","2FIS","3FIS","3SIS","2PDI","2PFI","HEFI","HEWI"]

    if "pricing_key" in df.columns:
        df = df[df['pricing_key'].isin(hc_list)]
    
    df = df[df['pricing_date_end'].astype(str).str.contains('9999')]
    #df = df[(df['pricing_date_end'] == '9999-12-31') | (df['pricing_date_end'] == '31-12-9999') | (df['pricing_date_end'] == 9999) ]
    
    if "campaign-subcode" in df.columns:
        df = df[df['campaign-subcode'].isna() | (df['campaign-subcode'] == '')]

    return df




# List of file labels
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
"GEO_PSCHAL",
"GEO_FACHAL",
"Absolute_Capping",
"Minimum_Capping"
]

# Initialize session state for uploaded files and processed data
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {label: None for label in file_labels}
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = {label: None for label in file_labels}


# Create a 6x3 matrix of file uploaders
uploaded_files = {}
for i in range(0, len(file_labels), 3):
    cols = st.columns(3)
    for j, col in enumerate(cols):
        if i + j < len(file_labels):
            label = file_labels[i + j]
            with col:
                uploaded_file = st.file_uploader(label=f'Upload {label} Table', help=f'Upload unformatted SAP Table here', label_visibility="visible")
                if uploaded_file is not None:
                    st.session_state.uploaded_files[label] = uploaded_file
                    uploaded_files[label] = uploaded_file

# Add a "Process" button
if st.button('Process'):
    all_processed = True
    for label in file_labels:
        uploaded_file = uploaded_files.get(label)
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.session_state.processed_data[label] = process_dataframe(df)
            except Exception as e:
                st.error(f"Error processing {label}: {e}")
                all_processed = False
        else:
            st.write(f"Please upload {label}.")
            all_processed = False
    
    if all_processed:
        st.success("All tables processed successfully")


# # Create a 6x3 matrix of file uploaders
# for i in range(0, len(file_labels), 3):
#     cols = st.columns(3)
#     for j, col in enumerate(cols):
#         if i + j < len(file_labels):
#             label = file_labels[i + j]
#             with col:
#                 uploaded_file = st.file_uploader(label=f'Upload {label} Table', help=f'Upload unformatted SAP Table here', label_visibility="visible")
#                 if uploaded_file is not None:
#                     #st.session_state.uploaded_files[label] = uploaded_file
#                     df = pd.read_excel(uploaded_file)
#                     st.session_state.processed_data[label] = process_dataframe(df)
#                     #st.write(st.session_state.processed_data[label])
#                 #elif st.session_state.processed_data[label] is not None:
#                     #st.write(st.session_state.processed_data[label])
#                 else:
#                     st.write(f"Please upload {label}.")

if st.session_state.processed_data["GEO_PSCHAL"] is not None:
    acq_geo_pschal = st.session_state.processed_data["GEO_PSCHAL"][['geo_groupid','pricing_date_start','pricing_date_end','post_sector',
                                                                'exec_rule','acq_geo']]
    acq_geo_pschal['price_group'] = 50
    acq_geo_pschal.rename(columns = {'acq_geo':'geo_code'},inplace = True)


    ren_geo_pschal = st.session_state.processed_data["GEO_PSCHAL"][['geo_groupid','pricing_date_start','pricing_date_end','post_sector',
                                                                'exec_rule','ren_geo']]
    ren_geo_pschal['price_group'] = 51
    ren_geo_pschal.rename(columns = {'ren_geo':'geo_code'},inplace = True)

    geo_pschal = pd.concat([acq_geo_pschal,ren_geo_pschal], ignore_index=True)

    st.session_state.geo_pschal = geo_pschal
    
    #st.dataframe(geo_pschal)

    #st.download_button(data=st.session_state.geo_pschal,file_name='geo.csv',mime = "text/csv",label='geo table')


#Example of accessing the processed data in another page
if st.button('Show Processed Data'):
    for label in file_labels:
        if st.session_state.processed_data[label] is not None:
            st.write(f"Processed data for {label}:")
            st.write(st.session_state.processed_data[label])
        else:
            st.write(f"No data available for {label}.")


# pricing_date = st.date_input(label = 'Pick the pricing date')

# pricing_date = pd.to_datetime(pricing_date, errors='coerce').date()




##look up logic. 
# Define the lookup variables
# var1 = 'CNI1'
# var2 = 51
# var3 = 14
# var4 = pricing_date

# Use the query method to find the matching row
#result = df.query('pricing_key == @var1 and price_group == @var2 and exec_rule == @var3 and pricing_date_start <= @var4 and pricing_date_end >= @var4')

# Get the value from the 4th column
#matching_value = result['base_price_claims'].values if not result.empty else None

#st.write(matching_value)

#st.download_button("Download your table",df.to_csv(),mime = 'text/csv',file_name = 'output.csv')