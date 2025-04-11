import pandas as pd
import time
import random
from datetime import datetime
import streamlit as st
import io

def get_timestamp():
    """Generate a timestamp string for file naming"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def dataframe_to_csv(df):
    """Convert DataFrame to CSV for download"""
    return df.to_csv(index=False).encode('utf-8')

def add_retry_delay(retry_count, base_delay=2, jitter=0.5):
    """Calculate and apply delay for retry with exponential backoff"""
    delay = base_delay ** retry_count
    jitter_value = random.uniform(-jitter, jitter)
    actual_delay = delay + (delay * jitter_value)
    time.sleep(actual_delay)
    return actual_delay

def check_required_columns(df, required_columns):
    """Check if DataFrame has all required columns"""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, missing_columns
    return True, []

def create_batches(df, batch_size):
    """Split DataFrame into batches of specified size"""
    total_rows = len(df)
    return [(i, min(i + batch_size, total_rows)) for i in range(0, total_rows, batch_size)]

def tqdm_streamlit(iterable, desc="Processing"):
    """A tqdm-like progress indicator for Streamlit"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(iterable)
    
    for i, item in enumerate(iterable):
        yield item
        progress_bar.progress((i + 1) / total)
        status_text.text(f"{desc}: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
    
    progress_bar.empty()
    status_text.text(f"{desc}: Completed!")