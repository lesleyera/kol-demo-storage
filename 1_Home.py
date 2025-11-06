import streamlit as st
import pandas as pd
from datetime import datetime, timedelta 
from utils import load_data_from_csv # 💡 공용 함수 임포트

# -----------------------------------------------------------------
# 1. 페이지 설정 및 데이터 로드
# -----------------------------------------------------------------
st.set_page_config(page_title="KOL 대시보드 (Home)", layout="wide")
st.title("📊 KOL 활동 관리 대시보드 (MVP)")

master_df, activities_df = load_data_from_csv() # 💡 함수 이름 변경

# -----------------------------------------------------------------
# 2. 사이드바 (모든 페이지 공통)
# -----------------------------------------------------------------
st.sidebar.subheader("KOL 상세 조회 필터")
if master_df is not None:
    kol_names = master_df['Name'].tolist()
    # 'selected_kol'이라는 세션 상태(st.session_state)를 사용해 선택을 기억
    if 'selected_kol' not in st.session_state:
        st.session_state.selected_kol = "전체"

    selected_name = st.sidebar.selectbox(
        "KOL 이름을 선택하세요:", 
        ["전체"] + kol_names, 
        key='selected_kol' # 세션 상태와 연결
    )
else:
    selected_name = st.sidebar.selectbox("KOL 이름을 선택하세요:", ["전체"])

# -----------------------------------------------------------------
# 3. 메인 화면 UI
# -----------------------------------------------------------------
if master_df is not None and activities_df is not None:

    if selected_name == "전체":
        
        # ===================================
        # 1. KPI 요약
        # ===================================
        st.header("1. KPI 요약")
        
        total_budget = master_df['Budget (USD)'].sum()
        total_spent = master_df['Spent (USD)'].sum()
        avg_completion = master_df['Completion_Rate'].mean()
        avg_utilization = (total_spent / total_budget) * 100 if total_budget > 0 else 0
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1: st.metric(label="총 KOL 인원", value=master_df.shape[0])
        with col_kpi2: st.metric(label="총 예산 규모", value=f"${total_budget:,.0f}")
        with col_kpi3: st.metric(label="평균 완료율", value=f"{avg_completion:.1f}%")
        with col_kpi4: st.metric(label="예산 활용률", value=f"{avg_utilization:.1f}%")
        
        st.divider()

        # ===================================
        # 2. 경고 및 알림 (Alerts)
        # ===================================
        st.header("2. 경고 및 알림 (Alerts)")
        
        today = datetime.now()
        alert_found = False

        contract_alert_date = today + timedelta(days=30)
        imminent_contracts = master_df[
            (master_df['Contract_End'] <= contract_alert_date) &
            (master_df['Contract_End'] >= today)
        ].copy()
        
        with st.expander(f"🚨 계약 만료 임박 ({imminent_contracts.shape[0]} 건) - 30일 이내", expanded=False):
            if not imminent_contracts.empty:
                alert_found = True
                imminent_contracts['D-Day'] = (imminent_contracts['Contract_End'] - today).dt.days
                st.dataframe(imminent_contracts[['Name', 'Country', 'Contract_End', 'D-Day']].astype(str), use_container_width=True)
            else:
                st.info("해당 없음")

        overdue_activities = activities_df[
            (activities_df['Due_Date'] < today) &
            (activities_df['Status'] != 'Done')
        ].copy()

        with st.expander(f"🔥 활동 지연 ({overdue_activities.shape[0]} 건)", expanded=True): 
            if not overdue_activities.empty:
                alert_found = True
                overdue_activities = pd.merge(overdue_activities, master_df[['Kol_ID', 'Name']], on='Kol_ID', how='left')
                overdue_activities['Overdue (Days)'] = (today - overdue_activities['Due_Date']).dt.days
                st.error("아래 활동들이 지연되고 있습니다. Follow-up이 필요합니다.")
                st.dataframe(overdue_activities[['Name', 'Activity_Type', 'Due_Date', 'Status', 'Overdue (Days)']].astype(str), use_container_width=True)
            else:
                st.info("해당 없음")
        
        if not alert_found: st.success("🎉 모든 일정이 정상입니다!")
        st.divider()
        
        st.info("👈 사이드바에서 '📈 Charts Dashboard' 또는 '🗃️ Raw Data' 페이지를 선택하여 더 많은 정보를 확인하세요.")


    # --- (KOL 상세 뷰 - 홈에서는 간략히 표시) ---
    else:
        st.header(f"👨‍⚕️ {selected_name} 님 요약")
        st.info("상세 차트 및 원본 데이터는 왼쪽 메뉴의 각 페이지에서 확인하세요.")
        
        try:
            selected_kol_id = master_df[master_df['Name'] == selected_name]['Kol_ID'].iloc[0]
            
            st.subheader("상세 정보")
            kol_details = master_df[master_df['Kol_ID'] == selected_kol_id]
            st.dataframe(kol_details.astype(str), use_container_width=True) 
            
            st.subheader("활동 내역 요약")
            kol_activities = activities_df[activities_df['Kol_ID'] == selected_kol_id]
            
            if not kol_activities.empty:
                total = kol_activities.shape[0]
                done = kol_activities[kol_activities['Status'] == 'Done'].shape[0]
                completion_rate = (done / total) * 100 if total > 0 else 0
                
                kol_budget = kol_details['Budget (USD)'].iloc[0]
                kol_spent = kol_details['Spent (USD)'].iloc[0]
                kol_utilization = (kol_spent / kol_budget) * 100 if kol_budget > 0 else 0

                c1, c2, c3, c4 = st.columns(4)
                c1.metric(label="배정된 총 활동 수", value=total)
                c2.metric(label="활동 완료율", value=f"{completion_rate:.1f}%")
                c3.metric(label="배정된 예산", value=f"${kol_budget:,.0f}")
                c4.metric(label="예산 활용률", value=f"{kol_utilization:.1f}%")
            else:
                st.warning("이 KOL에 배정된 활동 내역이 없습니다.")
                
        except Exception as e:
            st.error(f"데이터 표시 중 에러: {e}")

else:
    st.error("데이터를 불러오는 데 실패했습니다. CSV 파일이 GitHub에 올바르게 업로드되었는지 확인하세요.")