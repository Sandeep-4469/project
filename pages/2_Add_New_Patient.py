import streamlit as st
import pandas as pd
import os
import plotly.express as px

from src.data_loader import load_emr_data
from src.mhabi_algorithm import calculate_mhabi

# --- Page Configuration ---
st.set_page_config(page_title="Add & Assess Patient", page_icon="➕")

# --- Constants ---
DATA_FILE_PATH = 'data/sample_emr_data.csv'

# Initialize session state to hold the single patient report
if 'new_patient_report' not in st.session_state:
    st.session_state.new_patient_report = None

def reset_form():
    """Resets the session state to show the form again."""
    st.session_state.new_patient_report = None

# --- Main Page Logic ---
st.title("➕ Add & Assess New Patient")

# --- STATE 2: Display the Patient Report ---
if st.session_state.new_patient_report:
    report = st.session_state.new_patient_report
    patient_id = report['patient_id']
    
    st.header(f"Patient Report: {patient_id}")
    st.success("Patient record has been calculated and saved to the dataset.")
    
    c1, c2, c3 = st.columns(3)
    c1.metric(label="Calculated MHABI Score", value=f"{report['mhabi_score']:.2f}")
    c2.metric(label="User-Input Suicide Risk Score", value=f"{report['suicide_risk_score']}/10")
    c3.metric(label="Risk Amplified?", value="✔️ Yes" if report['risk_amplified'] else "❌ No")

    st.subheader("Diagnostic Sub-Score Breakdown")
    norm_scores = report['normalized_scores']
    df_scores = pd.DataFrame(list(norm_scores.items()), columns=['Factor', 'Normalized Score'])
    fig_sub_scores = px.bar(
        df_scores, x='Normalized Score', y='Factor', orientation='h',
        title=f"Contributing Factors for {patient_id}",
        color='Normalized Score', color_continuous_scale=px.colors.sequential.Reds
    )
    fig_sub_scores.update_layout(xaxis_title="Normalized Score (0-100)", yaxis_title="Component")
    st.plotly_chart(fig_sub_scores, use_container_width=True)

    st.button("Add Another Patient", on_click=reset_form)

# --- STATE 1: Display the Input Form ---
else:
    st.markdown("Use this form to enter a patient's details and a clinically assessed suicide risk score.")
    
    existing_data = load_emr_data(DATA_FILE_PATH)
    
    with st.form(key="new_patient_form"):
        st.subheader("Enter Patient Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            if not existing_data.empty:
                last_id = existing_data['patient_id'].str.extract(r'(\d+)').astype(int).max().values[0]
                suggested_id = f"P{last_id + 1:03d}"
            else:
                suggested_id = "P001"
            patient_id = st.text_input("Patient ID", value=suggested_id)
            region = st.selectbox("Region", options=["North", "South", "East", "West"])
            
        with c2:
            age_group = st.selectbox("Age Group", options=["18-24", "25-34", "35-44", "45-54", "55+"])
            gender = st.selectbox("Gender", options=["Female", "Male", "Non-binary"])
            
        with c3:
            wait_time_days = st.number_input("Wait Time (days)", min_value=0, step=1)
            dalys = st.number_input("DALYs Score", min_value=0.0, format="%.2f", step=0.01)
            
        st.divider()
        c4, c5 = st.columns(2)
        with c4:
            er_visits_last_year = st.number_input("ER Visits (last year)", min_value=0, step=1)
            missed_work_school_days = st.number_input("Missed Work/School (days)", min_value=0, step=1)
        with c5:
            # Re-introducing the manual suicide risk score slider
            suicide_risk_score = st.slider("Clinician Assessed Suicide Risk Score", min_value=1, max_value=10, value=5, step=1)

        submitted = st.form_submit_button("Calculate & View Patient Report")

        if submitted:
            if not existing_data.empty and patient_id in existing_data['patient_id'].values:
                st.error(f"Patient ID '{patient_id}' already exists. Please use a unique ID.")
            else:
                # This dictionary now contains all the raw data needed for calculation and saving
                new_patient_input = {
                    'patient_id': patient_id, 'region': region, 'age_group': age_group, 'gender': gender,
                    'wait_time_days': wait_time_days, 'dalys': dalys, 'er_visits_last_year': er_visits_last_year,
                    'missed_work_school_days': missed_work_school_days,
                    'suicide_risk_score': suicide_risk_score  
                }
                
                mhabi_result = calculate_mhabi(new_patient_input)
                
                try:
                    df_to_save = pd.DataFrame([new_patient_input])
                    df_to_save.to_csv(DATA_FILE_PATH, mode='a', header=not os.path.exists(DATA_FILE_PATH) or os.path.getsize(DATA_FILE_PATH) == 0, index=False)
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed to write to CSV file: {e}")
                    st.stop()
                
                # Combine the raw input with the calculated results for the report
                full_report = {**new_patient_input, **mhabi_result}
                st.session_state.new_patient_report = full_report
                st.rerun()