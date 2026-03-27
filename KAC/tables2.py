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

        # Boiler Age Explosion Function
    def cleaned_lists(s):
        if pd.isna(s):
            return []
        if isinstance(s, int):
            return [s]
        if '>' in s:
            return ['Maximum']
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
        
    # Applying cleaned age function to Boiler age column
    if 'boiler_age' in df.columns:
        df['boiler_age'] = df['boiler_age'].apply(cleaned_lists)
        df = df.explode('boiler_age').reset_index(drop=True)

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
    df['pricing_date_start'] = pd.to_datetime(df['pricing_date_start'], errors='coerce').dt.date

    df['pricing_date_end'] = df['pricing_date_end'].str.replace('.', '-')
    df['pricing_date_end'] = df['pricing_date_end'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d').date())

    # Change exec_rule, price_group to integer
    for i in ['exec_rule', 'price_group']:
        df[i] = df[i].astype(int)

    return df



df = process_dataframe(df)

pricing_date = st.date_input(label = 'Pick the pricing date')

pricing_date = pd.to_datetime(pricing_date, errors='coerce').date()


st.write(pricing_date)



##look up logic. 
# Define the lookup variables
var1 = 'CNI1'
var2 = 51
var3 = 14
var4 = pricing_date

# Use the query method to find the matching row
#result = df.query('pricing_key == @var1 and price_group == @var2 and exec_rule == @var3 and pricing_date_start <= @var4 and pricing_date_end >= @var4')

# Get the value from the 4th column
#matching_value = result['base_price_claims'].values if not result.empty else None

#st.write(matching_value)

#st.download_button("Download your table",df.to_csv(),mime = 'text/csv',file_name = 'output.csv')