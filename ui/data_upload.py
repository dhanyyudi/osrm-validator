import streamlit as st
import pandas as pd
import io
from config.settings import REQUIRED_COLUMNS, SESSION_KEYS
from modules.data_cleaning.cleaner import clean_store_dc_data, filter_warehouse_data, prepare_store_dc_mapping
from utils.helpers import check_required_columns, dataframe_to_csv, get_timestamp

def show_data_upload():
    """
    Display the data upload and preparation UI
    """
    st.header("Data Upload & Preparation")
    
    # Upload options
    upload_option = st.radio(
        "Choose input data type",
        ["Upload Store-DC File", "Upload All Locations File", "Use Processed Data"]
    )
    
    if upload_option == "Upload Store-DC File":
        show_store_dc_upload()
    elif upload_option == "Upload All Locations File":
        show_all_locations_upload()
    else:
        show_processed_data_upload()

def show_store_dc_upload():
    """
    Display UI for uploading and processing Store-DC mapping data
    """
    uploaded_file = st.file_uploader("Upload Store-DC Mapping CSV file", type=['csv'])
    
    if uploaded_file is not None:
        # Read the CSV file
        try:
            df = pd.read_csv(uploaded_file)
            st.write(f"Data loaded successfully: {len(df)} rows")
            
            # Display data preview
            st.subheader("Data Preview")
            st.dataframe(df.head())
            
            # Check if data has required columns
            has_columns, missing_columns = check_required_columns(df, REQUIRED_COLUMNS)
            
            if not has_columns:
                st.error(f"Data is missing required columns: {', '.join(missing_columns)}")
                st.info(f"Required columns: {', '.join(REQUIRED_COLUMNS)}")
            else:
                # Process button
                if st.button("Process & Clean Data"):
                    with st.spinner("Cleaning and preparing data..."):
                        # Clean the data
                        cleaned_df, cleaning_stats = clean_store_dc_data(df)
                        
                        # Save to session state
                        st.session_state[SESSION_KEYS["PREPARED_DATA"]] = cleaned_df
                        
                        # Display processing results
                        st.success(f"Data processed successfully! {len(cleaned_df)} rows ready for validation.")
                        
                        # Show cleaning statistics
                        st.subheader("Data Cleaning Statistics")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Initial Data Count", cleaning_stats['initial_count'])
                        col2.metric("Rows with Missing Coords", cleaning_stats['rows_with_missing_coords'])
                        col3.metric("Duplicate Routes", cleaning_stats['duplicate_routes'])
                        
                        st.subheader("Cleaned Data Preview")
                        st.dataframe(cleaned_df.head())
                        
                        # Download button for cleaned data
                        st.download_button(
                            "Download Cleaned Data",
                            dataframe_to_csv(cleaned_df),
                            f"store_dc_cleaned_{get_timestamp()}.csv",
                            "text/csv",
                            key='download-cleaned-csv'
                        )
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

def show_all_locations_upload():
    """
    Display UI for uploading and processing locations data (stores and warehouses)
    """
    col1, col2 = st.columns(2)
    
    with col1:
        all_locations_file = st.file_uploader("Upload All Locations CSV file", type=['csv'])
    
    with col2:
        consolidated_file = st.file_uploader("Upload Consolidated Stores CSV file", type=['csv'])
    
    if all_locations_file is not None and consolidated_file is not None:
        try:
            # Read both CSV files
            all_locations_df = pd.read_csv(all_locations_file)
            consolidated_df = pd.read_csv(consolidated_file)
            
            st.write(f"All Locations data: {len(all_locations_df)} rows")
            st.write(f"Consolidated Stores data: {len(consolidated_df)} rows")
            
            # Display previews
            st.subheader("All Locations Preview")
            st.dataframe(all_locations_df.head())
            
            st.subheader("Consolidated Stores Preview")
            st.dataframe(consolidated_df.head())
            
            # Process button
            if st.button("Process & Create Store-DC Mapping"):
                with st.spinner("Processing data..."):
                    # Filter warehouse locations
                    warehouses_df = filter_warehouse_data(all_locations_df)
                    
                    # Create mapping
                    mapping_df = prepare_store_dc_mapping(consolidated_df, warehouses_df)
                    
                    # Clean the mapping
                    cleaned_mapping_df, cleaning_stats = clean_store_dc_data(mapping_df)
                    
                    # Save to session state
                    st.session_state[SESSION_KEYS["PREPARED_DATA"]] = cleaned_mapping_df
                    
                    # Display results
                    st.success(f"Data processed successfully! {len(cleaned_mapping_df)} Store-DC mappings ready for validation.")
                    
                    # Show statistics
                    st.subheader("Processing Statistics")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Warehouses Identified", len(warehouses_df))
                    col2.metric("Mappings Created", len(mapping_df))
                    col3.metric("Final Mappings", len(cleaned_mapping_df))
                    
                    st.subheader("Store-DC Mapping Preview")
                    st.dataframe(cleaned_mapping_df.head())
                    
                    # Download buttons
                    st.download_button(
                        "Download Store-DC Mapping",
                        dataframe_to_csv(cleaned_mapping_df),
                        f"store_dc_mapping_{get_timestamp()}.csv",
                        "text/csv",
                        key='download-mapping-csv'
                    )
                    
                    st.download_button(
                        "Download Warehouse Data",
                        dataframe_to_csv(warehouses_df),
                        f"warehouse_locations_{get_timestamp()}.csv",
                        "text/csv",
                        key='download-warehouse-csv'
                    )
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")

def show_processed_data_upload():
    """
    Display UI for uploading already processed data
    """
    uploaded_file = st.file_uploader("Upload processed CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            st.write(f"Data loaded successfully: {len(df)} rows")
            
            # Display preview
            st.subheader("Data Preview")
            st.dataframe(df.head())
            
            # Check if file is already a validation result
            is_validation_result = all(col in df.columns for col in 
                                     ['distance_to_dest', 'last_route_lon', 'last_route_lat', 'status'])
            
            if is_validation_result:
                # This is a validation result file
                st.info("Uploaded file is a validation result. Data will be available in the Analysis tab.")
                
                # Convert numeric columns to proper type for analysis
                numeric_cols = ['origin_lon', 'origin_lat', 'dest_lon', 'dest_lat', 
                               'last_route_lon', 'last_route_lat', 'distance_to_dest', 'retries']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Save to session state for analysis
                st.session_state[SESSION_KEYS["VALIDATION_RESULTS"]] = df
                
                # Jump to analysis tab
                st.success("Validation results loaded. Please open the 'Analysis' tab to view the analysis.")
            else:
                # Check if data has required columns for validation
                coord_columns = ['origin_lon', 'origin_lat', 'dest_lon', 'dest_lat']
                has_columns, missing_columns = check_required_columns(df, coord_columns)
                
                if not has_columns:
                    st.error(f"Data is missing required coordinate columns: {', '.join(missing_columns)}")
                else:
                    # IMPORTANT: Convert coordinate columns to numeric type
                    for col in coord_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Check for rows with invalid coordinates after conversion
                    invalid_coords = df[coord_columns].isnull().any(axis=1)
                    if invalid_coords.any():
                        # Show which rows have invalid coordinates
                        invalid_rows = df[invalid_coords][['store_location', 'store_number'] + coord_columns] if 'store_location' in df.columns else df[invalid_coords][coord_columns]
                        st.warning(f"Found {invalid_coords.sum()} row(s) with invalid/missing coordinates. These will be removed.")
                        with st.expander("View invalid rows"):
                            st.dataframe(invalid_rows)
                        # Remove invalid rows
                        df = df[~invalid_coords]
                    
                    # Display data type information
                    st.info("Data types after processing:")
                    dtype_info = pd.DataFrame({
                        'Column': coord_columns,
                        'Type': [str(df[col].dtype) for col in coord_columns]
                    })
                    st.dataframe(dtype_info)
                    
                    # Save to session state for validation
                    st.session_state[SESSION_KEYS["PREPARED_DATA"]] = df
                    
                    st.success(f"Data loaded and ready for validation. {len(df)} valid routes available. Please open the 'OSRM Validation' tab.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")