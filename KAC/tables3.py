import pandas as pd
from datetime import datetime
import streamlit as st
import re


st.set_page_config(
    page_title="Welcome to the Pricing World",
    page_icon="BG_Flame_Big.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

baseprice_user_file = st.file_uploader(label = 'Upload BasePrice Table', help = 'upload your SAP table',label_visibility="visible")

df = pd.read_excel(baseprice_user_file)

st.write(df)




def cleaned_lists(s):
    if pd.isna(s):
        return []
    if isinstance(s, int):
        return [s]
    if '>' in s:
        return [int(100)]
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

# Define the process_dataframe function
def process_dataframe(df):
    # Rename main columns
    col_dict = {
        'Services Pricing : Execution Rule': 'exec_rule',
        'Pricing Exec Rule': 'exec_rule',
        'PRICING_EXEC_RULE': 'exec_rule',
        'PRICE_KEY': 'pricing_key',
        'Pricing Date': 'pricing_date',
        'PRICE_DT_FR': 'pricing_date_start',
        'PRICE_DT_TO': 'pricing_date_end',
        'Boiler Age': 'boiler_age',
        'SPRC : RADS': 'radiators',
        'No. Spec. Radiators': 'spl_radiators',
        'No. of Jobs Complete': 'jobs_completed',
    }
    df.rename(columns=col_dict, inplace=True)

    # Basic formatting
    df.replace({'=': ''}, regex=True, inplace=True)  # replace "=" signs
    df.replace({' ': ''}, regex=True, inplace=True)  # replace random spaces
    df.columns = df.columns.str.replace(': ', '', regex=False).str.replace('- ', '', regex=False).str.lower().str.replace('  ', '', regex=False).str.replace(' ', '_', regex=False)


    # Check if boiler_age column exists
    if 'boiler_age' in df.columns:
        print("boiler_age column exists")
        df['boiler_age'] = df['boiler_age'].apply(cleaned_lists)
        st.write("After applying cleaned_lists:")
        st.write(df['boiler_age'].head())  # Print the first few rows for debugging
        df = df.explode('boiler_age').reset_index(drop=True)
        st.write("After exploding boiler_age:")
        st.write(df)  # Print the first few rows for debugging
    else:
        print("boiler_age column does not exist")

    return df

df = process_dataframe(df)

st.write(df)

#     # Boiler Age Explosion Function
# def cleaned_lists(s):
#     if pd.isna(s):
#         return []
#     if isinstance(s, int):
#         return [s]
#     if '>' in s:
#         return ['Maximum']
#     elif re.match(r'\[\d+\.\.\d+\]', s):
#         match = re.match(r'\[(\d+)\.\.(\d+)\]', s)
#         if match:
#             start, end = map(int, match.groups())
#             return list(range(start, end + 1))
#     elif re.match(r'(\d+\s*;\s*)+\d+', s):
#         return [int(x) for x in s.split(';')]
#     elif re.match(r'^\d+$', s):
#         return [int(s)]
#     return []

# def process_dataframe(df):

#     # Rename main columns
#     col_dict = {
#         'Services Pricing : Execution Rule': 'exec_rule',
#         'Pricing Exec Rule': 'exec_rule',
#         'PRICING_EXEC_RULE': 'exec_rule',
#         'PRICE_KEY': 'pricing_key',
#         'Pricing Date': 'pricing_date',
#         'PRICE_DT_FR': 'pricing_date_start',
#         'PRICE_DT_TO': 'pricing_date_end',
#         'Boiler Age': 'boiler_age',
#         'SPRC : RADS': 'radiators',
#         'No. Spec. Radiators': 'spl_radiators',
#         'No. of Jobs Complete': 'jobs_completed',
#     }
#     df.rename(columns=col_dict, inplace=True)

#     # Basic formatting
#     df.replace({'=': ''}, regex=True, inplace=True)  # replace "=" signs
#     df.replace({' ': ''}, regex=True, inplace=True)  # replace random spaces
#     df.columns = df.columns.str.replace(': ', '', regex=False).str.replace('- ', '', regex=False).str.lower().str.replace('  ', '', regex=False).str.replace(' ', '_', regex=False)




#         # Applying cleaned age function to Boiler age column
#     if 'boiler_age' in df.columns:
#         df['boiler_age'] = df['boiler_age'].apply(cleaned_lists)
#         df = df.explode('boiler_age').reset_index(drop=True)





#     return df



