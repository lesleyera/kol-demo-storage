import streamlit as st
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
import os
from datetime import datetime, timedelta 

# -----------------------------------------------------------------
# 0. 유틸리티 함수 (차트 축 계산)
# -----------------------------------------------------------------
def get_max_value(df, column, is_percentage=False):
    """주어진 컬럼의 최대값보다 10% 더 큰 값을 계산합니다."""
    if df.empty or column not in df.columns:
        return 100 if is_percentage else 10 # 기본값
    
    max_val = df[column].max()
    
    if is_percentage:
        # 백분율은 최대 100%로 고정
        return 100 
    else:
        # 건수/금액은 최대값보다 10% 크게 설정
        return max_val * 1.1 if max_val > 0 else 10

# -----------------------------------------------------------------
# 1. Google Sheets 인증 및 데이터 로드 (공용 함수)
# -----------------------------------------------------------------

@st.cache_data(ttl=60) 
def load_data_from_gsheet():
    """모든 페이지에서 공유할 데이터 로드 함수"""
    
    SPREADSHEET_NAME = "KOL 관리 시트" 
    WORKSHEET1_NAME = "KOL_Master"
    WORKSHEET2_NAME = "Activities"
    
    try:
        # --- 인증 로직 ---
        gc = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, 'google_credentials.json')
        
        if os.path.exists(creds_path):
            gc = gspread.service_account(filename=creds_path)
        elif 'gcp_service_account' in st.secrets:
            creds_dict = st.secrets['gcp_service_account']
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            st.error("인증 실패: 'google_credentials.json' 파일을 찾거나 Streamlit 'Secrets' 설정을 확인하세요.")
            return None, None

        # --- 데이터 로드 ---
        sh = gc.open(SPREADSHEET_NAME)
        master_df = get_as_dataframe(sh.worksheet(WORKSHEET1_NAME)).dropna(how='all') 
        activities_df = get_as_dataframe(sh.worksheet(WORKSHEET2_NAME)).dropna(how='all')
        
        # --- 데이터 타입 변환 및 계산 ---
        master_df['Contract_End'] = pd.to_datetime(master_df['Contract_End'], errors='coerce')
        activities_df['Due_Date'] = pd.to_datetime(activities_df['Due_Date'], errors='coerce')
        master_df['Budget (USD)'] = pd.to_numeric(master_df['Budget (USD)'], errors='coerce').fillna(0)
        master_df['Spent (USD)'] = pd.to_numeric(master_df['Spent (USD)'], errors='coerce').fillna(0)
        
        activities_df['Done'] = activities_df['Status'].apply(lambda x: 1 if x == 'Done' else 0)
        activity_summary = activities_df.groupby('Kol_ID').agg(Total=('Activity_ID', 'count'), Done=('Done', 'sum')).reset_index()
        activity_summary['Completion_Rate'] = (activity_summary['Done'] / activity_summary['Total']) * 100
        master_df = pd.merge(master_df, activity_summary[['Kol_ID', 'Completion_Rate']], on='Kol_ID', how='left').fillna({'Completion_Rate': 0})
        master_df['Utilization_Rate'] = (master_df['Spent (USD)'] / master_df['Budget (USD)']) * 100
        master_df['Utilization_Rate'] = master_df['Utilization_Rate'].fillna(0).apply(lambda x: min(x, 100))
        
        activities_df['YearMonth'] = activities_df['Due_Date'].dt.to_period('M').astype(str)

        st.success("🎉 데이터 로드 및 초기 계산 완료!")
        return master_df, activities_df

    except Exception as e:
        st.error(f"데이터 로드 중 에러 발생: {e}")
        return None, None

# -----------------------------------------------------------------
# 2. 조건부 서식 함수 정의 (공용 함수)
# -----------------------------------------------------------------

def highlight_master_row(row, today, alert_days=30):
    """KOL_Master 테이블에서 계약 만료 임박 행을 강조합니다."""
    contract_end = row['Contract_End']
    is_imminent = False
    if pd.notnull(contract_end):
        is_imminent = (contract_end.date() >= today.date()) and \
                      (contract_end.date() <= (today + timedelta(days=alert_days)).date())
    
    if is_imminent:
        return ['background-color: #ffd70040'] * len(row) 
    return [''] * len(row)

def highlight_activity_row(row, today):
    """Activities 테이블에서 지연된 활동 행을 강조합니다."""
    due_date = row['Due_Date']
    status = row['Status']
    
    is_overdue = False
    if pd.notnull(due_date):
        is_overdue = (due_date.date() < today.date()) and (status != 'Done')
    
    if is_overdue:
        return ['background-color: #ff4c4c40'] * len(row)
    return [''] * len(row)