import pandas as pd
import glob


full_list = glob.glob(r"C:\Users\manickay\Downloads\py\tables\*")
chal_list = [x for x in full_list if 'DT_CHAL' in x]
print(chal_list)

# Helper Function for formatting SAP Tables
def format_SAP_table(input_file_path):
    
    #Column Names
    col_dict = {'Services Pricing : Execution Rule':'exec_rule',
                'Price Group':'price_group',
                'Pricing Key':'pricing_key',
                'Pricing Date': 'pricing_date'}
    
    #Read File
    #print("Reading and formatting: " + input_file_path)
    df = pd.read_excel(input_file_path) # read file
    df.rename(columns=col_dict,inplace=True)
    
    #pricing_key Formatting
    df.replace({'=':''}, regex=True, inplace=True) # replace "=" signs 
    df.replace({' ':''}, regex=True, inplace=True) # replace random spaces
    df['pricing_key'] = df['pricing_key'].str.split(";")
    df = df.explode('pricing_key' , ignore_index=True)
    
    #pricing_date Formatting
    df['pricing_date'] = df['pricing_date'].str.replace('[', '')
    df['pricing_date'] = df['pricing_date'].str.replace(']', '')
    df['pricing_date_start'] = df['pricing_date'].str.replace("..",",").str.split(",", expand=True)[0]
    df['pricing_date_end'] = df['pricing_date'].str.replace("..",",").str.split(",", expand=True)[1]
    df.drop(['pricing_date'], axis=1, inplace=True)
    
    return df

# Create a dictionary of SAP Tables
df_dictionary = {}

for file in chal_list: 
    df_dictionary[file] = format_SAP_table(file)

