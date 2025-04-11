import pandas as pd
import numpy as np
import streamlit as st

def clean_store_dc_data(df):
    """
    Clean and prepare store-DC mapping data for OSRM validation.
    
    Args:
        df (pandas.DataFrame): Input DataFrame with store and DC data
        
    Returns:
        pandas.DataFrame: Cleaned and prepared DataFrame
    """
    # Make a copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Basic cleaning operations
    # 1. Remove rows with missing coordinates
    initial_count = len(cleaned_df)
    coord_columns = ['origin_lon', 'origin_lat', 'dest_lon', 'dest_lat']
    missing_coords = cleaned_df[coord_columns].isnull().any(axis=1)
    cleaned_df = cleaned_df[~missing_coords]
    
    # 2. Remove duplicate routes based on coordinates
    duplicated_count = cleaned_df.duplicated(subset=coord_columns, keep=False).sum()
    cleaned_df = cleaned_df.drop_duplicates(subset=coord_columns)
    
    # 3. Round coordinates to 6 decimal places for consistency
    for col in coord_columns:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].round(6)
    
    # 4. Convert column types if needed
    for col in ['store_number', 'dc_code']:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].astype(str)
    
    # Return the cleaned DataFrame with cleaning statistics
    cleaning_stats = {
        'initial_count': initial_count,
        'rows_with_missing_coords': missing_coords.sum(),
        'duplicate_routes': duplicated_count,
        'final_count': len(cleaned_df)
    }
    
    return cleaned_df, cleaning_stats

def filter_warehouse_data(df):
    """
    Filter warehouse locations from all locations data.
    
    Args:
        df (pandas.DataFrame): DataFrame with location data
        
    Returns:
        pandas.DataFrame: Filtered DataFrame with only warehouse locations
    """
    # Filter rows where "Store Location" contains "WH" (case sensitive)
    wh_only = df[df['Store Location'].str.contains('WH', case=True, na=False)]
    
    # Remove duplicates based on Store Code and coordinates
    wh_unique = wh_only.drop_duplicates(subset=['Store Code', 'Lat ', 'Long'])
    
    # Remove duplicates based on Store Location and Store Code
    wh_unique = wh_unique.drop_duplicates(subset=['Store Location', 'Store Code'])
    
    return wh_unique

def prepare_store_dc_mapping(stores_df, warehouses_df):
    """
    Prepare store to DC mapping from stores and warehouses data.
    
    Args:
        stores_df (pandas.DataFrame): DataFrame with store data
        warehouses_df (pandas.DataFrame): DataFrame with warehouse data
        
    Returns:
        pandas.DataFrame: DataFrame with store-DC mapping ready for validation
    """
    # Create warehouse mapping dictionary
    warehouse_mapping = {}
    
    for _, wh in warehouses_df.iterrows():
        # Extract the code (part before the first colon or space)
        location = wh['Store Location']
        if ':' in location:
            code = location.split(':', 1)[0]
        else:
            code = location.split(' ', 1)[0]
        
        warehouse_mapping[code] = {
            'location': wh['Store Location'],
            'code': wh['Store Code'],
            'lat': wh['Lat '],
            'long': wh['Long']
        }
    
    # Process store data to match with warehouses
    result = []
    
    for _, store in stores_df.iterrows():
        loading_depot = store['LoadingDepot']
        
        # Skip if loading depot is empty
        if pd.isna(loading_depot):
            continue
        
        # Look for exact match
        if loading_depot in warehouse_mapping:
            wh_info = warehouse_mapping[loading_depot]
            
            # Check if store has valid coordinates
            if not pd.isna(store['Latitude']) and not pd.isna(store['Longitude']):
                result.append({
                    'store_location': store['StoreName'],
                    'store_number': store['StoreNumber'],
                    'dc_location': wh_info['location'],
                    'dc_code': wh_info['code'],
                    'origin_lon': wh_info['long'],
                    'origin_lat': wh_info['lat'],
                    'dest_lon': store['Longitude'],
                    'dest_lat': store['Latitude']
                })
        else:
            # Try partial matching in case the format is different
            for wh_code in warehouse_mapping:
                # Check if the LoadingDepot contains the warehouse code or vice versa
                if (wh_code in loading_depot) or (loading_depot in wh_code):
                    wh_info = warehouse_mapping[wh_code]
                    
                    if not pd.isna(store['Latitude']) and not pd.isna(store['Longitude']):
                        result.append({
                            'store_location': store['StoreName'],
                            'store_number': store['StoreNumber'],
                            'dc_location': wh_info['location'],
                            'dc_code': wh_info['code'],
                            'origin_lon': wh_info['long'],
                            'origin_lat': wh_info['lat'],
                            'dest_lon': store['Longitude'],
                            'dest_lat': store['Latitude']
                        })
                    break
    
    # Create the final DataFrame
    return pd.DataFrame(result)