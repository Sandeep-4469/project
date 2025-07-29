import streamlit as st
import pandas as pd
import os
import plotly.express as px

from src.data_loader import load_emr_data
from src.mhabi_algorithm import calculate_mhabi

st.set_page_config(page_title="Add & Assess Patient", page_icon="➕")

DATA_FILE_PATH = 'data/sample_emr_data.csv'

if 'new_patient_report' not in st.session_state:
    st.session_state.new_patient_report = None

def reset_form():
    """Resets the session state to show the form again."""
    st.session_state.new_patient_report = None

st.title("➕ Add & Assess New Patient")

if st.session_state.new_patient_report:
    report = st.session_state.new_patient_report
    patient_id = report['raw_data_with_risk']['patient_id']
    
    st.header(f"Patient Report: {patient_id}")
    st.success("Patient record has been calculated and saved to the dataset.")
    
    # Display metrics
    c1, c2, c3 = st.columns(3)
    c1.metric(label="Calculated MHABI Score", value=f"{report['mhabi_score']:.2f}")
    c2.metric(label="Algorithmic Suicide Risk Score", value=f"{report['raw_data_with_risk']['suicide_risk_score']}/10")
    c3.metric(label="Risk Amplified?", value="✔️ Yes" if report['risk_amplified'] else "❌ No")

    # Display diagnostic sub-scores
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

else:
    st.markdown("Use this form to enter a patient's details. The **Risk Score** will be calculated automatically based on the inputs provided.")

    existing_data = load_emr_data(DATA_FILE_PATH)
    
    with st.form(key="new_patient_form"):
        st.subheader("Enter Patient Details")
        c1, c2 = st.columns(2)
        with c1:
            if not existing_data.empty:
                last_id = existing_data['patient_id'].str.extract(r'(\d+)').astype(int).max().values[0]
                suggested_id = f"P{last_id + 1:03d}"
            else:
                suggested_id = "P001"
            patient_id = st.text_input("Patient ID", value=suggested_id)
            region = st.selectbox("Region", options=sorted(existing_data['region'].unique()) if not existing_data.empty else ["North", "South", "East", "West"])
            age_group = st.selectbox("Age Group", options=sorted(existing_data['age_group'].unique()) if not existing_data.empty else ["18-24", "25-34", "35-44", "45-54", "55+"])
            gender = st.selectbox("Gender", options=sorted(existing_data['gender'].unique()) if not existing_data.empty else ["Female", "Male", "Non-binary"])

        with c2:
            wait_time_days = st.number_input("Wait Time (days)", min_value=0, step=1, help="Number of days patient has been on a waitlist.")
            dalys = st.number_input("DALYs Score", min_value=0.0, format="%.2f", step=0.01, help="Disability-Adjusted Life Years score, if available.")
            er_visits_last_year = st.number_input("ER Visits (last year)", min_value=0, step=1, help="Number of mental health-related ER visits in the past 12 months.")
            missed_work_school_days = st.number_input("Missed Work/School (days)", min_value=0, step=1, help="Days of work or school missed due to mental health in the past 3 months.")

        submitted = st.form_submit_button("Calculate & View Patient Report")

        if submitted:
            if not existing_data.empty and patient_id in existing_data['patient_id'].values:
                st.error(f"Patient ID '{patient_id}' already exists. Please use a unique ID.")
            else:
                new_patient_input = {
                    'patient_id': patient_id, 'region': region, 'age_group': age_group, 'gender': gender,
                    'wait_time_days': wait_time_days, 'dalys': dalys, 'er_visits_last_year': er_visits_last_year,
                    'missed_work_school_days': missed_work_school_days
                }
                
                mhabi_result = calculate_mhabi(new_patient_input)
                try:
                    df_to_save = pd.DataFrame([mhabi_result['raw_data_with_risk']])
                    df_to_save.to_csv(DATA_FILE_PATH, mode='a', header=not os.path.exists(DATA_FILE_PATH) or os.path.getsize(DATA_FILE_PATH) == 0, index=False)
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed to write to CSV file: {e}")
                    st.stop()
                
                st.session_state.new_patient_report = mhabi_result
                st.rerun()

