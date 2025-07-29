import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loader import load_emr_data
from src.mhabi_algorithm import process_dataframe

st.set_page_config(
    page_title="MHABI Dashboard",
    page_icon="",
    layout="wide"
)
def highlight_amplified(row):
    bg_color = '#ffcccc'    
    text_color = 'black'    

    style = f'background-color: {bg_color}; color: {text_color};'
    
    if row.risk_amplified:
        return [style for _ in row]
    else:
        return ['' for _ in row]

st.title("MHABI Dashboard")
st.markdown("""

""")

data = load_emr_data()
if not data.empty:
    processed_data = process_dataframe(data)
else:
    st.warning("Could not load data. Please check the data source.")
    st.stop()


st.sidebar.header("Filter Options")

regions = sorted(processed_data['region'].unique())
selected_regions = st.sidebar.multiselect(
    "Select Region(s)", options=regions, default=regions)

age_groups = sorted(processed_data['age_group'].unique())
selected_age_groups = st.sidebar.multiselect(
    "Select Age Group(s)", options=age_groups, default=age_groups)

genders = sorted(processed_data['gender'].unique())
selected_genders = st.sidebar.multiselect(
    "Select Gender(s)", options=genders, default=genders)

# Apply filters
filtered_df = processed_data[
    (processed_data['region'].isin(selected_regions)) &
    (processed_data['age_group'].isin(selected_age_groups)) &
    (processed_data['gender'].isin(selected_genders))
]

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

st.header("Exploratory Analysis")

plot_options = [
    "Average MHABI Score by Region",
    "MHABI Score Distribution by Age Group",
    "MHABI Score Distribution by Gender",
    "Risk Amplification Breakdown",
    "Correlation of Inputs with MHABI Score"
]
selected_plot = st.selectbox("Choose a visualization to display:", plot_options)

if selected_plot == "Average MHABI Score by Region":
    avg_mhabi_by_region = filtered_df.groupby('region')['mhabi_score'].mean().reset_index()
    fig = px.bar(
        avg_mhabi_by_region, x='region', y='mhabi_score',
        title="Average MHABI Score by Region", color='region',
        labels={'mhabi_score': 'Average MHABI Score', 'region': 'Region'}
    )
    st.plotly_chart(fig, use_container_width=True)

elif selected_plot == "MHABI Score Distribution by Age Group":
    sorted_age = sorted(filtered_df['age_group'].unique())
    fig = px.box(
        filtered_df, x='age_group', y='mhabi_score',
        title="MHABI Score Distribution by Age Group", color='age_group',
        category_orders={"age_group": sorted_age},
        labels={'mhabi_score': 'MHABI Score', 'age_group': 'Age Group'}
    )
    st.plotly_chart(fig, use_container_width=True)

elif selected_plot == "MHABI Score Distribution by Gender":
    fig = px.box(
        filtered_df, x='gender', y='mhabi_score',
        title="MHABI Score Distribution by Gender", color='gender',
        labels={'mhabi_score': 'MHABI Score', 'gender': 'Gender'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
elif selected_plot == "Risk Amplification Breakdown":
    amplified_counts = filtered_df['risk_amplified'].value_counts()
    fig = px.pie(
        values=amplified_counts.values,
        names=amplified_counts.index,
        title="Proportion of Patients with Amplified Risk",
        hole=0.3,
        color_discrete_map={True: 'crimson', False: 'royalblue'}
    )
    st.plotly_chart(fig, use_container_width=True)

elif selected_plot == "Correlation of Inputs with MHABI Score":
    st.markdown("Select a raw input variable to see its correlation with the final MHABI score.")
    correlation_var = st.selectbox(
        "Select an input variable:",
        ['wait_time_days', 'dalys', 'er_visits_last_year', 'missed_work_school_days', 'suicide_risk_score']
    )
    fig = px.scatter(
        filtered_df,
        x=correlation_var,
        y='mhabi_score',
        title=f"MHABI Score vs. {correlation_var.replace('_', ' ').title()}",
        trendline="ols",
        trendline_color_override="red",
        labels={
            'mhabi_score': 'MHABI Score',
            correlation_var: correlation_var.replace('_', ' ').title()
        }
    )
    st.plotly_chart(fig, use_container_width=True)


st.header("Patient-Level Data")
st.markdown("Rows for patients with **amplified risk** are highlighted in red.")

display_cols = ['patient_id', 'region', 'age_group', 'gender', 'mhabi_score', 'risk_amplified']

st.dataframe(
    filtered_df[display_cols].style.apply(highlight_amplified, axis=1),
    use_container_width=True
)

st.header("Diagnostic Sub-Score Drill-Down")
patient_list = filtered_df['patient_id'].tolist()
selected_patient_id = st.selectbox("Select a Patient ID for a detailed view of their score components:", options=patient_list)

if selected_patient_id:
    patient_details = filtered_df[filtered_df['patient_id'] == selected_patient_id].iloc[0]
    
    st.subheader(f"Contributing Factors for Patient {selected_patient_id}")
    
    norm_scores = patient_details['normalized_scores']
    df_scores = pd.DataFrame(list(norm_scores.items()), columns=['Factor', 'Normalized Score'])
    
    fig_sub_scores = px.bar(
        df_scores, x='Normalized Score', y='Factor', orientation='h',
        title=f"Diagnostic Sub-Scores for {selected_patient_id}",
        color='Normalized Score', color_continuous_scale=px.colors.sequential.Reds
    )
    fig_sub_scores.update_layout(xaxis_title="Normalized Score (0-100)", yaxis_title="Component")
    
    st.plotly_chart(fig_sub_scores, use_container_width=True)
    
    if patient_details['risk_amplified']:
        st.warning(f"**Risk Amplified:** This patient's score was increased by 10% due to high suicide risk (Score: {patient_details['suicide_risk_score']}) and ER visits (Count: {patient_details['er_visits_last_year']}).")
    else:
        st.info("Risk was not amplified for this patient.")