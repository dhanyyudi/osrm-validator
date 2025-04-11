import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import folium
from streamlit_folium import folium_static

def get_validation_statistics(results_df, threshold=50):
    """
    Calculate statistics from validation results
    
    Args:
        results_df (pandas.DataFrame): DataFrame with validation results
        threshold (float): Distance threshold for problematic routes (meters)
        
    Returns:
        dict: Statistics about the validation results
        pandas.DataFrame: DataFrame with problematic routes
    """
    # Basic stats
    total_rows = len(results_df)
    success_count = results_df[results_df['status'] == 'success'].shape[0]
    error_count = total_rows - success_count
    
    # Initialize statistics dictionary
    stats = {
        'total_rows': total_rows,
        'success_count': success_count,
        'error_count': error_count,
        'success_rate': success_count / total_rows * 100 if total_rows > 0 else 0
    }
    
    # Only analyze successful routes
    if success_count > 0:
        # Distance analysis
        distance_data = results_df[results_df['status'] == 'success']['distance_to_dest']
        
        stats.update({
            'mean_distance': distance_data.mean(),
            'median_distance': distance_data.median(),
            'min_distance': distance_data.min(),
            'max_distance': distance_data.max(),
            'std_distance': distance_data.std()
        })
        
        # Identify problematic routes
        problematic = results_df[(results_df['status'] == 'success') & 
                                 (results_df['distance_to_dest'] > threshold)]
        
        stats.update({
            'problematic_count': len(problematic),
            'problematic_rate': len(problematic) / success_count * 100 if success_count > 0 else 0
        })
        
        # Calculate distance distribution
        distance_bins = [0, 10, 20, 50, 100, 200, 500, float('inf')]
        bin_labels = ['0-10m', '10-20m', '20-50m', '50-100m', '100-200m', '200-500m', '500m+']
        
        distance_dist = []
        for i in range(len(distance_bins)-1):
            lower = distance_bins[i]
            upper = distance_bins[i+1]
            count = len(results_df[(results_df['status'] == 'success') & 
                                   (results_df['distance_to_dest'] >= lower) & 
                                   (results_df['distance_to_dest'] < upper)])
            distance_dist.append({
                'range': bin_labels[i],
                'count': count,
                'percentage': count / success_count * 100 if success_count > 0 else 0
            })
        
        stats['distance_distribution'] = distance_dist
        
        # Retry analysis
        if 'retries' in results_df.columns:
            retry_stats = {
                'total_retries': results_df['retries'].sum(),
                'avg_retries': results_df['retries'].mean(),
                'max_retries': results_df['retries'].max(),
                'routes_with_retries': (results_df['retries'] > 0).sum(),
                'retry_rate': (results_df['retries'] > 0).sum() / total_rows * 100 if total_rows > 0 else 0
            }
            stats.update(retry_stats)
        
        return stats, problematic
    else:
        return stats, pd.DataFrame()

def create_distance_histogram(results_df, threshold=50):
    """
    Create a histogram of distances between route endpoints and destinations
    
    Args:
        results_df (pandas.DataFrame): DataFrame with validation results
        threshold (float): Distance threshold for problematic routes (meters)
        
    Returns:
        matplotlib.figure.Figure: The histogram figure
    """
    # Filter for successful routes
    successful = results_df[results_df['status'] == 'success']
    
    if len(successful) == 0:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create histogram
    sns.histplot(successful['distance_to_dest'], bins=30, kde=True, ax=ax)
    
    # Add vertical line at threshold
    plt.axvline(x=threshold, color='r', linestyle='--', 
                label=f'Threshold ({threshold}m)')
    
    # Add styling
    plt.title('Distribution of Distances Between Route Endpoints and Destinations', fontsize=14)
    plt.xlabel('Distance (meters)', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.legend()
    plt.grid(alpha=0.3)
    
    return fig

def create_distance_pie_chart(results_df, threshold=50):
    """
    Create a pie chart of distance categories
    
    Args:
        results_df (pandas.DataFrame): DataFrame with validation results
        threshold (float): Distance threshold for problematic routes (meters)
        
    Returns:
        matplotlib.figure.Figure: The pie chart figure
    """
    # Filter for successful routes
    successful = results_df[results_df['status'] == 'success']
    
    if len(successful) == 0:
        return None
    
    # Create distance categories
    bins = [0, threshold, threshold*2, threshold*4, float('inf')]
    labels = [f'<{threshold}m', f'{threshold}-{threshold*2}m', 
              f'{threshold*2}-{threshold*4}m', f'>{threshold*4}m']
    
    # Count routes in each category
    counts = []
    for i in range(len(bins)-1):
        count = len(successful[(successful['distance_to_dest'] >= bins[i]) & 
                               (successful['distance_to_dest'] < bins[i+1])])
        counts.append(count)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Create pie chart only if we have data
    if sum(counts) > 0:
        # Define colors based on severity (green to red)
        colors = ['#3CB371', '#FFD700', '#FF8C00', '#DC143C']
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Equal aspect ratio ensures the pie chart is circular
        ax.axis('equal')
        
        # Styling
        plt.title('Distance Categories', fontsize=14)
        plt.setp(autotexts, size=10, weight="bold")
    else:
        plt.text(0.5, 0.5, 'No successful routes available', 
                 horizontalalignment='center', fontsize=12)
    
    return fig

def create_error_bar_chart(results_df):
    """
    Create a bar chart of error types
    
    Args:
        results_df (pandas.DataFrame): DataFrame with validation results
        
    Returns:
        matplotlib.figure.Figure: The bar chart figure
    """
    # Filter for error routes
    errors = results_df[results_df['status'] != 'success']
    
    if len(errors) == 0:
        return None
    
    # Count errors by type
    error_counts = errors['status'].value_counts()
    
    # Truncate long error messages for display
    error_counts.index = [str(err)[:50] + '...' if len(str(err)) > 50 else str(err) 
                          for err in error_counts.index]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar chart
    error_counts.plot(kind='barh', ax=ax)
    
    # Add styling
    plt.title('Error Types', fontsize=14)
    plt.xlabel('Count', fontsize=12)
    plt.ylabel('Error Type', fontsize=12)
    plt.grid(alpha=0.3)
    
    return fig

def create_interactive_map(problematic_df, map_center=None, threshold=50):
    """
    Create an interactive map showing problematic routes
    
    Args:
        problematic_df (pandas.DataFrame): DataFrame with problematic routes
        map_center (list): [lat, lon] center of the map
        threshold (float): Distance threshold for color coding
        
    Returns:
        folium.Map: Interactive map
    """
    if len(problematic_df) == 0:
        return None
    
    # Determine map center if not provided
    if map_center is None:
        center_lat = problematic_df['dest_lat'].mean()
        center_lon = problematic_df['dest_lon'].mean()
    else:
        center_lat, center_lon = map_center
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Define a color function based on distance
    def get_color(distance, threshold):
        if distance < threshold * 2:
            return 'green'
        elif distance < threshold * 4:
            return 'orange'
        else:
            return 'red'
    
    # Add markers and lines for each problematic route
    for _, route in problematic_df.iterrows():
        # Only include if both endpoint and destination have coordinates
        if (pd.notna(route['last_route_lat']) and pd.notna(route['last_route_lon']) and
            pd.notna(route['dest_lat']) and pd.notna(route['dest_lon'])):
            
            # Calculate distance
            distance = route['distance_to_dest']
            
            # Line color based on distance
            color = get_color(distance, threshold)
            
            # Line weight based on distance (thicker = more problematic)
            weight = min(5, 1 + (distance / threshold))
            
            # Add a line between last route point and destination
            folium.PolyLine(
                locations=[
                    [route['last_route_lat'], route['last_route_lon']],
                    [route['dest_lat'], route['dest_lon']]
                ],
                color=color,
                weight=weight,
                opacity=0.7,
                tooltip=f"Distance: {distance:.1f}m"
            ).add_to(m)
            
            # Add marker for destination
            folium.CircleMarker(
                location=[route['dest_lat'], route['dest_lon']],
                radius=5,
                color='blue',
                fill=True,
                fill_color='blue',
                tooltip=f"Destination {route.get('store_location', '')} ({route.get('store_number', '')})"
            ).add_to(m)
            
            # Add marker for last route point
            folium.CircleMarker(
                location=[route['last_route_lat'], route['last_route_lon']],
                radius=5,
                color='red',
                fill=True,
                fill_color='red',
                tooltip=f"Route Endpoint (distance: {distance:.1f}m)"
            ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
        bottom: 50px; left: 50px; width: 180px; height: 120px; 
        border:2px solid grey; z-index:9999; font-size:14px;
        background-color:white; padding: 10px;
        border-radius: 5px;">
        <p style="margin-bottom: 5px;">Distance:</p>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 5px; background-color: green; margin-right: 10px;"></div>
            < {0}m
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 5px; background-color: orange; margin-right: 10px;"></div>
            {0}m - {1}m
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 5px; background-color: red; margin-right: 10px;"></div>
            > {1}m
        </div>
    </div>
    '''.format(threshold * 2, threshold * 4)
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m