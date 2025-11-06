import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta 
from utils import load_data_from_csv, get_max_value # 💡 공용 함수 임포트 이름 변경

st.set_page_config(page_title="차트 대시보드", layout="wide")
st.title("📈 2. 주요 차트 현황")

master_df, activities_df = load_data_from_csv() # 💡 함수 이름 변경

# -----------------------------------------------------------------
# 1. 차트 UI
# -----------------------------------------------------------------
if master_df is not None and activities_df is not None:
    
    # st.session_state.selected_kol은 1_Home.py의 사이드바에서 설정됨
    selected_name = st.session_state.get('selected_kol', "전체")

    if selected_name == "전체":
        
        # --- 축 최대값 계산 ---
        max_count = get_max_value(activities_df.groupby('YearMonth').size().reset_index(name='Count'), 'Count')
        max_budget = get_max_value(master_df.groupby('Country')['Budget (USD)'].sum().reset_index(name='Total_Budget'), 'Total_Budget')
        
        # -----------------------------------
        # Row 1: 차트 3개 (파이차트, 파이차트, 혼합 세로 막대+선)
        # -----------------------------------
        col_r1_c1, col_r1_c2, col_r1_c3 = st.columns(3)

        with col_r1_c1:
            st.subheader("활동 상태별 분포")
            status_counts = activities_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            base = alt.Chart(status_counts).encode(theta=alt.Theta("Count", stack=True), color=alt.Color("Status", title='상태'))
            pie = base.mark_arc(outerRadius=100, innerRadius=60).encode(tooltip=['Status', alt.Tooltip('Count', title='활동 건수', format='d')])
            text_labels = base.mark_text(radius=120, fill='black', fontSize=14).encode( 
                text=alt.Text('Count', format='d'),
                order=alt.Order('Count', sort='descending')
            )
            chart1 = (pie + text_labels).interactive()
            st.altair_chart(chart1, use_container_width=True)
        
        with col_r1_c2:
            st.subheader("KOL 등급별 분포")
            type_counts = master_df['KOL_Type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            
            base = alt.Chart(type_counts).encode(theta=alt.Theta("Count", stack=True), color=alt.Color("Type", title='등급'))
            pie = base.mark_arc(outerRadius=100, innerRadius=60).encode(tooltip=['Type', alt.Tooltip('Count', title='KOL 건수', format='d')])
            text_labels = base.mark_text(radius=120, fill='black', fontSize=14).encode(
                text=alt.Text('Count', format='d'),
                order=alt.Order('Count', sort='descending')
            )
            chart2 = (pie + text_labels).interactive()
            st.altair_chart(chart2, use_container_width=True)
                
        with col_r1_c3:
            st.subheader("월별 총 활동 스케줄")
            timeline_data = activities_df.groupby('YearMonth').size().reset_index(name='Count')
            
            bar_chart = alt.Chart(timeline_data).mark_bar(color='#4c78a8').encode(
                x=alt.X('YearMonth', title='월별 마감일', sort=timeline_data['YearMonth'].tolist()),
                y=alt.Y('Count', title='활동 건수 (건)', axis=alt.Axis(format='d'), scale=alt.Scale(domain=[0, max_count])), 
                tooltip=['YearMonth', alt.Tooltip('Count', title='활동 건수', format='d')]
            )
            text_bar = bar_chart.mark_text(align='center', baseline='bottom', dy=-5, color='black').encode(text=alt.Text('Count', format='d'))
            line_chart = alt.Chart(timeline_data).mark_line(point=True, color='red').encode(
                x=alt.X('YearMonth'), y=alt.Y('Count'), tooltip=['YearMonth', alt.Tooltip('Count', title='활동 건수', format='d')]
            )
            chart3 = (bar_chart + text_bar + line_chart).interactive()
            st.altair_chart(chart3, use_container_width=True)

        st.divider()

        # -----------------------------------
        # Row 2: 차트 3개 (꺾은선, 혼합 차트 분리, 세로 막대)
        # -----------------------------------
        col_r2_c1, col_r2_c2, col_r2_c3 = st.columns(3)

        with col_r2_c1:
            st.subheader("월별 완료 활동 트렌드")
            completed_df = activities_df[activities_df['Status'] == 'Done'].copy()
            completed_timeline = completed_df.groupby('YearMonth').size().reset_index(name='Completed')
            max_completed = get_max_value(completed_timeline, 'Completed')
            line = alt.Chart(completed_timeline).mark_line(point=True, color='green').encode(
                x=alt.X('YearMonth', title='월별 완료 시점', sort=completed_timeline['YearMonth'].tolist()),
                y=alt.Y('Completed', title='완료된 활동 건수 (건)', axis=alt.Axis(format='d'), scale=alt.Scale(domain=[0, max_completed])), 
                tooltip=['YearMonth', alt.Tooltip('Completed', title='완료된 활동 건수', format='d')]
            )
            text_line = line.mark_text(align='left', baseline='middle', dx=5, color='green').encode(text=alt.Text('Completed', format='d'))
            chart4 = (line + text_line).interactive()
            st.altair_chart(chart4, use_container_width=True)

        with col_r2_c2:
            st.subheader("국가별 총 예산 (USD)") 
            country_summary = master_df.groupby('Country').agg(Total_Budget=('Budget (USD)', 'sum')).reset_index()
            max_budget_single = get_max_value(country_summary, 'Total_Budget')
            bar = alt.Chart(country_summary).mark_bar().encode(
                x=alt.X('Total_Budget', title='총 예산 (USD)', axis=alt.Axis(format='$,.0f'), scale=alt.Scale(domain=[0, max_budget_single])), 
                y=alt.Y('Country', title='국가', sort='-x'),
                tooltip=['Country', alt.Tooltip('Total_Budget', title='총 예산', format='$,.0f')]
            )
            text_bar = bar.mark_text(align='left', baseline='middle', dx=5, color='black').encode(text=alt.Text('Total_Budget', format='$,.0f'))
            st.altair_chart(bar + text_bar, use_container_width=True)
        
        with col_r2_c3:
            st.subheader("활동 유형별 분포")
            type_counts = activities_df['Activity_Type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            max_type_count = get_max_value(type_counts, 'Count')
            bar = alt.Chart(type_counts).mark_bar().encode(
                x=alt.X('Type', title='활동 유형'), 
                y=alt.Y('Count', title='활동 건수 (건)', axis=alt.Axis(format='d'), scale=alt.Scale(domain=[0, max_type_count])), 
                tooltip=['Type', alt.Tooltip('Count', title='활동 건수', format='d')]
            )
            text_bar = bar.mark_text(align='center', baseline='bottom', dy=-5, color='black').encode(text=alt.Text('Count', format='d'))
            chart6 = (bar + text_bar).interactive()
            st.altair_chart(chart6, use_container_width=True)

        st.divider()

        # -----------------------------------
        # Row 3: 새로운 차트 - 우수 KOL 순위 (세로 막대, 폭 자동)
        # -----------------------------------
        st.subheader("🏆 우수 KOL별 완료율 순위 (Top 10)")
        
        top_kols = master_df.sort_values(by='Completion_Rate', ascending=False).head(10).reset_index(drop=True)
        max_completion = get_max_value(top_kols, 'Completion_Rate', is_percentage=True)
        
        bar = alt.Chart(top_kols).mark_bar().encode(
            x=alt.X('Name', title='KOL 이름', sort='-y'), 
            y=alt.Y('Completion_Rate', title='활동 완료율 (%)', axis=alt.Axis(format='.1f'), scale=alt.Scale(domain=[0, max_completion])), 
            color=alt.Color('Completion_Rate', title='완료율 (%)', scale=alt.Scale(range='heatmap')),
            tooltip=['Name', alt.Tooltip('Completion_Rate', title='완료율', format='.1f')]
        )
        text_bar = bar.mark_text(align='center', baseline='bottom', dy=-5, color='black').encode(text=alt.Text('Completion_Rate', format='.1f'))
        chart7 = (bar + text_bar).interactive()
        st.altair_chart(chart7, use_container_width=True)

    else:
        # --- (KOL 상세 뷰) ---
        # (이전과 동일)
        st.header(f"👨‍⚕️ {selected_name} 님 차트 요약")
        # ... (이하 상세 뷰 코드) ...
        
else:
    st.error("데이터를 불러오는 데 실패했습니다. '1_Home' 페이지에서 연결을 확인하세요.")