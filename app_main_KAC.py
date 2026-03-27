import streamlit as st

#--- Page Setup ---

st.set_page_config(
    page_title="OTTO - BG Pricing Engine Test",
    page_icon="BG_Flame_Big.ico",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
         'Get Help': 'https://www.extremelycoolapp.com/help',
         'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "# This is a header. This is an *extremely* cool app!"}
)

about_page = st.Page(
                page = "views/about.py",
                title = "About",
                icon = ":material/home:",
                default=True,
)

upload_page = st.Page(
                page = "views/upload_section_test.py",
                title = "Upload Section",
                icon = ":material/drive_folder_upload:",
)

exploration_page = st.Page(
                page = "views/exploration.py",
                title = "Explore Results",
                icon = ":material/explore:",
)

calculation_page = st.Page(
                page = "views/calculation_section_test.py",
                title = "Validate & Calculate",
                icon = ":material/calculate:",
)

download_page = st.Page(
                page = "views/download.py",
                title = "Download Results",
                icon = ":material/download:",
)

ask_page = st.Page(
                page = "views/ask.py",
                title = "Ask your Data",
                icon = ":material/robot_2:",
)


# -- NAVIGATION SETUP --

pg = st.navigation(
    {
        "Info" : [about_page],
        "Upload": [upload_page],
        "Calculate" : [calculation_page],
        "Explore": [exploration_page,ask_page],
        "Download": [download_page]
    }
)


lines = [
    "**_Developed by_** : Yoga Manickavasakam",
    "**_Credits_:**",
    "Peter Vickers"
  
]

for line in lines:
    st.sidebar.markdown(line,unsafe_allow_html=True)

st.logo("BG_Logo_Big.jpg",size = 'large',link="https://www.britishgas.co.uk/cover/boiler-and-heating.html")








# -- Run Navigation ---
pg.run()