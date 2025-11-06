import streamlit as st
import pandas as pd
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
# 1. 💡 CSV 파일에서 데이터 로드 (gspread 제거됨)
# -----------------------------------------------------------------

@st.cache_data(ttl=60) 
def load_data_from_csv():
    """모든 페이지에서 공유할 데이터 로드 함수"""
    
    # 💡 파일 이름은 우리가 1단계에서 바꾼 이름
    MASTER_FILE = "contracts.csv"
    ACTIVITIES_FILE = "activities.csv"
    
    try:
        # --- 데이터 로드 ---
        master_df = pd.read_csv(MASTER_FILE, dtype=str).dropna(how='all') 
        activities_df = pd.read_csv(ACTIVITIES_FILE, dtype=str).dropna(how='all')
        
        # --- 💡 CSV 컬럼 이름 매핑 (사장님 파일 기준) ---
        # Google Sheets 열 이름 -> CSV 열 이름
        master_df = master_df.rename(columns={
            "Contract": "Kol_ID",
            "KOL Type": "KOL_Type",
            "KOL Name": "Name",
            "Country": "Country",
            "Contract Start Date": "Contract_Start",
            "Contract End Date": "Contract_End",
            "Contract Value (USD)": "Budget (USD)",
            # "Spent (USD)"는 CSV에 없어서 0으로 채웁니다. (필요시 추가)
        })
        
        activities_df = activities_df.rename(columns={
            "Activity ID": "Activity_ID",
            "Contract": "Kol_ID",
            "Activity Type": "Activity_Type",
            "Planned Date": "Due_Date",
            "Status": "Status",
            "File Link": "File_Link"
        })

        # --- 데이터 타입 변환 및 계산 ---
        master_df['Contract_End'] = pd.to_datetime(master_df['Contract_End'], errors='coerce')
        activities_df['Due_Date'] = pd.to_datetime(activities_df['Due_Date'], errors='coerce')
        master_df['Budget (USD)'] = pd.to_numeric(master_df['Budget (USD)'], errors='coerce').fillna(0)
        
        # 💡 CSV에 'Spent (USD)'가 없으므로 0으로 생성
        if 'Spent (USD)' not in master_df.columns:
            master_df['Spent (USD)'] = 0 
        else:
            master_df['Spent (USD)'] = pd.to_numeric(master_df['Spent (USD)'], errors='coerce').fillna(0)

        
        activities_df['Done'] = activities_df['Status'].apply(lambda x: 1 if x == 'Done' else 0)
        activity_summary = activities_df.groupby('Kol_ID').agg(Total=('Activity_ID', 'count'), Done=('Done', 'sum')).reset_index()
        activity_summary['Completion_Rate'] = (activity_summary['Done'] / activity_summary['Total']) * 100
        master_df = pd.merge(master_df, activity_summary[['Kol_ID', 'Completion_Rate']], on='Kol_ID', how='left').fillna({'Completion_Rate': 0})
        master_df['Utilization_Rate'] = (master_df['Spent (USD)'] / master_df['Budget (USD)']) * 100
        master_df['Utilization_Rate'] = master_df['Utilization_Rate'].fillna(0).apply(lambda x: min(x, 100))
        
        activities_df['YearMonth'] = activities_df['Due_Date'].dt.to_period('M').astype(str)

        st.success("🎉 CSV 데이터 로드 및 초기 계산 완료!")
        return master_df, activities_df

    except FileNotFoundError as e:
        st.error(f"데이터 파일 찾기 실패: {e.filename} 파일이 GitHub 저장소에 없습니다.")
        st.error("1단계에서 파일 이름을 'contracts.csv'와 'activities.csv'로 변경했는지 확인하세요.")
        return None, None
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