"""
val_report_app.py — 사용자 친화 v4
큼직하고 직관적인 투자 스크리너
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="주식 가치평가 스크리너",
    page_icon="📊", layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
*, html, body, [class*="css"] { font-family: 'Noto Sans KR','Malgun Gothic',sans-serif !important; }
.stApp { background: #F2F4F7; }
.block-container { padding: 1.5rem 2rem !important; }

/* ── 헤더 ── */
.main-header {
    background: #0F1923;
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}
.main-header-title { color: #FFF; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
.main-header-sub   { color: #8A9BB0; font-size: 13px; margin-top: 4px; }
.header-tags { display: flex; gap: 10px; flex-wrap: wrap; }
.htag {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 6px 14px;
    color: #C8D8E8;
    font-size: 13px;
    font-weight: 500;
}
.htag span { color: #64B5F6; font-weight: 700; }

/* ── 큰 KPI ── */
.kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 20px; }
.kpi-card {
    background: #FFF;
    border-radius: 16px;
    padding: 22px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 5px solid #E0E0E0;
    cursor: default;
}
.kpi-card.green  { border-left-color: #1DB954; }
.kpi-card.red    { border-left-color: #E53935; }
.kpi-card.orange { border-left-color: #F57C00; }
.kpi-card.blue   { border-left-color: #1565C0; }
.kpi-label  { font-size: 12px; font-weight: 600; color: #8A8A90; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-number { font-size: 42px; font-weight: 800; color: #0F1923; line-height: 1; }
.kpi-desc   { font-size: 13px; color: #AAAAAA; margin-top: 6px; }

/* ── 섹션 박스 ── */
.section-box {
    background: #FFF;
    border-radius: 16px;
    padding: 24px 28px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}
.section-title { font-size: 17px; font-weight: 700; color: #0F1923; margin-bottom: 4px; }
.section-sub   { font-size: 13px; color: #8A9BB0; margin-bottom: 16px; }

/* ── 9칸 매트릭스 ── */
.matrix-table { width: 100%; border-collapse: separate; border-spacing: 6px; }
.matrix-head-cell {
    background: #0F1923; color: #8A9BB0;
    border-radius: 8px; padding: 10px 8px;
    font-size: 12px; font-weight: 600;
    text-align: center; letter-spacing: .04em;
}
.matrix-side-cell {
    background: #F2F4F7; border-radius: 8px;
    padding: 10px 12px; font-size: 13px;
    font-weight: 600; text-align: center;
    white-space: nowrap;
}
.matrix-cell {
    border-radius: 12px; padding: 14px 10px;
    text-align: center; transition: .2s;
}
.mc-best   { background: #E8F5E9; }
.mc-good   { background: #EDF7F1; }
.mc-warn   { background: #FFF8E1; }
.mc-mid    { background: #F5F5F5; }
.mc-bad    { background: #FFF3E0; }
.mc-danger { background: #FFEBEE; }
.mc-worst  { background: #FFCDD2; }
.mc-number { font-size: 32px; font-weight: 800; line-height: 1; }
.mc-label  { font-size: 11px; font-weight: 600; margin-top: 4px; }
.c-green  { color: #1B5E20; }
.c-tgreen { color: #2E7D32; }
.c-yellow { color: #E65100; }
.c-gray   { color: #555; }
.c-orange { color: #BF360C; }
.c-red    { color: #B71C1C; }

/* ── 설명 박스 ── */
.info-box {
    background: #F8F9FC;
    border-radius: 12px;
    padding: 16px 20px;
    border-left: 4px solid #1565C0;
    margin-top: 12px;
}
.info-box-title { font-size: 14px; font-weight: 700; color: #1565C0; margin-bottom: 8px; }
.info-box-text  { font-size: 13px; color: #445; line-height: 1.8; }

/* ── 투자의견 카드 ── */
.verdict-card {
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    border-left: 8px solid;
}
.verdict-buy    { background: #F1FBF5; border-color: #1DB954; }
.verdict-watch  { background: #FFF8EC; border-color: #F57C00; }
.verdict-avoid  { background: #FFF0F0; border-color: #E53935; }
.verdict-trap   { background: #FFF4E5; border-color: #F57C00; }
.verdict-name   { font-size: 15px; font-weight: 500; color: #555; margin-bottom: 4px; }
.verdict-signal { font-size: 32px; font-weight: 800; margin-bottom: 8px; }
.verdict-buy  .verdict-signal { color: #1B5E20; }
.verdict-watch .verdict-signal { color: #E65100; }
.verdict-avoid .verdict-signal { color: #B71C1C; }
.verdict-trap .verdict-signal  { color: #E65100; }
.verdict-desc   { font-size: 15px; color: #445; line-height: 1.7; }

/* ── 지표 그리드 ── */
.metric-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 12px; margin-bottom: 16px; }
.metric-card {
    background: #FFF;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.metric-name  { font-size: 12px; font-weight: 600; color: #8A8A90; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.metric-value { font-size: 28px; font-weight: 800; color: #0F1923; line-height: 1; }
.metric-hint  { font-size: 12px; color: #AAAAAA; margin-top: 4px; }
.metric-good  .metric-value { color: #1B5E20; }
.metric-bad   .metric-value { color: #B71C1C; }

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    background: #FFF;
    border-radius: 12px;
    padding: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    gap: 4px;
    margin-bottom: 16px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 20px;
    color: #888 !important;
}
.stTabs [aria-selected="true"] {
    background: #0F1923 !important;
    color: #FFF !important;
}

/* 사이드바 */
section[data-testid="stSidebar"] { background: #0F1923; }
section[data-testid="stSidebar"] * { color: #C8D8E8 !important; }
</style>
""", unsafe_allow_html=True)

# ── 데이터 ────────────────────────────────────────────────────────────────────
MATRIX_MAP = {
    ('위험','고평가'): ('즉시 회피',   'worst',  'c-red'),
    ('위험','적정'):   ('재무 위험',   'danger', 'c-red'),
    ('위험','저평가'): ('가치 함정',   'bad',    'c-orange'),
    ('주의','고평가'): ('회피 검토',   'bad',    'c-orange'),
    ('주의','적정'):   ('관찰 필요',   'mid',    'c-gray'),
    ('주의','저평가'): ('관심 종목',   'warn',   'c-yellow'),
    ('정상','고평가'): ('과열 주의',   'warn',   'c-yellow'),
    ('정상','적정'):   ('관망',        'mid',    'c-gray'),
    ('정상','저평가'): ('매수 검토',   'best',   'c-green'),
}

VERDICT = {
    '매수 검토': ('buy',   '매수 검토',   '재무가 건강하고 주가가 저평가된 종목입니다. 기업 본질 가치 대비 주가가 낮아 투자 매력이 있습니다.'),
    '관심 종목': ('watch', '관심 종목',   '저평가 신호가 있지만 재무 상태를 추가 확인하세요.'),
    '과열 주의': ('watch', '과열 주의',   '재무는 건전하지만 현재 주가가 기업 가치보다 높습니다. 추가 매수는 신중히 판단하세요.'),
    '관망':      ('watch', '관망',        '특별한 투자 포인트가 없습니다. 다른 기회를 기다리세요.'),
    '관찰 필요': ('watch', '관찰 필요',   '재무 상태가 다소 불안합니다. 꾸준히 모니터링하세요.'),
    '회피 검토': ('avoid', '회피 검토',   '재무가 불안정하고 주가도 높습니다. 투자를 피하는 것을 권장합니다.'),
    '가치 함정': ('trap',  '가치 함정',   '주가가 낮아 저렴해 보이지만 재무 상태가 나쁩니다. 이유 있는 저가입니다. 투자 전 반드시 재무제표를 직접 확인하세요.'),
    '재무 위험': ('avoid', '재무 위험',   '재무 상태가 심각하게 위험합니다. 투자를 피하세요.'),
    '즉시 회피': ('avoid', '즉시 회피',   '재무 위험 + 고평가의 최악 조합입니다. 즉시 관심 목록에서 제외하세요.'),
}

CLST_LABEL = {
    'EHS': 'EHS (고안정·저평가)',
    'FD':  'FD (재무위험)',
    'HS':  'HS (균형안정)',
    'LR':  'LR (전통가치주)',
    'NG':  'NG (성장주)',
    'WG':  'WG (취약성장)',
}

BASE = os.path.dirname(os.path.abspath(__file__))

@st.cache_data(ttl=300)
def load():
    df = pd.read_csv(os.path.join(BASE,'val_report_data.csv'), encoding='utf-8-sig')
    df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)
    df['year']       = df['year'].astype(int)
    if 'risk_grade' not in df.columns:
        def rg(g):
            if g in ['Critical','High Risk']: return '위험'
            if g in ['Medium Risk','Watchlist']: return '주의'
            return '정상'
        df['risk_grade'] = df['anomaly_grade'].apply(rg)
    def get_signal(r):
        info = MATRIX_MAP.get((r.get('risk_grade',''), r.get('val_grade','')))
        return info[0] if info else '기타'
    df['final_signal'] = df.apply(get_signal, axis=1)
    return df

df = load()
latest_year = int(df['year'].max())
today_str   = date.today().strftime('%Y년 %m월 %d일')
n_total     = df['stock_code'].nunique()

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <div>
    <div class="main-header-title">주식 가치평가 스크리너</div>
    <div class="main-header-sub">코스피·코스닥 상장 기업의 재무 건전성과 저평가 여부를 한눈에 확인하세요</div>
  </div>
  <div class="header-tags">
    <div class="htag">재무 기준 <span>{latest_year}년</span></div>
    <div class="htag">주가 기준 <span>{today_str}</span></div>
    <div class="htag">분석 종목 <span>{n_total:,}개</span></div>
    <div class="htag">PBR · PER 매일 자동 갱신</div>
  </div>
</div>
""", unsafe_allow_html=True)

df_f = df.copy()

# ── 탭 ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["전체 현황", "종목 스크리너", "종목 분석 리포트", "가치 지도"])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — 전체 현황
# ══════════════════════════════════════════════════════════════════
with tab1:
    n_buy   = (df_f['final_signal']=='매수 검토').sum()
    n_trap  = (df_f['final_signal']=='가치 함정').sum()
    n_avoid = df_f['final_signal'].isin(['즉시 회피','재무 위험','회피 검토']).sum()

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card green">
        <div class="kpi-label">매수 검토 종목</div>
        <div class="kpi-number">{n_buy}</div>
        <div class="kpi-desc">재무 건전 + 저평가</div>
      </div>
      <div class="kpi-card orange">
        <div class="kpi-label">가치 함정 주의</div>
        <div class="kpi-number">{n_trap}</div>
        <div class="kpi-desc">저렴해 보이지만 재무 위험</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-label">회피 권고 종목</div>
        <div class="kpi-number">{n_avoid}</div>
        <div class="kpi-desc">재무 위험 또는 고평가</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-label">전체 분석 종목</div>
        <div class="kpi-number">{len(df_f):,}</div>
        <div class="kpi-desc">코스피 + 코스닥</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([6, 5], gap="large")

    with col1:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">투자 시그널 현황판</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">재무 건전성과 가치평가를 조합한 9가지 투자 판단 결과</div>', unsafe_allow_html=True)

        risk3 = ['정상', '주의', '위험']
        val3  = ['저평가', '적정', '고평가']
        VAL_HEAD = {
            '저평가': '저평가<div style="font-size:11px;color:#888;font-weight:400;margin-top:2px">주가가 쌈</div>',
            '적정':   '적정<div style="font-size:11px;color:#888;font-weight:400;margin-top:2px">적당한 가격</div>',
            '고평가': '고평가<div style="font-size:11px;color:#888;font-weight:400;margin-top:2px">주가가 비쌈</div>',
        }
        RISK_ICON = {'정상': '● 재무 정상', '주의': '◐ 재무 주의', '위험': '○ 재무 위험'}
        RISK_SUB  = {'정상': '건전한 기업', '주의': '모니터링 필요', '위험': '심각한 상태'}

        tbl = '<table class="matrix-table">'
        tbl += '<tr><td style="width:100px"></td>'
        for v in val3:
            tbl += f'<td class="matrix-head-cell">{VAL_HEAD[v]}</td>'
        tbl += '</tr>'

        for r in risk3:
            risk_color = {'정상':'#1B5E20','주의':'#E65100','위험':'#B71C1C'}[r]
            tbl += f'''<tr>
            <td class="matrix-side-cell">
              <div style="color:{risk_color};font-size:13px;font-weight:700">{RISK_ICON[r]}</div>
              <div style="color:#888;font-size:11px;font-weight:400;margin-top:2px">{RISK_SUB[r]}</div>
            </td>'''
            for v in val3:
                info = MATRIX_MAP.get((r, v), ('기타', 'mid', 'c-gray'))
                sig_name, mc_cls, fc_cls = info
                n = ((df_f['risk_grade']==r) & (df_f['val_grade']==v)).sum()
                tbl += f'''<td class="matrix-cell mc-{mc_cls}">
                  <div class="mc-number {fc_cls}">{n}</div>
                  <div class="mc-label {fc_cls}">{sig_name}</div>
                </td>'''
            tbl += '</tr>'
        tbl += '</table>'
        st.markdown(tbl, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-box" style="margin-top:16px">
          <div class="info-box-title">이 현황판은 어떻게 읽나요?</div>
          <div class="info-box-text">
            <b>가로축</b>은 현재 주가 수준입니다. 왼쪽일수록 주가가 싸고, 오른쪽일수록 비쌉니다.<br>
            <b>세로축</b>은 기업의 재무 건전성입니다. 위로 갈수록 재무가 건전합니다.<br><br>
            <b>왼쪽 위 (재무 좋고 + 주가 쌈)</b> → <b style="color:#1B5E20">매수 검토</b> — 가장 좋은 조합<br>
            <b>오른쪽 아래 (재무 나쁘고 + 주가 비쌈)</b> → <b style="color:#B71C1C">즉시 회피</b> — 가장 나쁜 조합<br>
            <b>왼쪽 아래 (주가 싸지만 재무 위험)</b> → <b style="color:#E65100">가치 함정</b> — 이유 있는 저가, 주의!
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">시그널별 종목 수</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">전체 종목이 9가지 시그널 중 어디에 해당하는지</div>', unsafe_allow_html=True)

        SIG_ORDER = ['매수 검토','관심 종목','과열 주의','관망','관찰 필요','회피 검토','가치 함정','재무 위험','즉시 회피']
        SIG_COLOR = {
            '매수 검토':'#1DB954','관심 종목':'#43A047','과열 주의':'#1565C0',
            '관망':'#9E9E9E','관찰 필요':'#F9A825','회피 검토':'#EF6C00',
            '가치 함정':'#E53935','재무 위험':'#C62828','즉시 회피':'#B71C1C',
        }
        SIG_DESC = {
            '매수 검토':   '재무 건전 · 주가 저평가',
            '관심 종목':   '재무 주의 · 주가 저평가',
            '과열 주의':   '재무 건전 · 주가 고평가',
            '관망':        '재무 건전 · 적정 가격',
            '관찰 필요':   '재무 주의 · 적정 가격',
            '회피 검토':   '재무 주의 · 주가 고평가',
            '가치 함정':   '재무 위험 · 주가 저평가',
            '재무 위험':   '재무 위험 · 적정 가격',
            '즉시 회피':   '재무 위험 · 주가 고평가',
        }
        sig_cnt = df_f['final_signal'].value_counts()
        sigs  = [s for s in SIG_ORDER if s in sig_cnt.index]
        vals  = [sig_cnt.get(s,0) for s in sigs]
        descs = [SIG_DESC.get(s,'') for s in sigs]
        colors= [SIG_COLOR.get(s,'#CCC') for s in sigs]
        labels= [f"<b>{s}</b><br><span style='font-size:10px;color:#999'>{d}</span>" for s,d in zip(sigs,descs)]

        fig = go.Figure(go.Bar(
            x=vals, y=labels, orientation='h',
            marker_color=colors, marker_line_width=0,
            text=vals, textposition='outside',
            textfont=dict(size=13, color='#333', family='Noto Sans KR'),
            hovertemplate='%{y}<br>종목 수: %{x}개<extra></extra>'
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=360, margin=dict(l=4, r=60, t=4, b=4),
            xaxis=dict(visible=False),
            yaxis=dict(tickfont=dict(size=12, family='Noto Sans KR'), autorange='reversed'),
            font=dict(family='Noto Sans KR,Malgun Gothic')
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if n_trap > 0:
            st.markdown(f"""
            <div style="background:#FFF4E5;border-radius:12px;padding:16px 18px;border:1px solid #FFCC80">
              <div style="font-size:15px;font-weight:700;color:#E65100;margin-bottom:6px">가치 함정 {n_trap}개 종목 발견</div>
              <div style="font-size:13px;color:#6D4C41;line-height:1.6">
                주가가 낮아 저렴해 보이지만 재무 상태가 위험한 종목입니다.<br>
                단순히 주가가 싸다는 이유로 투자하면 큰 손실이 날 수 있습니다.<br>
                <b>종목 스크리너</b>에서 목록을 확인하세요.
              </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — 스크리너
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">종목 스크리너</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">조건을 설정하면 해당 종목 리스트를 바로 확인할 수 있습니다</div>', unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 1])
    with fc1:
        sig_choice = st.selectbox('시그널 선택', [
            '매수 검토 (재무 건전 + 저평가)',
            '관심 종목 (재무 주의 + 저평가)',
            '가치 함정 (함정 주의)',
            '즉시 회피 + 재무 위험',
            '전체 시그널 보기',
        ])
    with fc2:
        sort_choice = st.selectbox('정렬 기준', [
            '가치점수 높은 순',
            'PBR 낮은 순',
            'PER 낮은 순',
            '12개월 수익률 높은 순',
        ])
    with fc3:
        risk_choice = st.multiselect('재무 건전성', ['정상','주의','위험'],
                                      default=['정상','주의','위험'],
                                      format_func=lambda x: {'정상':'정상 (건전)','주의':'주의 (불안)','위험':'위험 (심각)'}.get(x,x))
    with fc4:
        top_n = st.number_input('표시 수', 10, 500, 50, step=10)

    st.markdown('</div>', unsafe_allow_html=True)

    ALL_SIGS = list({v[0] for v in MATRIX_MAP.values()})
    sig_map = {
        '매수 검토 (재무 건전 + 저평가)': ['매수 검토'],
        '관심 종목 (재무 주의 + 저평가)': ['관심 종목'],
        '가치 함정 (함정 주의)':           ['가치 함정'],
        '즉시 회피 + 재무 위험':           ['즉시 회피','재무 위험'],
        '전체 시그널 보기':                 ALL_SIGS,
    }
    target_sigs = sig_map.get(sig_choice, ALL_SIGS)

    df_sc = df_f[df_f['risk_grade'].isin(risk_choice) & df_f['final_signal'].isin(target_sigs)].copy()

    sort_col_map = {
        '가치점수 높은 순':       ('val_score', False),
        'PBR 낮은 순':            ('pbr', True),
        'PER 낮은 순':            ('per', True),
        '12개월 수익률 높은 순':  ('momentum_12m', False),
    }
    scol, sasc = sort_col_map.get(sort_choice, ('val_score', False))
    if scol in df_sc.columns:
        df_sc = df_sc.sort_values(scol, ascending=sasc)
    df_sc = df_sc.head(int(top_n))

    show = [c for c in ['corp_name','stock_code','cluster_label','risk_grade','val_grade',
                         'final_signal','val_score','pbr','per','ev_ebitda','momentum_12m'] if c in df_sc.columns]
    ddisp = df_sc[show].copy()
    if 'cluster_label' in ddisp.columns:
        ddisp['cluster_label'] = ddisp['cluster_label'].map(CLST_LABEL).fillna(ddisp['cluster_label'])
    if 'momentum_12m' in ddisp.columns:
        ddisp['momentum_12m'] = ddisp['momentum_12m'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else '-')
    # NaN → 의미있는 텍스트로 변환 (pandas 3.x 호환)
    if 'pbr' in ddisp.columns:
        ddisp['pbr'] = ddisp['pbr'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '자본잠식')
    if 'per' in ddisp.columns:
        ddisp['per'] = ddisp['per'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else '적자기업')
    if 'ev_ebitda' in ddisp.columns:
        ddisp['ev_ebitda'] = ddisp['ev_ebitda'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else '영업손실')
    ddisp = ddisp.rename(columns={
        'corp_name':'기업명','stock_code':'종목코드','cluster_label':'재무군집',
        'risk_grade':'재무건전성','val_grade':'가치평가','final_signal':'시그널',
        'val_score':'가치점수','pbr':'PBR','per':'PER','ev_ebitda':'EV/EBITDA','momentum_12m':'12개월수익률'
    })

    st.caption(f"검색 결과 {len(ddisp)}개 종목  |  재무 기준: {latest_year}년  |  주가 기준: 오늘  |  PBR·PER 낮을수록 저평가  |  자본잠식·적자·영업손실 기업은 해당 배수 계산 불가")
    st.dataframe(ddisp.style.format({'가치점수':'{:.3f}'}, na_rep='-'),
                 use_container_width=True, height=500, hide_index=True)

    with st.expander("PBR · PER · EV/EBITDA 지표 설명"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.markdown("""
            **PBR (주가순자산비율)**

            주가 ÷ 주당 순자산

            - 1 미만 → 기업 장부가치보다 싸게 거래 중
            - 숫자가 낮을수록 저평가 가능성
            - 단, 업종마다 평균이 달라 같은 군집 내에서 비교합니다
            """)
        with ec2:
            st.markdown("""
            **PER (주가수익비율)**

            주가 ÷ 주당 순이익

            - 10배 = 이익의 10배에 거래 중
            - 낮을수록 이익 대비 저평가
            - 적자 기업은 계산 불가 → N/A 표시
            """)
        with ec3:
            st.markdown("""
            **EV/EBITDA**

            기업 전체 가치 ÷ 영업 이익

            - 부채까지 포함한 종합 평가 지표
            - 낮을수록 저평가
            - PER이 계산 안 되는 경우 대안으로 활용
            """)

    # 가치 함정 경고
    traps = df_f[df_f['final_signal']=='가치 함정']
    if not traps.empty:
        with st.expander(f"가치 함정 종목 목록 ({len(traps)}개) — 투자 전 반드시 확인", expanded=False):
            st.markdown("""
            <div style="background:#FFF0F0;border-radius:12px;padding:16px 18px;margin-bottom:12px;border:1px solid #FFCDD2">
              <div style="font-size:15px;font-weight:700;color:#B71C1C;margin-bottom:6px">가치 함정이란?</div>
              <div style="font-size:13px;color:#4A1010;line-height:1.7">
                PBR이나 PER이 낮아서 싸 보이지만, 실제로는 재무 상태가 매우 나쁜 종목입니다.<br>
                주가가 낮은 데는 이유가 있습니다 — 시장이 이미 재무 위험을 반영한 것입니다.<br>
                <b>단순히 '싸다'는 이유로 투자하면 더 큰 손실을 볼 수 있습니다.</b>
              </div>
            </div>
            """, unsafe_allow_html=True)
            tc = [c for c in ['corp_name','stock_code','cluster_label','val_score','pbr','per','anomaly_score'] if c in traps.columns]
            st.dataframe(traps[tc].rename(columns={
                'corp_name':'기업명','stock_code':'종목코드','cluster_label':'재무군집',
                'val_score':'가치점수','pbr':'PBR','per':'PER','anomaly_score':'위험점수'
            }).style.format({'가치점수':'{:.3f}','PBR':'{:.2f}','PER':'{:.1f}','위험점수':'{:.3f}'}, na_rep='-'),
            use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════
# TAB 3 — 리포트
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">종목 분석 리포트</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">종목코드 6자리 또는 기업명을 입력하면 상세 분석 리포트가 생성됩니다</div>', unsafe_allow_html=True)

    qcol, _ = st.columns([3, 4])
    with qcol:
        query = st.text_input('', placeholder='종목코드 또는 기업명 입력 (예: 005930, 삼성전자)',
                               label_visibility='collapsed')
    st.markdown('</div>', unsafe_allow_html=True)

    sel_corp = None
    if query:
        mq = df['stock_code'].str.contains(query, na=False)
        if 'corp_name' in df.columns:
            mq = mq | df['corp_name'].str.contains(query, na=False)
        hits = df[mq]['corp_name'].unique() if 'corp_name' in df.columns else df[mq]['stock_code'].unique()
        if len(hits) == 0:
            st.warning('검색 결과가 없습니다. 종목코드(6자리) 또는 기업명을 정확히 입력해주세요.')
        elif len(hits) == 1:
            sel_corp = hits[0]
        else:
            sel_corp = st.selectbox('여러 종목이 검색됐습니다:', hits)

    if sel_corp:
        kc  = 'corp_name' if 'corp_name' in df.columns else 'stock_code'
        dc  = df[df[kc]==sel_corp].sort_values('year')
        lat = dc.iloc[-1]
        code= dc['stock_code'].iloc[0]
        sig = str(lat.get('final_signal', '기타'))
        vrd = VERDICT.get(sig, ('watch', sig, '추가 분석이 필요합니다.'))
        op_cls, op_label, op_desc = vrd

        # 투자의견 카드
        st.markdown(f"""
        <div class="verdict-card verdict-{op_cls}">
          <div class="verdict-name">{code}  {sel_corp}</div>
          <div class="verdict-signal">{op_label}</div>
          <div class="verdict-desc">{op_desc}</div>
        </div>
        """, unsafe_allow_html=True)

        st.info(f"재무 데이터: {latest_year}년 DART 공시 기준   |   주가: {today_str} 기준으로 PBR · PER 자동 계산")

        def fv(col, fmt):
            v = lat.get(col)
            return fmt.format(v) if pd.notna(v) else 'N/A'

        pbr = lat.get('pbr'); per = lat.get('per'); mom = lat.get('momentum_12m')
        pbr_cls = 'metric-good' if pd.notna(pbr) and pbr < 1 else 'metric-bad' if pd.notna(pbr) and pbr > 3 else ''
        per_cls = 'metric-good' if pd.notna(per) and per < 10 else 'metric-bad' if pd.notna(per) and per > 30 else ''
        mom_cls = 'metric-good' if pd.notna(mom) and mom > 0 else 'metric-bad' if pd.notna(mom) else ''

        pbr_hint = ('1 미만 — 장부가치보다 싸게 거래 중' if pd.notna(pbr) and pbr<1
                    else '1 이상 — 장부가치보다 비싸게 거래 중' if pd.notna(pbr)
                    else '자본잠식 기업 — PBR 계산 불가 (자본이 마이너스)')
        per_hint = ('낮은 PER — 이익 대비 저평가' if pd.notna(per) and per<10
                    else '높은 PER — 이익 대비 고평가' if pd.notna(per) and per>30
                    else '적자 기업 — PER 계산 불가 (순이익 없음)' if not pd.notna(per)
                    else '보통 수준')
        mom_hint = ('최근 1년 주가 상승 중' if pd.notna(mom) and mom>0
                    else '최근 1년 주가 하락 중' if pd.notna(mom) else '-')

        st.markdown(f"""
        <div class="metric-grid">
          <div class="metric-card {pbr_cls}">
            <div class="metric-name">PBR — 주가순자산비율</div>
            <div class="metric-value">{fv('pbr','{:.2f}')}</div>
            <div class="metric-hint">{pbr_hint}</div>
          </div>
          <div class="metric-card {per_cls}">
            <div class="metric-name">PER — 주가수익비율</div>
            <div class="metric-value">{fv('per','{:.1f}x')}</div>
            <div class="metric-hint">{per_hint}</div>
          </div>
          <div class="metric-card">
            <div class="metric-name">EV/EBITDA</div>
            <div class="metric-value">{fv('ev_ebitda','{:.1f}x')}</div>
            <div class="metric-hint">낮을수록 기업 전체 가치 저평가</div>
          </div>
          <div class="metric-card {mom_cls}">
            <div class="metric-name">12개월 주가 수익률</div>
            <div class="metric-value">{fv('momentum_12m','{:.1%}')}</div>
            <div class="metric-hint">{mom_hint}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        r1, r2 = st.columns(2, gap="medium")

        with r1:
            risk  = lat.get('risk_grade', '-')
            val   = lat.get('val_grade', '-')
            vscore= lat.get('val_score')
            prob  = lat.get('prob_저평가')
            ai    = lat.get('lgbm_pred_name', '-')
            clst  = lat.get('cluster_label', '-')
            RISK_D = {'위험':'위험 — 부채·손실 등 이상 신호 감지','주의':'주의 — 일부 지표 모니터링 필요','정상':'정상 — 안정적인 재무 구조'}
            VAL_D  = {'고평가':'주가가 기업 가치보다 높습니다','적정':'주가가 기업 가치에 적절합니다','저평가':'주가가 기업 가치보다 낮습니다'}
            CLST_D = CLST_LABEL

            st.markdown(f"""
            <div class="section-box" style="height:100%">
              <div class="section-title">분석 결과 상세</div>
              <table style="width:100%;border-collapse:collapse">
                <tr style="border-bottom:1px solid #F0F0EC">
                  <td style="padding:12px 4px;font-size:12px;color:#888;font-weight:600;width:110px">재무 건전성</td>
                  <td style="padding:12px 4px;font-size:14px;color:#1A1A1A">{RISK_D.get(str(risk), risk)}</td>
                </tr>
                <tr style="border-bottom:1px solid #F0F0EC">
                  <td style="padding:12px 4px;font-size:12px;color:#888;font-weight:600">가치 평가</td>
                  <td style="padding:12px 4px;font-size:14px;color:#1A1A1A">{VAL_D.get(str(val), val)}</td>
                </tr>
                <tr style="border-bottom:1px solid #F0F0EC">
                  <td style="padding:12px 4px;font-size:12px;color:#888;font-weight:600">가치 점수</td>
                  <td style="padding:12px 4px;font-size:14px;color:#1A1A1A">{f'{vscore:.3f}' if pd.notna(vscore) else 'N/A'}
                    <span style="font-size:11px;color:#AAA"> (1에 가까울수록 저평가·안정)</span></td>
                </tr>
                <tr style="border-bottom:1px solid #F0F0EC">
                  <td style="padding:12px 4px;font-size:12px;color:#888;font-weight:600">AI 예측</td>
                  <td style="padding:12px 4px;font-size:14px;color:#1A1A1A">{ai}
                    {f' <span style="color:#888;font-size:12px">(저평가 확률 {prob:.0%})</span>' if pd.notna(prob) else ''}</td>
                </tr>
                <tr>
                  <td style="padding:12px 4px;font-size:12px;color:#888;font-weight:600">재무 군집</td>
                  <td style="padding:12px 4px;font-size:14px;color:#1A1A1A">{clst}
                    <span style="font-size:12px;color:#AAA"> ({CLST_D.get(str(clst), '')})</span></td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

        with r2:
            if len(dc) > 1 and 'val_score' in dc.columns:
                fig_h = go.Figure()
                fig_h.add_trace(go.Scatter(
                    x=dc['year'].astype(str), y=dc['val_score'],
                    name='가치점수 (높을수록 저평가)',
                    mode='lines+markers',
                    line=dict(color='#1565C0', width=3),
                    marker=dict(size=10, color='#1565C0'),
                    hovertemplate='%{x}년<br>가치점수: %{y:.3f}<extra></extra>'))
                if 'anomaly_score' in dc.columns:
                    fig_h.add_trace(go.Scatter(
                        x=dc['year'].astype(str), y=dc['anomaly_score'],
                        name='위험점수 (높을수록 위험)',
                        mode='lines+markers',
                        line=dict(color='#E53935', width=2.5, dash='dash'),
                        marker=dict(size=9, color='#E53935'),
                        hovertemplate='%{x}년<br>위험점수: %{y:.3f}<extra></extra>'))
                fig_h.update_layout(
                    title=dict(text='연도별 점수 변화', font=dict(size=14, family='Noto Sans KR')),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FAFAFA',
                    height=260, margin=dict(l=4, r=4, t=40, b=4),
                    legend=dict(orientation='h', y=-0.25, font=dict(size=11)),
                    yaxis=dict(gridcolor='#EEEEEA'),
                    xaxis=dict(title='기준 연도', tickfont=dict(size=12)),
                    font=dict(family='Noto Sans KR,Malgun Gothic', size=11))
                st.plotly_chart(fig_h, use_container_width=True)

        if sig == '가치 함정':
            st.error("**가치 함정 경고**  주가가 낮아 저렴해 보이지만 재무 상태가 심각하게 나쁩니다. '싸다'는 이유만으로 투자하면 큰 손실이 날 수 있습니다. 재무제표를 반드시 직접 확인하세요.")
        elif sig == '즉시 회피':
            st.error("**즉시 회피 권고**  재무가 위험하고 주가도 과도하게 비쌉니다. 투자를 강력히 권장하지 않습니다.")
        elif sig == '매수 검토':
            st.success("**매수 검토 종목**  재무가 건전하고 주가가 저평가된 상태입니다. 본 분석은 참고용이며 투자 결정은 반드시 본인이 판단하세요.")

        st.markdown(f"##### 연도별 이력  ·  재무는 각 연도 공시 기준 / 주가는 각 연도 말 기준")
        hc = [c for c in ['year','risk_grade','val_grade','final_signal','val_score','pbr','per','ev_ebitda','momentum_12m'] if c in dc.columns]
        hd = dc[hc].copy()
        hd['year'] = hd['year'].astype(str) + '년'
        hd = hd.rename(columns={'year':'기준연도','risk_grade':'재무건전성','val_grade':'가치평가',
                                  'final_signal':'시그널','val_score':'가치점수',
                                  'pbr':'PBR','per':'PER','ev_ebitda':'EV/EBITDA','momentum_12m':'12개월수익률'})
        if '12개월수익률' in hd.columns:
            hd['12개월수익률'] = hd['12개월수익률'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else '-')
        st.dataframe(hd.style.format({'가치점수':'{:.3f}','PBR':'{:.2f}','PER':'{:.1f}','EV/EBITDA':'{:.1f}'}, na_rep='-'),
                     use_container_width=True, hide_index=True)

        st.caption("본 분석은 투자 참고용 정보이며 투자 권유가 아닙니다. 투자 손익에 대한 책임은 본인에게 있습니다.")

    else:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;color:#BBBBBB">
          <div style="font-size:16px;font-weight:500;color:#888">종목코드 또는 기업명을 입력하세요</div>
          <div style="font-size:13px;margin-top:8px">예시: 005930, 삼성전자, 카카오, 현대차</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 4 — 가치 지도
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">전체 종목 가치 지도</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">PBR과 12개월 수익률로 전체 종목의 위치를 한눈에 파악합니다</div>', unsafe_allow_html=True)

    gc1, gc2 = st.columns([1, 4])
    with gc1:
        yr_sel = st.selectbox('기준 연도', sorted(df['year'].unique(), reverse=True), key='vmap')

    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px">
      <div style="background:#F8FFF9;border:1px solid #C8E6C9;border-radius:10px;padding:12px 14px">
        <div style="font-size:12px;font-weight:700;color:#1B5E20;margin-bottom:4px">왼쪽 위</div>
        <div style="font-size:13px;color:#333">PBR 낮고 수익률 높음<br><b>가장 이상적인 구간</b></div>
      </div>
      <div style="background:#FFF8F0;border:1px solid #FFE0B2;border-radius:10px;padding:12px 14px">
        <div style="font-size:12px;font-weight:700;color:#E65100;margin-bottom:4px">왼쪽 아래</div>
        <div style="font-size:13px;color:#333">PBR 낮고 수익률 낮음<br><b>저점 매수 기회 탐색 구간</b></div>
      </div>
      <div style="background:#FFF8F0;border:1px solid #FFE0B2;border-radius:10px;padding:12px 14px">
        <div style="font-size:12px;font-weight:700;color:#E65100;margin-bottom:4px">오른쪽 위</div>
        <div style="font-size:13px;color:#333">PBR 높고 수익률 높음<br><b>추가 매수 신중히 판단</b></div>
      </div>
      <div style="background:#FFF0F0;border:1px solid #FFCDD2;border-radius:10px;padding:12px 14px">
        <div style="font-size:12px;font-weight:700;color:#B71C1C;margin-bottom:4px">오른쪽 아래</div>
        <div style="font-size:13px;color:#333">PBR 높고 수익률 낮음<br><b>회피 권고 구간</b></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    df_v = df[(df['year']==yr_sel) & df['pbr'].notna() & df['momentum_12m'].notna()].copy()
    df_v = df_v[df_v['pbr'] < df_v['pbr'].quantile(0.97)]

    top30 = df_v.nlargest(30,'val_score').index if 'val_score' in df_v.columns else []
    df_v['종목구분'] = '일반 종목'
    if len(top30) > 0: df_v.loc[top30, '종목구분'] = '매수 검토 Top 30'
    df_v.loc[df_v['final_signal']=='가치 함정', '종목구분'] = '가치 함정 주의'

    CLST_COLOR = {'EHS':'#1DB954','FD':'#E53935','HS':'#1565C0','LR':'#F57C00','NG':'#7B1FA2','WG':'#795548'}


    hover = ['stock_code','risk_grade','val_grade','final_signal']
    if 'corp_name' in df_v.columns: hover = ['corp_name'] + hover

    fig_v = px.scatter(df_v, x='pbr', y='momentum_12m',
        color='cluster_label' if 'cluster_label' in df_v.columns else 'risk_grade',
        color_discrete_map=CLST_COLOR,
        symbol='종목구분',
        symbol_map={'일반 종목':'circle','매수 검토 Top 30':'star','가치 함정 주의':'x'},
        size='val_score' if 'val_score' in df_v.columns else None,
        size_max=22, hover_data=hover, opacity=0.65,
        labels={'pbr':'PBR (낮을수록 저평가)','momentum_12m':'12개월 수익률','cluster_label':'재무군집'})

    fig_v.add_hline(y=0, line_dash='dot', line_color='#CCCCCC', line_width=1.5,
                    annotation_text='수익률 0%', annotation_font_size=11, annotation_font_color='#AAA')
    fig_v.add_vline(x=1, line_dash='dot', line_color='#CCCCCC', line_width=1.5,
                    annotation_text='PBR = 1', annotation_font_size=11, annotation_font_color='#AAA')

    fig_v.add_shape(type='rect', x0=0, x1=1, y0=0, y1=1.5,
                    fillcolor='rgba(29,185,84,0.05)', line=dict(width=0))

    fig_v.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FAFAFA',
        height=540, margin=dict(l=8,r=8,t=8,b=8),
        font=dict(family='Noto Sans KR,Malgun Gothic', size=12),
        yaxis=dict(tickformat='.0%', gridcolor='#EEEEEA', title='12개월 수익률'),
        xaxis=dict(gridcolor='#EEEEEA', title='PBR (낮을수록 주가 저평가)'),
        legend=dict(font=dict(size=11), title_text=''))
    st.plotly_chart(fig_v, use_container_width=True)

    st.caption(f"별표(★) = 매수 검토 Top 30   X 표시 = 가치 함정 주의   점 크기 = 가치점수   재무: {yr_sel}년   주가: {today_str}")

    if len(top30) > 0:
        st.markdown('<div class="section-box" style="margin-top:8px">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">매수 검토 Top 30 ({yr_sel}년 기준)</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">가치점수 기준 상위 30개 종목 — 재무 건전 + 저평가 조합으로 자동 선별</div>', unsafe_allow_html=True)
        t30 = df_v.loc[top30].sort_values('val_score', ascending=False)
        tc  = [c for c in ['corp_name','stock_code','cluster_label','risk_grade','val_grade','final_signal','val_score','pbr','per','momentum_12m'] if c in t30.columns]
        t30[tc] = t30[tc].copy()
        if 'cluster_label' in t30.columns:
            t30['cluster_label'] = t30['cluster_label'].map(CLST_LABEL).fillna(t30['cluster_label'])
        t30d = t30[tc].rename(columns={
            'corp_name':'기업명','stock_code':'종목코드','cluster_label':'재무군집',
            'risk_grade':'재무건전성','val_grade':'가치평가','final_signal':'시그널',
            'val_score':'가치점수','pbr':'PBR','per':'PER','momentum_12m':'12개월수익률'})
        if '12개월수익률' in t30d.columns:
            t30d['12개월수익률'] = t30d['12개월수익률'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else '-')
        st.dataframe(t30d.style.format({'가치점수':'{:.3f}','PBR':'{:.2f}','PER':'{:.1f}'}, na_rep='-'),
                     use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("본 서비스는 투자 참고용 정보 제공을 목적으로 합니다. 투자 손익에 대한 책임은 투자자 본인에게 있습니다.")
