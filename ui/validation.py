import streamlit as st
import pandas as pd
import time
from config.settings import DEFAULT_OSRM_API_SETTINGS, DEFAULT_SETTINGS, SESSION_KEYS
from modules.osrm.validator import validate_routes
from utils.helpers import dataframe_to_csv, get_timestamp

def show_validation():
    """
    Display the OSRM validation UI
    """
    st.header("OSRM API Validation")
    
    # First, set up OSRM API parameters
    setup_osrm_parameters()
    
    if SESSION_KEYS["PREPARED_DATA"] in st.session_state:
        # Get data from session state
        prepared_data = st.session_state[SESSION_KEYS["PREPARED_DATA"]]
        
        st.write(f"Data ready for validation: {len(prepared_data)} routes")
        
        # Validation settings
        st.subheader("Validation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Use stored profiles if available, otherwise use default
            if SESSION_KEYS["OSRM_API_SETTINGS"] in st.session_state:
                profiles = st.session_state[SESSION_KEYS["OSRM_API_SETTINGS"]].get("PROFILES", DEFAULT_OSRM_API_SETTINGS["PROFILES"])
            else:
                profiles = DEFAULT_OSRM_API_SETTINGS["PROFILES"]
                
            api_profile = st.selectbox(
                "OSRM Profile", 
                list(profiles.keys()),
                help="Select the OSRM routing profile to validate"
            )
            
            batch_size = st.slider(
                "Batch Size", 
                min_value=10, 
                max_value=500, 
                value=DEFAULT_SETTINGS["BATCH_SIZE"],
                step=10,
                help="Number of routes in one batch process"
            )
        
        with col2:
            max_workers = st.slider(
                "Thread Workers", 
                min_value=1, 
                max_value=10, 
                value=DEFAULT_SETTINGS["MAX_WORKERS"],
                help="Number of parallel threads for processing"
            )
            
            request_delay = st.slider(
                "Request Delay (seconds)", 
                min_value=0.05, 
                max_value=1.0, 
                value=DEFAULT_SETTINGS["REQUEST_DELAY"],
                step=0.05,
                help="Delay between API requests to avoid throttling"
            )
        
        # Additional parameters
        with st.expander("Advanced Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                max_retries = st.slider(
                    "Max Retries", 
                    min_value=1, 
                    max_value=10, 
                    value=DEFAULT_SETTINGS["MAX_RETRIES"],
                    help="Maximum number of retry attempts for failed requests"
                )
            
            with col2:
                base_delay = st.slider(
                    "Base Delay (seconds)", 
                    min_value=1, 
                    max_value=10, 
                    value=DEFAULT_SETTINGS["BASE_DELAY"],
                    help="Base delay for exponential backoff retry strategy"
                )
        
        # Validation control
        st.subheader("Validation Control")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Data preview button
            if st.button("Show Data Preview"):
                st.dataframe(prepared_data.head(10))
        
        with col2:
            # Data sample count
            sample_count = st.number_input(
                "Sample Size for Validation", 
                min_value=10, 
                max_value=len(prepared_data), 
                value=min(len(prepared_data), 100),
                help="Use a subset of data for quick validation"
            )
        
        with col3:
            # Use sample checkbox
            use_sample = st.checkbox(
                "Use Sample", 
                value=len(prepared_data) > 100,
                help="Validate using a subset of data for quick testing"
            )
        
        # Start validation button
        start_validation = st.button("Start OSRM API Validation")
        
        if start_validation:
            # Check if OSRM API settings are configured
            if SESSION_KEYS["OSRM_API_SETTINGS"] not in st.session_state:
                st.error("Please configure OSRM API settings before starting validation.")
                return
                
            api_settings = st.session_state[SESSION_KEYS["OSRM_API_SETTINGS"]]
            
            # Check if access token is provided
            if not api_settings.get("ACCESS_TOKEN"):
                st.error("Please provide an Access Token in OSRM API settings.")
                return
            
            # Use full data or sample based on checkbox
            validation_data = prepared_data.sample(sample_count) if use_sample else prepared_data
            
            # Display info
            st.info(f"""
            Starting validation with the following settings:
            - OSRM Profile: {api_profile}
            - Data: {"Sample of " + str(sample_count) + " routes" if use_sample else "All data (" + str(len(prepared_data)) + " routes)"}
            - Batch Size: {batch_size}
            - Thread Workers: {max_workers}
            - Request Delay: {request_delay} seconds
            """)
            
            # Run validation
            with st.spinner("Performing OSRM API validation..."):
                try:
                    # Start validation
                    start_time = time.time()
                    
                    # Run validation
                    results_df, validation_stats = validate_routes(
                        validation_data, 
                        api_settings,
                        api_profile, 
                        batch_size=batch_size, 
                        max_workers=max_workers, 
                        request_delay=request_delay
                    )
                    
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    # Save results to session state
                    st.session_state[SESSION_KEYS["VALIDATION_RESULTS"]] = results_df
                    st.session_state[SESSION_KEYS["VALIDATION_STATS"]] = validation_stats
                    
                    # Display success message
                    st.success(f"""
                    Validation completed in {execution_time:.1f} seconds!
                    - Successful routes: {validation_stats['successful_routes']} ({validation_stats['success_rate']:.1f}%)
                    - Failed routes: {validation_stats['failed_routes']}
                    """)
                    
                    # Preview results
                    st.subheader("Validation Results Preview")
                    st.dataframe(results_df.head(10))
                    
                    # Download results button
                    st.download_button(
                        "Download Validation Results",
                        dataframe_to_csv(results_df),
                        f"osrm_validation_{api_profile}_{get_timestamp()}.csv",
                        "text/csv",
                        key='download-validation-results'
                    )
                    
                    # Suggest next step
                    st.info("Please open the 'Analysis' tab to view detailed analysis of validation results.")
                
                except Exception as e:
                    st.error(f"Error during validation: {str(e)}")
    else:
        st.warning("No data prepared yet. Please upload and prepare data in the 'Data Upload & Preparation' tab first.")

def setup_osrm_parameters():
    """
    Set up OSRM API parameters
    """
    st.subheader("OSRM API Configuration")
    
    # Check if we already have OSRM API settings in session state
    if SESSION_KEYS["OSRM_API_SETTINGS"] in st.session_state:
        api_settings = st.session_state[SESSION_KEYS["OSRM_API_SETTINGS"]]
    else:
        api_settings = DEFAULT_OSRM_API_SETTINGS.copy()
    
    # Display parameter inputs with existing values
    with st.expander("OSRM API Parameters", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            base_url = st.text_input(
                "Base URL", 
                value=api_settings.get("BASE_URL", DEFAULT_OSRM_API_SETTINGS["BASE_URL"]),
                help="Base URL for OSRM API requests"
            )
        
        with col2:
            access_token = st.text_input(
                "Access Token", 
                value=api_settings.get("ACCESS_TOKEN", ""),
                help="Access token for OSRM API authentication"
            )
        
        # Profile management
        st.subheader("Routing Profiles")
        
        # Get existing profiles
        profiles = api_settings.get("PROFILES", DEFAULT_OSRM_API_SETTINGS["PROFILES"])
        
        # Create DataFrame for profiles
        profile_data = [{"Name": k, "Value": v} for k, v in profiles.items()]
        profile_df = pd.DataFrame(profile_data)
        
        # Display editable profiles
        edited_profile_df = st.data_editor(
            profile_df,
            num_rows="dynamic",
            key="profile_editor",
            column_config={
                "Name": st.column_config.TextColumn(
                    "Profile Name",
                    help="Display name for the profile"
                ),
                "Value": st.column_config.TextColumn(
                    "Profile Value",
                    help="Actual profile value used in API requests"
                )
            }
        )
        
        # Save button
        if st.button("Save OSRM API Configuration"):
            # Convert edited profiles back to dictionary
            new_profiles = {row["Name"]: row["Value"] for _, row in edited_profile_df.iterrows()}
            
            # Update settings
            new_settings = {
                "BASE_URL": base_url,
                "ACCESS_TOKEN": access_token,
                "PROFILES": new_profiles
            }
            
            # Save to session state
            st.session_state[SESSION_KEYS["OSRM_API_SETTINGS"]] = new_settings
            
            st.success("OSRM API settings saved successfully!")