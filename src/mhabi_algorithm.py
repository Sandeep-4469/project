import pandas as pd

# --- New function to calculate a proxy suicide risk score ---
def _calculate_proxy_suicide_risk(raw_data):
    """
    Calculates a proxy suicide risk score (1-10) based on other clinical indicators.
    This replaces manual user input for the risk score.
    """
    proxy_score = 1  # Start with a baseline score
    
    # Add points based on high-severity indicators
    if raw_data['er_visits_last_year'] >= 2:
        proxy_score += 3
    elif raw_data['er_visits_last_year'] == 1:
        proxy_score += 1

    if raw_data['missed_work_school_days'] >= 20:
        proxy_score += 2
    elif raw_data['missed_work_school_days'] >= 10:
        proxy_score += 1
        
    if raw_data['dalys'] >= 0.3:
        proxy_score += 2
    elif raw_data['dalys'] >= 0.2:
        proxy_score += 1

    # Ensure the score is capped between 1 and 10
    return min(proxy_score, 10)

# --- Normalization Tiered Thresholds (Unchanged) ---
def _normalize_wait_time(days):
    if days <= 7: return 10
    if days <= 30: return 40
    if days <= 90: return 70
    return 100

def _normalize_dalys(daly_score):
    if daly_score < 0.1: return 10
    if daly_score < 0.2: return 40
    if daly_score < 0.3: return 70
    return 100

def _normalize_er_visits(visits):
    if visits == 0: return 0
    if visits == 1: return 40
    if visits == 2: return 70
    return 100

def _normalize_missed_work(days):
    if days <= 5: return 10
    if days <= 10: return 40
    if days <= 20: return 70
    return 100

def _normalize_suicide_risk(risk_score):
    if risk_score <= 3: return 10
    if risk_score <= 6: return 50
    if risk_score <= 8: return 80
    return 100

def calculate_mhabi(patient_data_row):
    """
    Calculates the MHABI score for a single patient.
    Now includes automatic calculation of the suicide risk score.
    """
    # --- Create a mutable copy ---
    raw_data = dict(patient_data_row)
    
    # --- Step 0: Calculate Proxy Suicide Risk ---
    # This is the key change: the risk score is now generated here.
    raw_data['suicide_risk_score'] = _calculate_proxy_suicide_risk(raw_data)

    # --- Step 1: Normalization ---
    norm_scores = {
        "Wait Time": _normalize_wait_time(raw_data['wait_time_days']),
        "DALYs/YLDs": _normalize_dalys(raw_data['dalys']),
        "ER Utilization": _normalize_er_visits(raw_data['er_visits_last_year']),
        "Missed Work/School": _normalize_missed_work(raw_data['missed_work_school_days']),
        "Suicide Risk": _normalize_suicide_risk(raw_data['suicide_risk_score'])
    }

    # --- Step 2: Weighted Composite Score ---
    weights = {
        "Wait Time": 0.25, "DALYs/YLDs": 0.20, "ER Utilization": 0.20,
        "Missed Work/School": 0.15, "Suicide Risk": 0.20
    }
    subtotal = sum(norm_scores[key] * weights[key] for key in norm_scores)

    # --- Step 3: Risk Amplification Logic ---
    amplified = False
    final_score = subtotal
    if raw_data['suicide_risk_score'] >= 7 and raw_data['er_visits_last_year'] >= 2:
        final_score *= 1.1
        amplified = True
    
    final_score = min(final_score, 100)
    
    return {
        "raw_data_with_risk": raw_data, # Return the full raw data including the new risk score
        "mhabi_score": round(final_score, 2),
        "normalized_scores": norm_scores,
        "risk_amplified": amplified
    }

def process_dataframe(df):
    """Applies the MHABI calculation to an entire DataFrame."""
    if df.empty:
        return df

    # We need to process row by row since the risk score is now dynamic
    results_list = []
    for _, row in df.iterrows():
        result = calculate_mhabi(row)
        # Combine original data with calculated scores for the new row
        processed_row = {**row.to_dict(), **result}
        del processed_row['raw_data_with_risk'] # Avoid redundancy
        results_list.append(processed_row)
        
    return pd.DataFrame(results_list)

