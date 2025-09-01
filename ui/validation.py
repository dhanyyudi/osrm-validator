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
        
        # NEW: Start Time Configuration
        with st.expander("Start Time Configuration"):
            st.write("Configure the start time parameter for OSRM API requests")
            
            col1, col2 = st.columns(2)
            
            with col1:
                use_current_time = st.checkbox(
                    "Use Current Time", 
                    value=True,
                    help="Use current timestamp for all requests"
                )
                
                use_custom_time = st.checkbox(
                    "Use Custom Time",
                    value=False,
                    help="Specify a custom start time for all requests"
                )
            
            with col2:
                if use_custom_time:
                    custom_date = st.date_input(
                        "Custom Date",
                        value=datetime.now().date(),
                        help="Select date for start time"
                    )
                    
                    custom_time = st.time_input(
                        "Custom Time",
                        value=datetime.now().time(),
                        help="Select time for start time"
                    )
                    
                    # Combine date and time
                    custom_datetime = datetime.combine(custom_date, custom_time)
                    st.info(f"Custom start time: {custom_datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')}")
                
                # Option for offset from current time
                time_offset_hours = st.number_input(
                    "Time Offset (hours)",
                    min_value=-24,
                    max_value=24,
                    value=0,
                    help="Offset in hours from current time (negative for past, positive for future)"
                )
            
            # Display effective start time
            if use_custom_time and 'custom_datetime' in locals():
                effective_start_time = custom_datetime
            else:
                effective_start_time = datetime.now() + timedelta(hours=time_offset_hours)
            
            st.info(f"Effective start time for validation: {effective_start_time.strftime('%Y-%m-%dT%H:%M:%S+00:00')}")
        
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
            
            # Prepare start time parameter
            if use_custom_time and 'custom_datetime' in locals():
                start_time_param = custom_datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            else:
                start_time_param = (datetime.now() + timedelta(hours=time_offset_hours)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
            
            # Add start_time to API settings
            api_settings_with_time = api_settings.copy()
            api_settings_with_time["START_TIME"] = start_time_param
            
            # Use full data or sample based on checkbox
            validation_data = prepared_data.sample(sample_count) if use_sample else prepared_data
            
            # Display info
            st.info(f"""
            Starting validation with the following settings:
            - OSRM Profile: {api_profile}
            - Start Time: {start_time_param}
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
                        api_settings_with_time,
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
        
        # Additional OSRM Parameters Section
        st.subheader("Additional OSRM Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Overview parameter
            overview_param = st.selectbox(
                "Overview",
                ["false", "full", "simplified"],
                index=0,
                help="Geometry overview level (false=none, full=detailed, simplified=reduced)"
            )
            
            # Steps parameter
            steps_param = st.selectbox(
                "Steps",
                ["true", "false"],
                index=0,
                help="Include turn-by-turn instructions"
            )
        
        with col2:
            # Geometries parameter
            geometries_param = st.selectbox(
                "Geometries",
                ["polyline6", "polyline", "geojson"],
                index=0,
                help="Geometry format for route coordinates"
            )
            
            # Approaches parameter
            approaches_param = st.text_input(
                "Approaches",
                value="unrestricted;unrestricted",
                help="Approach constraints for start and end points"
            )
        
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
                "Parameter": st.column_config.TextColumn(
                    "Parameter Name",
                    help="Custom parameter name (e.g., 'alternatives', 'continue_straight')"
                ),
                "Value": st.column_config.TextColumn(
                    "Parameter Value",
                    help="Parameter value"
                )
            }
        )
        
        # Save button
        if st.button("Save OSRM API Configuration"):
            # Convert edited profiles back to dictionary
            new_profiles = {row["Name"]: row["Value"] for _, row in edited_profile_df.iterrows() if row["Name"]}
            
            # Convert edited custom parameters back to dictionary
            new_custom_params = {row["Parameter"]: row["Value"] for _, row in edited_custom_params.iterrows() if row["Parameter"]}
            
            # Update settings
            new_settings = {
                "BASE_URL": base_url,
                "ACCESS_TOKEN": access_token,
                "PROFILES": new_profiles,
                "OVERVIEW": overview_param,
                "STEPS": steps_param,
                "GEOMETRIES": geometries_param,
                "APPROACHES": approaches_param,
                "CUSTOM_PARAMS": new_custom_params
            }
            
            # Save to session state
            st.session_state[SESSION_KEYS["OSRM_API_SETTINGS"]] = new_settings
            
            st.success("OSRM API settings saved successfully!")
            
            # Display current configuration
            with st.expander("Current Configuration Preview"):
                st.json(new_settings)