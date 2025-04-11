import streamlit as st
from ui.data_upload import show_data_upload
from ui.validation import show_validation
from ui.analysis import show_analysis

# Page configuration
st.set_page_config(
    page_title="OSRM Route Validator",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title
st.title("OSRM Route Validator")
st.write("Validate OSRM routes by checking the distance between requested destinations and actual route endpoints.")

# Tabs for different stages of the process
tab1, tab2, tab3 = st.tabs(["1. Data Upload & Preparation", "2. OSRM Validation", "3. Analysis"])

with tab1:
    show_data_upload()

with tab2:
    show_validation()

with tab3:
    show_analysis()