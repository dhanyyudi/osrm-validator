import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
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
    
    # Initialize session state for start time if not exists
    if "start_time_option" not in st.session_state:
        st.session_state.start_time_option = "current"
    if "custom_start_date" not in st.session_state:
        st.session_state.custom_start_date = datetime.now().date()
    if "custom_start_time" not in st.session_state:
        st.session_state.custom_start_time = datetime.now().time()
    if "time_offset_hours" not in st.session_state:
        st.session_state.time_offset_hours = 0
    
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
        
        # Start Time Configuration
        st.subheader("Start Time Parameter")
        
        # Use session state for persistent values
        start_time_option = st.radio(
            "Start Time Option",
            ["Use Current Time", "Use Custom Time", "Add to Custom Parameters"],
            index=["Use Current Time", "Use Custom Time", "Add to Custom Parameters"].index(st.session_state.start_time_option) if st.session_state.start_time_option in ["Use Current Time", "Use Custom Time", "Add to Custom Parameters"] else 0,
            key="start_time_radio"
        )
        
        # Update session state
        if start_time_option == "Use Current Time":
            st.session_state.start_time_option = "current"
        elif start_time_option == "Use Custom Time":
            st.session_state.start_time_option = "custom"
        else:
            st.session_state.start_time_option = "manual"
        
        if start_time_option == "Use Custom Time":
            col1, col2 = st.columns(2)
            with col1:
                custom_date = st.date_input(
                    "Date", 
                    value=st.session_state.custom_start_date,
                    key="custom_date_input"
                )
                st.session_state.custom_start_date = custom_date
                
            with col2:
                custom_time = st.time_input(
                    "Time", 
                    value=st.session_state.custom_start_time,
                    key="custom_time_input"
                )
                st.session_state.custom_start_time = custom_time
            
            # Combine date and time
            custom_datetime = datetime.combine(custom_date, custom_time)
            start_time_value = custom_datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            
            st.code(f"start_time: {start_time_value}")
            
        elif start_time_option == "Add to Custom Parameters":
            st.info("Add 'start_time' parameter manually in Custom Parameters section below")
            start_time_value = None
            
        else:  # Use Current Time
            start_time_value = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
            st.code(f"start_time: {start_time_value}")
        
        # Custom parameters section
        st.subheader("Custom Parameters")
        
        # Allow users to add custom parameters
        custom_params = api_settings.get("CUSTOM_PARAMS", {})
        
        # Create DataFrame for custom parameters
        custom_param_data = [{"Parameter": k, "Value": v} for k, v in custom_params.items()]
        if not custom_param_data:
            custom_param_data = [{"Parameter": "", "Value": ""}]
        
        custom_param_df = pd.DataFrame(custom_param_data)
        
        # Display editable custom parameters
        edited_custom_params = st.data_editor(
            custom_param_df,
            num_rows="dynamic",
            key="custom_params_editor",
            column_config={
                "Parameter": st.column_config.TextColumn("Parameter Name"),
                "Value": st.column_config.TextColumn("Parameter Value")
            }
        )
        
        # Helper section for start_time
        if start_time_option == "Add to Custom Parameters":
            st.info("💡 **Quick Add start_time:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Current Time"):
                    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
                    st.code(f"Parameter: start_time\nValue: {current_time}")
            
            with col2:
                offset_hours = st.number_input("Hours Offset", value=0, min_value=-24, max_value=24, key="offset_input")
                if st.button("Apply Offset"):
                    offset_datetime = datetime.now() + timedelta(hours=offset_hours)
                    offset_time_str = offset_datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                    st.code(f"Parameter: start_time\nValue: {offset_time_str}")
            
            with col3:
                if st.button("Custom Time"):
                    # Use the values from session state
                    custom_datetime = datetime.combine(st.session_state.custom_start_date, st.session_state.custom_start_time)
                    custom_time_str = custom_datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                    st.code(f"Parameter: start_time\nValue: {custom_time_str}")
        
        # Save button
        if st.button("Save OSRM API Configuration"):
            # Convert edited profiles back to dictionary
            new_profiles = {}
            for _, row in edited_profile_df.iterrows():
                if row["Name"]:
                    new_profiles[row["Name"]] = row["Value"]
            
            # Convert edited custom parameters back to dictionary
            new_custom_params = {}
            for _, row in edited_custom_params.iterrows():
                if row["Parameter"]:
                    new_custom_params[row["Parameter"]] = row["Value"]
            
            # Build new settings
            new_settings = {
                "BASE_URL": base_url,
                "ACCESS_TOKEN": access_token,
                "PROFILES": new_profiles,
                "CUSTOM_PARAMS": new_custom_params
            }
            
            # Add start_time if configured via UI (not manual)
            if start_time_option != "Add to Custom Parameters" and 'start_time_value' in locals():
                new_settings["START_TIME"] = start_time_value
            
            # Save to session state
            st.session_state[SESSION_KEYS["OSRM_API_SETTINGS"]] = new_settings
            
            st.success("OSRM API settings saved successfully!")
            
            # Show what was saved
            st.write("**Saved Configuration:**")
            if "START_TIME" in new_settings:
                st.write(f"- Start Time: {new_settings['START_TIME']}")
            if new_custom_params:
                st.write("- Custom Parameters:")
                for param, value in new_custom_params.items():
                    st.write(f"  - {param}: {value}")
    
    else:
        st.warning("No data prepared yet. Please upload and prepare data in the 'Data Upload & Preparation' tab first.")