import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_data_from_gsheet, highlight_master_row, highlight_activity_row # 💡 공용 함수 임포트

st.set_page_config(page_title="원본 데이터", layout="wide")
st.title("🗃️ 4. 원본 데이터 (Raw Data)")

master_df, activities_df = load_data_from_gsheet()

# -----------------------------------------------------------------
# 1. 원본 데이터 UI
# -----------------------------------------------------------------
if master_df is not None and activities_df is not None:

    # st.session_state.selected_kol은 1_Home.py의 사이드바에서 설정됨
    selected_name = st.session_state.get('selected_kol', "전체")
    
    today = datetime.now() 

    st.subheader("KOL 마스터")
    if selected_name == "전체":
        st.dataframe(
            master_df.style.apply(highlight_master_row, today=today, axis=1).format({'Contract_End': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ''}),
            use_container_width=True
        ) 
    else:
        # 선택된 KOL만 필터링
        selected_kol_df = master_df[master_df['Name'] == selected_name]
        st.dataframe(
            selected_kol_df.style.apply(highlight_master_row, today=today, axis=1).format({'Contract_End': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ''}),
            use_container_width=True
        )

    st.divider()

    st.subheader("모든 활동 내역")
    if selected_name == "전체":
        st.dataframe(
            activities_df.style.apply(highlight_activity_row, today=today, axis=1).format({'Due_Date': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ''}),
            use_container_width=True
        )
    else:
        # 선택된 KOL만 필터링
        selected_kol_id = master_df[master_df['Name'] == selected_name]['Kol_ID'].iloc[0]
        selected_activities_df = activities_df[activities_df['Kol_ID'] == selected_kol_id]
        st.dataframe(
            selected_activities_df.style.apply(highlight_activity_row, today=today, axis=1).format({'Due_Date': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ''}),
            column_config={
                "File_Link": None, 
                "자료 열람": st.column_config.LinkColumn(
                    "자료 열람 (링크)",
                    display_text="🔗 링크 열기"
                )
            },
            use_container_width=True,
            hide_index=True
        )
        
else:
    st.error("데이터를 불러오는 데 실패했습니다. '1_Home' 페이지에서 연결을 확인하세요.")