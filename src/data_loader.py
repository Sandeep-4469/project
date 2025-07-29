import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_emr_data(file_path='data/sample_emr_data.csv'):
    """
    Loads EMR data from a specified CSV file path.
    Uses Streamlit's caching to improve performance.

    Args:
        file_path (str): The path to the CSV data file.

    Returns:
        pd.DataFrame: A DataFrame containing the EMR data.
    """
    if not os.path.exists(file_path):
        st.error(f"Data file not found at: {file_path}")
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(file_path)
        # Basic validation
        required_columns = [
            'patient_id', 'region', 'age_group', 'gender', 'wait_time_days',
            'dalys', 'er_visits_last_year', 'missed_work_school_days', 'suicide_risk_score'
        ]
        if not all(col in df.columns for col in required_columns):
            st.error("CSV file is missing one or more required columns.")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()
