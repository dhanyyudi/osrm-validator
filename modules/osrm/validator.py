import requests
import polyline
import pandas as pd
import time
import random
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils.helpers import add_retry_delay
from modules.osrm.distance import haversine
from config.settings import SESSION_KEYS

def get_last_route_coordinate(route_data):
    """
    Extract the last coordinate from a route's steps
    
    Args:
        route_data (dict): Route data response from OSRM API
        
    Returns:
        list or None: [lon, lat] of last coordinate or None if not found
    """
    try:
        # Try to get the last coordinate from the last step
        if 'routes' in route_data and route_data['routes']:
            route = route_data['routes'][0]
            
            if 'legs' in route and route['legs']:
                leg = route['legs'][0]
                
                if 'steps' in leg and leg['steps']:
                    steps = leg['steps']
                    last_step = steps[-1]
                    
                    # Check if we have geometry to extract coordinates
                    if 'geometry' in last_step:
                        geometry = last_step['geometry']
                        # Decode the polyline6 geometry
                        coordinates = polyline.decode(geometry, 6)
                        
                        if coordinates:
                            # Last coordinate in format [lat, lon], but we return [lon, lat]
                            return [coordinates[-1][1], coordinates[-1][0]]
        
        # Fallback to maneuver location if exists
        if 'routes' in route_data and route_data['routes']:
            if 'legs' in route_data['routes'][0] and route_data['routes'][0]['legs']:
                if 'steps' in route_data['routes'][0]['legs'][0] and route_data['routes'][0]['legs'][0]['steps']:
                    last_step = route_data['routes'][0]['legs'][0]['steps'][-1]
                    if 'maneuver' in last_step and 'location' in last_step['maneuver']:
                        return last_step['maneuver']['location']
        
        return None
    except Exception as e:
        st.error(f"Error extracting last coordinate: {e}")
        return None

def process_route(row, api_settings, api_profile, max_retries=3, base_delay=2, jitter=0.5):
    """
    Process a single route with OSRM API
    
    Args:
        row (dict): Row with route coordinates
        api_settings (dict): OSRM API settings
        api_profile (str): OSRM API profile to use
        max_retries (int): Maximum number of retry attempts
        base_delay (float): Base delay for exponential backoff
        jitter (float): Random jitter factor
        
    Returns:
        dict: Results of route processing
    """
    origin_lon = row['origin_lon']
    origin_lat = row['origin_lat']
    dest_lon = row['dest_lon']
    dest_lat = row['dest_lat']
    
    # Prepare request URL
    access_token = api_settings.get("ACCESS_TOKEN", "")
    base_url = api_settings.get("BASE_URL", "")
    
    # Use current timestamp for start_time parameter
    current_time = time.strftime('%Y-%m-%dT%H:%M:%S%%2B00:00')
    
    coordinates = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    url = f"{base_url}{api_profile}/{coordinates}?overview=false&steps=true&access_token={access_token}&approaches=unrestricted;unrestricted&geometries=polyline6&start_time={current_time}"
    
    # Initialize retry counter
    retry_count = 0
    
    while True:
        try:
            # Make the request
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            route_data = response.json()
            
            # Get the last coordinate of the route
            last_coordinate = get_last_route_coordinate(route_data)
            
            if last_coordinate:
                # Calculate distance between last route point and requested destination
                last_lon, last_lat = last_coordinate
                distance = haversine(last_lon, last_lat, dest_lon, dest_lat)
                
                return {
                    'origin_lon': origin_lon,
                    'origin_lat': origin_lat,
                    'dest_lon': dest_lon,
                    'dest_lat': dest_lat,
                    'last_route_lon': last_lon,
                    'last_route_lat': last_lat,
                    'distance_to_dest': distance,
                    'status': 'success',
                    'retries': retry_count
                }
            else:
                return {
                    'origin_lon': origin_lon,
                    'origin_lat': origin_lat,
                    'dest_lon': dest_lon,
                    'dest_lat': dest_lat,
                    'last_route_lon': None,
                    'last_route_lat': None,
                    'distance_to_dest': None,
                    'status': 'error: could not extract last coordinate',
                    'retries': retry_count
                }
        
        except (requests.exceptions.RequestException, 
                requests.exceptions.HTTPError, 
                requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout) as e:
            
            # Check if we have retries left
            if retry_count < max_retries:
                # Increment retry counter
                retry_count += 1
                
                # Add delay before retrying
                actual_delay = add_retry_delay(retry_count, base_delay, jitter)
                
                continue
            
            # All retries exhausted, return error
            return {
                'origin_lon': origin_lon,
                'origin_lat': origin_lat,
                'dest_lon': dest_lon,
                'dest_lat': dest_lat,
                'last_route_lon': None,
                'last_route_lat': None,
                'distance_to_dest': None,
                'status': f'error: {str(e)}',
                'retries': retry_count
            }
        
        except Exception as e:
            # For unexpected errors, don't retry
            return {
                'origin_lon': origin_lon,
                'origin_lat': origin_lat,
                'dest_lon': dest_lon,
                'dest_lat': dest_lat,
                'last_route_lon': None,
                'last_route_lat': None,
                'distance_to_dest': None,
                'status': f'error: unexpected - {str(e)}',
                'retries': retry_count
            }

def process_batch(batch_df, batch_index, total_batches, api_settings, api_profile, max_workers, request_delay):
    """
    Process a batch of routes
    
    Args:
        batch_df (pandas.DataFrame): Batch of routes to process
        batch_index (int): Current batch index
        total_batches (int): Total number of batches
        api_settings (dict): OSRM API settings
        api_profile (str): OSRM API profile to use
        max_workers (int): Maximum number of concurrent workers
        request_delay (float): Delay between requests
        
    Returns:
        pandas.DataFrame: Results for the batch
    """
    batch_placeholder = st.empty()
    batch_placeholder.info(f"Processing batch {batch_index}/{total_batches} ({len(batch_df)} routes)...")
    
    results = []
    success_count = 0
    error_count = 0
    retry_count = 0
    
    # Convert DataFrame to list of dicts for processing
    batch_rows = batch_df.to_dict('records')
    
    # Progress bar for the batch
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(process_route, row, api_settings, api_profile) for row in batch_rows]
        total = len(futures)
        
        # Process results as they complete
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                results.append(result)
                
                if result['status'] == 'success':
                    success_count += 1
                    # Count total retries
                    if 'retries' in result:
                        retry_count += result['retries']
                else:
                    error_count += 1
                    # Count total retries for errors too
                    if 'retries' in result:
                        retry_count += result['retries']
                
                # Update progress bar
                progress_bar.progress((i + 1) / total)
                status_text.text(f"Progress: {i+1}/{total} routes ({(i+1)/total*100:.1f}%)")
                
                # Small delay to avoid overwhelming the API
                time.sleep(request_delay)
            except Exception as e:
                st.error(f"Error processing route: {str(e)}")
                error_count += 1
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Update batch status
    batch_placeholder.success(f"Batch {batch_index} completed - Success: {success_count}, Errors: {error_count}, Total Retries: {retry_count}")
    
    return pd.DataFrame(results)

def validate_routes(df, api_settings, api_profile, batch_size=200, max_workers=7, request_delay=0.1):
    """
    Validate routes using OSRM API
    
    Args:
        df (pandas.DataFrame): DataFrame with routes to validate
        api_settings (dict): OSRM API settings
        api_profile (str): OSRM API profile to use
        batch_size (int): Number of routes per batch
        max_workers (int): Maximum number of concurrent workers
        request_delay (float): Delay between requests
        
    Returns:
        pandas.DataFrame: Results of validation
        dict: Validation statistics
    """
    # Total rows to process
    total_rows = len(df)
    total_batches = (total_rows + batch_size - 1) // batch_size
    
    st.info(f"Starting validation for {total_rows} routes with batch size {batch_size}...")
    st.info(f"Using {max_workers} workers, {request_delay}s delay between requests")
    
    # Track overall statistics
    overall_success = 0
    overall_errors = 0
    overall_retries = 0
    
    # Process in batches and save incrementally
    all_results = []
    
    # Main progress bar for all batches
    overall_progress = st.progress(0)
    
    for i in range(total_batches):
        # Extract batch
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, total_rows)
        batch_df = df.iloc[start_idx:end_idx].copy()
        
        # Process batch
        batch_results = process_batch(batch_df, i+1, total_batches, api_settings, api_profile, max_workers, request_delay)
        all_results.append(batch_results)
        
        # Update overall statistics
        success_in_batch = len(batch_results[batch_results['status'] == 'success'])
        errors_in_batch = len(batch_results) - success_in_batch
        retries_in_batch = batch_results['retries'].sum() if 'retries' in batch_results.columns else 0
        
        overall_success += success_in_batch
        overall_errors += errors_in_batch
        overall_retries += retries_in_batch
        
        # Update overall progress
        overall_progress.progress((end_idx) / total_rows)
        
        st.info(f"Progress: {end_idx}/{total_rows} routes completed ({end_idx/total_rows*100:.1f}%)")
        st.info(f"Overall - Success: {overall_success}, Errors: {overall_errors}, Retries: {overall_retries}")
        
        # Add a small pause between batches
        if i < total_batches - 1:
            time.sleep(2)  # 2-second pause between batches
    
    # Clear overall progress bar
    overall_progress.empty()
    
    # Combine all results
    if all_results:
        try:
            results_df = pd.concat(all_results, ignore_index=True)
            
            # Final statistics
            validation_stats = {
                'total_routes': total_rows,
                'successful_routes': overall_success,
                'failed_routes': overall_errors,
                'success_rate': overall_success / total_rows * 100,
                'total_retries': overall_retries,
                'avg_retries': overall_retries / total_rows
            }
            
            st.success(f"Validation complete - {overall_success} successful, {overall_errors} failed")
            
            return results_df, validation_stats
        except Exception as e:
            st.error(f"Error while combining results: {str(e)}")
            st.warning("Returning the last batch results instead.")
            return all_results[-1] if all_results else None, {}
    else:
        st.error("No results were generated.")
        return None, {}