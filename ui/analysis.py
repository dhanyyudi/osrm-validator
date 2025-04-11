import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_folium import folium_static
from config.settings import DEFAULT_SETTINGS, SESSION_KEYS
from modules.analysis.analyzer import (
    get_validation_statistics, 
    create_distance_histogram, 
    create_distance_pie_chart, 
    create_error_bar_chart,
    create_interactive_map
)
from utils.helpers import dataframe_to_csv, get_timestamp

def show_analysis():
    """
    Display the analysis UI for validation results
    """
    st.header("Validation Results Analysis")
    
    if SESSION_KEYS["VALIDATION_RESULTS"] in st.session_state:
        # Get results from session state
        results_df = st.session_state[SESSION_KEYS["VALIDATION_RESULTS"]]
        
        # Analysis settings
        st.subheader("Analysis Settings")
        
        threshold = st.slider(
            "Distance Threshold (meters)", 
            min_value=10, 
            max_value=200, 
            value=DEFAULT_SETTINGS["THRESHOLD"],
            help="Minimum distance (in meters) to flag problematic routes"
        )
        
        # Run analysis
        with st.spinner("Analyzing validation results..."):
            # Get statistics and problematic routes
            stats, problematic_routes = get_validation_statistics(results_df, threshold)
            
            # Save problematic routes to session state for later use
            st.session_state[SESSION_KEYS["PROBLEMATIC_ROUTES"]] = problematic_routes
            
            # Display statistics
            st.subheader("Validation Statistics")
            
            # Basic stats in columns
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Total Routes", stats['total_rows'])
            col2.metric("Successful Routes", stats['success_count'])
            col3.metric("Failed Routes", stats['error_count'])
            col4.metric("Success Rate", f"{stats['success_rate']:.1f}%")
            
            if stats['success_count'] > 0:
                # Distance stats
                st.subheader("Distance Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Average Distance", f"{stats['mean_distance']:.2f}m")
                col2.metric("Median Distance", f"{stats['median_distance']:.2f}m")
                col3.metric("Minimum Distance", f"{stats['min_distance']:.2f}m")
                col4.metric("Maximum Distance", f"{stats['max_distance']:.2f}m")
                
                # Problematic routes
                st.subheader("Problematic Routes")
                
                col1, col2 = st.columns(2)
                
                col1.metric(
                    "Problematic Routes Count", 
                    stats['problematic_count'],
                    f"{stats['problematic_rate']:.1f}% of successful routes"
                )
                
                col2.metric(
                    "Distance Threshold", 
                    f"{threshold}m",
                    "Routes with distance > threshold are considered problematic"
                )
                
                # Display charts
                st.subheader("Result Visualizations")
                
                tab1, tab2, tab3, tab4 = st.tabs(["Distance Histogram", "Distance Categories", "Errors", "Map"])
                
                with tab1:
                    # Distance histogram
                    hist_fig = create_distance_histogram(results_df, threshold)
                    if hist_fig:
                        st.pyplot(hist_fig)
                    else:
                        st.info("No data available for histogram visualization.")
                
                with tab2:
                    # Distance pie chart
                    pie_fig = create_distance_pie_chart(results_df, threshold)
                    if pie_fig:
                        st.pyplot(pie_fig)
                    else:
                        st.info("No data available for pie chart visualization.")
                
                with tab3:
                    # Error bar chart
                    if stats['error_count'] > 0:
                        error_fig = create_error_bar_chart(results_df)
                        if error_fig:
                            st.pyplot(error_fig)
                        else:
                            st.info("No error data available for visualization.")
                    else:
                        st.info("No errors to visualize.")
                
                with tab4:
                    # Interactive map of problematic routes
                    if len(problematic_routes) > 0:
                        st.write(f"Displaying {len(problematic_routes)} problematic routes on map")
                        
                        # Create interactive map
                        folium_map = create_interactive_map(problematic_routes, threshold=threshold)
                        if folium_map:
                            folium_static(folium_map)
                        else:
                            st.info("Unable to create interactive map.")
                    else:
                        st.info("No problematic routes to display on map.")
                
                # Distance distribution table
                if 'distance_distribution' in stats:
                    st.subheader("Distance Distribution")
                    
                    # Create table
                    dist_data = pd.DataFrame(stats['distance_distribution'])
                    
                    # Display as table
                    st.table(dist_data)
                
                # Download problematic routes button
                if len(problematic_routes) > 0:
                    st.subheader("Download Problematic Routes")
                    
                    st.download_button(
                        "Download Problematic Routes",
                        dataframe_to_csv(problematic_routes),
                        f"problematic_routes_{threshold}m_{get_timestamp()}.csv",
                        "text/csv",
                        key='download-problematic-routes'
                    )
                
                # Problematic routes preview
                if len(problematic_routes) > 0:
                    st.subheader("Problematic Routes Preview")
                    
                    # Add sort options
                    sort_by = st.selectbox(
                        "Sort by",
                        ["distance_to_dest", "store_location", "dc_location"],
                        index=0
                    )
                    
                    # Sort and display
                    sorted_problematic = problematic_routes.sort_values(
                        by=sort_by, 
                        ascending=(sort_by != "distance_to_dest")
                    )
                    
                    st.dataframe(sorted_problematic)
                else:
                    st.info("No problematic routes found with current threshold.")
            
            else:
                st.warning("No successful routes to analyze.")
    else:
        st.warning("No validation results available. Please run validation first in the 'OSRM Validation' tab.")