"""
val_report_app.py
=================
Bloomberg 터미널 스타일 실시간 투자 보고서

실행: streamlit run val_report_app.py
입력: val_final.csv, val_report_data.csv (valuation_pipeline.py 출력)
"""

import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="◼ EQUITY VALUATION SCREENER",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
*, html, body, [class*="css"] { font-family: 'IBM Plex Sans', 'Malgun Gothic', sans-serif !important; }
.stApp { background: #F0F0EC; }
.top-bar { background:#0A1628; padding:8px 20px; display:flex; align-items:center; gap:28px; margin:-1rem -1rem 16px -1rem; border-bottom:1px solid #1E3A5F; }
.top-title { font-size:13px; font-weight:600; color:#FFFFFF; letter-spacing:0.14em; font-family:'IBM Plex Mono',monospace !important; }
.top-item { font-family:'IBM Plex Mono',monospace !important; font-size:11px; color:#5A7A9F; }
.top-item b { color:#4FC3F7; }
.top-item.up b { color:#00D4A0; }
.top-item.down b { color:#FF4444; }
.kpi-row { display:grid; grid-template-columns:repeat(6,1fr); gap:1px; background:#D0D0C8; border:1px solid #D0D0C8; margin-bottom:10px; }
.kpi-cell { background:#FFFFFF; padding:8px 12px; }
.kpi-label { font-size:9px; font-weight:600; color:#8B8B80; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:3px; }
.kpi-value { font-family:'IBM Plex Mono',monospace; font-size:22px; font-weight:500; color:#0A1628; line-height:1; }
.kpi-sub { font-size:10px; color:#AAAAAA; margin-top:2px; font-family:'IBM Plex Mono',monospace; }
.kpi-danger .kpi-value { color:#E04040; }
.kpi-caution .kpi-value { color:#CC8800; }
.kpi-safe .kpi-value { color:#00A862; }
.kpi-blue .kpi-value { color:#0066CC; }
.panel { background:#FFFFFF; border:1px solid #D0D0C8; margin-bottom:10px; }
.ph { background:#0A1628; color:#5A7A9F; font-size:9px; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; padding:5px 10px; display:flex; justify-content:space-between; }
.ph b { color:#FFFFFF; }
.pb { padding:10px; }
.report-header { background:#0A1628; padding:12px 16px; display:flex; align-items:baseline; gap:12px; margin-bottom:12px; }
.report-ticker { font-family:'IBM Plex Mono',monospace; font-size:20px; font-weight:500; color:#FFFFFF; }
.report-name { font-size:13px; color:#5A7A9F; }
.report-opinion { margin-left:auto; font-family:'IBM Plex Mono',monospace; font-size:14px; font-weight:600; }
.op-buy { color:#00D4A0; }
.op-watch { color:#FFB800; }
.op-avoid { color:#FF4444; }
.op-trap { color:#FF8C00; }
.report-kpi { display:grid; grid-template-columns:repeat(5,1fr); gap:1px; background:#D0D0C8; border:1px solid #D0D0C8; margin-bottom:12px; }
.report-kpi-cell { background:#FFFFFF; padding:8px 12px; }
.report-kpi-label { font-size:9px; font-weight:600; color:#8B8B80; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:3px; }
.report-kpi-value { font-family:'IBM Plex Mono',monospace; font-size:18px; font-weight:500; color:#0A1628; }
.signal-row { display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #F0F0E8; font-size:12px; }
.signal-label { color:#666660; }
.signal-value { font-family:'IBM Plex Mono',monospace; font-weight:500; }
.stTabs [data-baseweb="tab-list"] { background:#0A1628; gap:0; padding:0 8px; }
.stTabs [data-baseweb="tab"] { font-size:10px; font-weight:600; color:#5A7A9F !important; padding:7px 14px; letter-spacing:0.1em; text-transform:uppercase; border-bottom:2px solid transparent; background:transparent !important; }
.stTabs [aria-selected="true"] { color:#FFFFFF !important; border-bottom:2px solid #4FC3F7 !important; }
section[data-testid="stSidebar"] { background:#0A1628; }
section[data-testid="stSidebar"] * { color:#C8D8E4 !important; }
section[data-testid="stSidebar"] label { font-size:9px !important; letter-spacing:0.12em !important; text-transform:uppercase !important; color:#5A7A9F !important; }
</style>
""", unsafe_allow_html=True)

# ── 상수 ──────────────────────────────────────────────────────────────────────
MATRIX = {
    ('위험','고평가'):'⚠즉시 회피',  ('위험','적정'):'⚠재무위험',  ('위험','저평가'):'⚠Value Trap',
    ('주의','고평가'):'회피 검토',    ('주의','적정'):'관찰 필요',   ('주의','저평가'):'기회 or Trap',
    ('정상','고평가'):'과열 주의',    ('정상','적정'):'관망',        ('정상','저평가'):'★진성 저평가',
}
OPINION_MAP = {
    '★진성 저평가':('BUY',   'op-buy'),
    '기회 or Trap': ('WATCH', 'op-watch'),
    '과열 주의':    ('WATCH', 'op-watch'),
    '관망':         ('NEUTRAL','op-watch'),
    '⚠Value Trap': ('TRAP',  'op-trap'),
    '⚠재무위험':   ('AVOID', 'op-avoid'),
    '⚠즉시 회피':  ('AVOID', 'op-avoid'),
    '회피 검토':    ('AVOID', 'op-avoid'),
    '관찰 필요':    ('WATCH', 'op-watch'),
}
CSS_MATRIX = {
    ('위험','고평가'):'c-rh', ('위험','적정'):'c-rm', ('위험','저평가'):'c-rl',
    ('주의','고평가'):'c-wh', ('주의','적정'):'c-wm', ('주의','저평가'):'c-wl',
    ('정상','고평가'):'c-nh', ('정상','적정'):'c-nm', ('정상','저평가'):'c-nl',
}
RENAME = {
    'corp_name':'기업명','stock_code':'종목','year':'연도','cluster_label':'군집',
    'risk_grade':'Risk','val_grade':'Valuation','final_signal':'Signal',
    'val_score':'ValScore','anomaly_score':'AnomalyScore',
    'pbr':'PBR','per':'PER','ev_ebitda':'EV/EBITDA','momentum_12m':'12M Rtn',
    'lgbm_pred_name':'LGBM예측','prob_저평가':'P(저평가)',
}

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load():
    df = pd.read_csv(os.path.join(BASE, 'val_final.csv'), encoding='utf-8-sig')
    df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)
    df['year'] = df['year'].astype(int)
    # risk_grade 없으면 생성
    if 'risk_grade' not in df.columns:
        def to_risk(g):
            if g in ['Critical','High Risk']: return '위험'
            if g in ['Medium Risk','Watchlist']: return '주의'
            return '정상'
        df['risk_grade'] = df['anomaly_grade'].apply(to_risk)
    if 'final_signal' not in df.columns:
        df['final_signal'] = df.apply(
            lambda r: MATRIX.get((r['risk_grade'], str(r.get('val_grade',''))), '기타'), axis=1)
    return df

df = load()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="padding:8px 0 16px"><span style="font-family:IBM Plex Mono,monospace;font-size:14px;font-weight:600;color:#FFFFFF;letter-spacing:0.1em">◼ VALUATION<br>SCREENER</span></div>', unsafe_allow_html=True)
    sel_year    = st.multiselect('YEAR',    sorted(df['year'].unique(), reverse=True), default=[df['year'].max()])
    sel_cluster = st.multiselect('CLUSTER', sorted(df['cluster_label'].unique()), default=sorted(df['cluster_label'].unique()))
    sel_risk    = st.multiselect('RISK',    ['위험','주의','정상'], default=['위험','주의','정상'])
    st.markdown('<div style="border-top:1px solid #1E3A5F;margin:12px 0"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:9px;color:#5A7A9F;letter-spacing:0.08em">MODEL PERFORMANCE</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:18px;color:#00D4A0;font-weight:500">0.8498</div><div style="font-size:9px;color:#5A7A9F">ACCURACY (5-FOLD CV)</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:18px;color:#4FC3F7;font-weight:500;margin-top:8px">+0.1328</div><div style="font-size:9px;color:#5A7A9F">SPEARMAN ρ (MONOTONICITY)</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:18px;color:#FFB800;font-weight:500;margin-top:8px">21.37%p</div><div style="font-size:9px;color:#5A7A9F">9-BOX RETURN SPREAD</div>', unsafe_allow_html=True)

mask = (df['year'].isin(sel_year) &
        df['cluster_label'].isin(sel_cluster) &
        df['risk_grade'].isin(sel_risk))
df_f = df[mask].copy()

# ── 헤더 바 ───────────────────────────────────────────────────────────────────
n_d  = (df_f['risk_grade']=='위험').sum()
n_vt = ((df_f['risk_grade']=='위험') & (df_f['val_grade']=='저평가')).sum()
n_buy= (df_f['final_signal']=='★진성 저평가').sum()

st.markdown(f"""
<div class="top-bar">
  <div class="top-title">◼ EQUITY VALUATION SCREENER</div>
  <div class="top-item">COVERAGE <b>{len(df_f):,}</b></div>
  <div class="top-item">YEARS <b>{','.join(map(str,sorted(sel_year)))}</b></div>
  <div class="top-item down">DANGER <b>{n_d}</b></div>
  <div class="top-item">VALUE TRAP <b>{n_vt}</b></div>
  <div class="top-item up">BUY SIGNAL <b>{n_buy}</b></div>
  <div class="top-item up">ρ <b>+0.1328***</b></div>
</div>
""", unsafe_allow_html=True)

tot = len(df_f) or 1
n_w = (df_f['risk_grade']=='주의').sum()
n_n = (df_f['risk_grade']=='정상').sum()

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-cell kpi-danger"><div class="kpi-label">위험</div><div class="kpi-value">{n_d}</div><div class="kpi-sub">{n_d/tot*100:.1f}%</div></div>
  <div class="kpi-cell kpi-caution"><div class="kpi-label">주의</div><div class="kpi-value">{n_w}</div><div class="kpi-sub">{n_w/tot*100:.1f}%</div></div>
  <div class="kpi-cell kpi-safe"><div class="kpi-label">정상</div><div class="kpi-value">{n_n}</div><div class="kpi-sub">{n_n/tot*100:.1f}%</div></div>
  <div class="kpi-cell kpi-danger"><div class="kpi-label">Value Trap</div><div class="kpi-value">{n_vt}</div><div class="kpi-sub">위험×저평가</div></div>
  <div class="kpi-cell kpi-safe"><div class="kpi-label">진성 저평가</div><div class="kpi-value">{n_buy}</div><div class="kpi-sub">BUY 신호</div></div>
  <div class="kpi-cell kpi-blue"><div class="kpi-label">Avg PBR</div><div class="kpi-value">{df_f["pbr"].median():.2f}</div><div class="kpi-sub">중앙값</div></div>
</div>
""", unsafe_allow_html=True)

# ── 탭 ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(['OVERVIEW', 'SCREENER', 'REPORT', 'VALUATION MAP'])

# ══ OVERVIEW ══
with tab1:
    c1, c2 = st.columns(2, gap='small')
    with c1:
        # 9칸 매트릭스
        st.markdown('<div class="panel"><div class="ph">RISK × VALUATION MATRIX <b>전체 합산</b></div><div class="pb">', unsafe_allow_html=True)
        risk3 = ['위험','주의','정상']
        val3  = ['고평가','적정','저평가']
        rows_html = '<table style="width:100%;border-collapse:collapse;font-size:11px"><thead><tr><th style="background:#0A1628;color:#5A7A9F;padding:5px 8px;font-size:9px;letter-spacing:0.1em"></th>'
        for v in val3:
            rows_html += f'<th style="background:#0A1628;color:#5A7A9F;padding:5px 8px;font-size:9px;letter-spacing:0.1em;text-align:center">{v}</th>'
        rows_html += '</tr></thead><tbody>'
        BG = {('위험','고평가'):'#FFF0F0',('위험','적정'):'#FFF6EE',('위험','저평가'):'#FFFDE8',
              ('주의','고평가'):'#FFF6EE',('주의','적정'):'#F8F8F5',('주의','저평가'):'#EDFAF5',
              ('정상','고평가'):'#EEF4FF',('정상','적정'):'#F8F8F5',('정상','저평가'):'#E8F8F0'}
        FC = {('위험','고평가'):'#E04040',('위험','적정'):'#CC8800',('위험','저평가'):'#AA8800',
              ('주의','고평가'):'#CC8800',('주의','적정'):'#666660',('주의','저평가'):'#007A45',
              ('정상','고평가'):'#0044AA',('정상','적정'):'#666660',('정상','저평가'):'#006633'}
        for r in risk3:
            rows_html += f'<tr><th style="background:#0A1628;color:#5A7A9F;font-size:9px;padding:5px 8px;text-align:left">{r}</th>'
            for v in val3:
                n   = ((df_f['risk_grade']==r)&(df_f['val_grade']==v)).sum()
                lbl = MATRIX.get((r,v),'')
                bg  = BG.get((r,v),'#FFFFFF')
                fc  = FC.get((r,v),'#333')
                rows_html += f'<td style="border:1px solid #E0E0D8;padding:8px 10px;text-align:center;background:{bg}"><span style="font-size:20px;font-weight:500;color:{fc};display:block;line-height:1">{n}</span><span style="font-size:9px;color:{fc};display:block;margin-top:2px">{lbl}</span></td>'
            rows_html += '</tr>'
        rows_html += '</tbody></table>'
        st.markdown(rows_html + '</div></div>', unsafe_allow_html=True)

        # val_grade 추이
        st.markdown('<div class="panel"><div class="ph">VAL GRADE TREND <b>연도별 등급 분포</b></div><div class="pb">', unsafe_allow_html=True)
        trend = df.groupby(['year','val_grade']).size().reset_index(name='n')
        fig_t = px.bar(trend, x='year', y='n', color='val_grade',
                       color_discrete_map={'고평가':'#E05454','적정':'#888880','저평가':'#2E8B5A'},
                       barmode='stack', labels={'year':'','n':'','val_grade':''})
        fig_t.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
                            height=200, bargap=0.3, margin=dict(l=4,r=4,t=4,b=4),
                            font=dict(family='IBM Plex Sans,Malgun Gothic',size=11),
                            yaxis=dict(gridcolor='#EEEEEA'),
                            legend=dict(orientation='h',y=1.12,font=dict(size=10)))
        fig_t.update_traces(marker_line_width=0)
        st.plotly_chart(fig_t, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with c2:
        # 신호 breakdown
        st.markdown('<div class="panel"><div class="ph">FINAL SIGNAL BREAKDOWN</div><div class="pb">', unsafe_allow_html=True)
        sig_cnt = df_f['final_signal'].value_counts().reset_index()
        sig_cnt.columns = ['signal','count']
        sig_color = {
            '★진성 저평가':'#2E8B5A','기회 or Trap':'#4A9F70','과열 주의':'#4A6FBF',
            '관망':'#888880','관찰 필요':'#AA9900','회피 검토':'#CC6600',
            '⚠Value Trap':'#E07800','⚠재무위험':'#CC3300','⚠즉시 회피':'#E04040',
        }
        fig_s = px.bar(sig_cnt, x='count', y='signal', orientation='h',
                       color='signal', color_discrete_map=sig_color,
                       labels={'count':'','signal':''})
        fig_s.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
                            height=250, showlegend=False, margin=dict(l=4,r=4,t=4,b=4),
                            font=dict(family='IBM Plex Sans,Malgun Gothic',size=11),
                            xaxis=dict(gridcolor='#EEEEEA'))
        fig_s.update_traces(marker_line_width=0)
        st.plotly_chart(fig_s, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # val_score 박스
        st.markdown('<div class="panel"><div class="ph">CLUSTER DISTRIBUTION <b>val_score</b></div><div class="pb">', unsafe_allow_html=True)
        fig_b = px.box(df_f, x='cluster_label', y='val_score', color='cluster_label',
                       color_discrete_sequence=['#E05454','#2E8B5A','#4A6FBF','#CC8800','#7B5EA7','#888880'],
                       labels={'cluster_label':'','val_score':'val_score'}, points='outliers')
        fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
                            height=200, showlegend=False, margin=dict(l=4,r=4,t=4,b=4),
                            font=dict(family='IBM Plex Sans,Malgun Gothic',size=11),
                            yaxis=dict(gridcolor='#EEEEEA'))
        fig_b.update_traces(marker_size=3, line_width=1.2)
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

# ══ SCREENER ══
with tab2:
    fc1, fc2, fc3 = st.columns([2,2,1])
    with fc1:
        sort_col = st.selectbox('SORT BY', [c for c in ['val_score','prob_저평가','anomaly_score','pbr','momentum_12m'] if c in df_f.columns])
    with fc2:
        sig_filter = st.multiselect('SIGNAL', df_f['final_signal'].unique().tolist(), default=df_f['final_signal'].unique().tolist())
    with fc3:
        top_n = st.number_input('TOP N', 10, 500, 100, step=10)

    df_sc = df_f[df_f['final_signal'].isin(sig_filter)].sort_values(sort_col, ascending=False).head(int(top_n))
    show  = [c for c in ['corp_name','stock_code','year','cluster_label','risk_grade','val_grade',
                          'final_signal','val_score','prob_저평가','anomaly_score',
                          'pbr','per','ev_ebitda','momentum_12m','lgbm_pred_name'] if c in df_sc.columns]
    fmt   = {k:v for k,v in {'ValScore':'{:.3f}','P(저평가)':'{:.3f}','AnomalyScore':'{:.3f}',
                              'PBR':'{:.2f}','PER':'{:.1f}','EV/EBITDA':'{:.1f}','12M Rtn':'{:.1%}'}.items()}

    def style_risk(val):
        return {'위험':'color:#E04040;font-weight:600','주의':'color:#CC8800;font-weight:600',
                '정상':'color:#00A862'}.get(str(val),'')
    def style_sig(val):
        if '저평가' in str(val) and '★' in str(val): return 'color:#00A862;font-weight:600'
        if '⚠' in str(val): return 'color:#E04040;font-weight:600'
        return ''

    tbl    = df_sc[show].rename(columns=RENAME)
    styled = tbl.style.format({k:v for k,v in fmt.items() if k in tbl.columns}, na_rep='-')
    if 'Risk' in tbl.columns:     styled = styled.map(style_risk, subset=['Risk'])
    if 'Signal' in tbl.columns:   styled = styled.map(style_sig,  subset=['Signal'])
    st.dataframe(styled, use_container_width=True, height=520)

    # Value Trap watchlist
    vt = df_f[(df_f['risk_grade']=='위험') & (df_f['val_grade']=='저평가')]
    if not vt.empty:
        st.markdown(f'<div class="panel"><div class="ph" style="background:#3A0A0A">⚠ VALUE TRAP WATCHLIST <b>{len(vt)} NAMES</b></div><div class="pb">', unsafe_allow_html=True)
        vt_cols = [c for c in ['corp_name','stock_code','year','cluster_label','val_score','pbr','per','momentum_12m'] if c in vt.columns]
        vt_fmt  = {k:v for k,v in {'ValScore':'{:.3f}','PBR':'{:.2f}','PER':'{:.1f}','12M Rtn':'{:.1%}'}.items()}
        st.dataframe(vt.sort_values('val_score', ascending=False)[vt_cols].rename(columns=RENAME)
                     .style.format(vt_fmt, na_rep='-'), use_container_width=True, height=280)
        st.markdown('</div></div>', unsafe_allow_html=True)

# ══ REPORT ══
with tab3:
    q_col, _ = st.columns([2,3])
    with q_col:
        query = st.text_input('', placeholder='종목코드 또는 기업명 입력 (예: 삼성전자 / 005930)')

    sel_corp = None
    if query:
        mask_q = (df['stock_code'].str.contains(query, na=False))
        if 'corp_name' in df.columns:
            mask_q = mask_q | df['corp_name'].str.contains(query, na=False)
        hits = df[mask_q]['corp_name'].unique() if 'corp_name' in df.columns else df[mask_q]['stock_code'].unique()
        if len(hits) == 0:
            st.warning('검색 결과 없음')
        elif len(hits) == 1:
            sel_corp = hits[0]
        else:
            sel_corp = st.selectbox('기업 선택', hits)

    if sel_corp:
        key_col = 'corp_name' if 'corp_name' in df.columns else 'stock_code'
        dc      = df[df[key_col] == sel_corp].sort_values('year')
        latest  = dc.iloc[-1]
        code    = dc['stock_code'].iloc[0]
        cluster = latest.get('cluster_label', '-')
        signal  = latest.get('final_signal', '기타')
        opinion, op_cls = OPINION_MAP.get(signal, ('NEUTRAL','op-watch'))

        # 헤더
        st.markdown(f"""
        <div class="report-header">
          <div>
            <div class="report-ticker">{code}</div>
            <div class="report-name">{sel_corp} · {cluster}</div>
          </div>
          <div class="report-opinion {op_cls}">{opinion}</div>
        </div>
        """, unsafe_allow_html=True)

        # 핵심 KPI
        def fmt_val(col, fmt):
            v = latest.get(col, None)
            return fmt.format(v) if pd.notna(v) else 'N/A'

        st.markdown(f"""
        <div class="report-kpi">
          <div class="report-kpi-cell"><div class="report-kpi-label">PBR</div><div class="report-kpi-value">{fmt_val('pbr','{:.2f}')}</div></div>
          <div class="report-kpi-cell"><div class="report-kpi-label">PER</div><div class="report-kpi-value">{fmt_val('per','{:.1f}x')}</div></div>
          <div class="report-kpi-cell"><div class="report-kpi-label">EV/EBITDA</div><div class="report-kpi-value">{fmt_val('ev_ebitda','{:.1f}x')}</div></div>
          <div class="report-kpi-cell"><div class="report-kpi-label">12M RETURN</div><div class="report-kpi-value">{fmt_val('momentum_12m','{:.1%}')}</div></div>
          <div class="report-kpi-cell"><div class="report-kpi-label">VAL SCORE</div><div class="report-kpi-value">{fmt_val('val_score','{:.3f}')}</div></div>
        </div>
        """, unsafe_allow_html=True)

        r1, r2 = st.columns(2, gap='small')

        with r1:
            # 시그널 요약
            st.markdown('<div style="background:#FFFFFF;border:1px solid #D0D0C8;padding:10px 14px;margin-bottom:8px">'
                        '<div style="font-size:9px;font-weight:600;color:#5A7A9F;letter-spacing:0.14em;text-transform:uppercase;border-bottom:1px solid #E8E8E0;padding-bottom:4px;margin-bottom:8px">VALUATION SIGNAL</div>',
                        unsafe_allow_html=True)
            items = [
                ('Risk Grade',    latest.get('risk_grade','-')),
                ('Val Grade',     latest.get('val_grade','-')),
                ('Final Signal',  signal),
                ('Investment Op.', opinion),
                ('LGBM Pred',     latest.get('lgbm_pred_name','-')),
                ('P(저평가)',      f"{latest.get('prob_저평가',0):.1%}" if pd.notna(latest.get('prob_저평가')) else 'N/A'),
                ('Anomaly Grade', latest.get('anomaly_grade','-')),
                ('Cluster',       cluster),
            ]
            rows = ''.join([f'<div class="signal-row"><span class="signal-label">{k}</span><span class="signal-value">{v}</span></div>' for k,v in items])
            st.markdown(rows + '</div>', unsafe_allow_html=True)

        with r2:
            # 점수 추이 차트
            st.markdown('<div style="background:#FFFFFF;border:1px solid #D0D0C8;padding:10px 14px">'
                        '<div style="font-size:9px;font-weight:600;color:#5A7A9F;letter-spacing:0.14em;text-transform:uppercase;border-bottom:1px solid #E8E8E0;padding-bottom:4px;margin-bottom:8px">SCORE HISTORY</div>',
                        unsafe_allow_html=True)
            fig_h = go.Figure()
            for col_name, label, color, dash in [
                ('val_score',     'Val Score',    '#0066FF', 'solid'),
                ('anomaly_score', 'Anomaly',      '#E04040', 'dash'),
                ('prob_저평가',   'P(저평가)',    '#00A862', 'dot'),
            ]:
                if col_name in dc.columns:
                    fig_h.add_trace(go.Scatter(
                        x=dc['year'], y=dc[col_name], name=label, mode='lines+markers',
                        line=dict(color=color, width=1.8, dash=dash),
                        marker=dict(size=6, color=color)))
            fig_h.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
                height=210, margin=dict(l=4,r=4,t=4,b=4),
                font=dict(family='IBM Plex Sans,Malgun Gothic', size=10),
                legend=dict(orientation='h', y=1.12, font=dict(size=9)),
                yaxis=dict(gridcolor='#EEEEEA'),
                xaxis=dict(tickfont=dict(family='IBM Plex Mono')))
            st.plotly_chart(fig_h, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 배수 레이더 (군집 내 상대 위치)
        yr_latest = int(latest.get('year', df['year'].max()))
        peer = df[(df['cluster_label']==cluster) & (df['year']==yr_latest)]
        radar_feats = ['pbr','per','ev_ebitda','psr','momentum_12m']
        radar_feats = [f for f in radar_feats if f in peer.columns]
        if len(radar_feats) >= 3 and len(peer) > 5:
            ranks = {}
            for f in radar_feats:
                pct = peer[f].rank(pct=True, na_option='keep')
                idx = dc[dc['year']==yr_latest].index
                if len(idx) > 0 and idx[0] in pct.index:
                    r = pct.loc[idx[0]]
                    ranks[f] = 1 - r if pd.notna(r) else 0.5  # 낮을수록 저평가 → 역순
            if ranks:
                st.markdown('<div style="background:#FFFFFF;border:1px solid #D0D0C8;padding:10px 14px;margin-top:8px">'
                            '<div style="font-size:9px;font-weight:600;color:#5A7A9F;letter-spacing:0.14em;text-transform:uppercase;border-bottom:1px solid #E8E8E0;padding-bottom:4px;margin-bottom:8px">PEER RELATIVE POSITION (군집 내 저평가 상대 위치, 높을수록 저평가)</div>',
                            unsafe_allow_html=True)
                fig_r = go.Figure(go.Scatterpolar(
                    r=list(ranks.values()), theta=list(ranks.keys()),
                    fill='toself', fillcolor='rgba(46,139,90,0.15)',
                    line=dict(color='#2E8B5A', width=2)))
                fig_r.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0,1])),
                    paper_bgcolor='rgba(0,0,0,0)', height=250,
                    margin=dict(l=40,r=40,t=20,b=20),
                    font=dict(family='IBM Plex Sans,Malgun Gothic', size=10))
                st.plotly_chart(fig_r, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # 연도별 히스토리
        st.markdown('<div style="background:#FFFFFF;border:1px solid #D0D0C8;padding:10px 14px;margin-top:8px">'
                    '<div style="font-size:9px;font-weight:600;color:#5A7A9F;letter-spacing:0.14em;text-transform:uppercase;border-bottom:1px solid #E8E8E0;padding-bottom:4px;margin-bottom:8px">ANNUAL HISTORY</div>',
                    unsafe_allow_html=True)
        h_cols = [c for c in ['year','cluster_label','risk_grade','val_grade','final_signal',
                               'val_score','pbr','per','ev_ebitda','momentum_12m'] if c in dc.columns]
        h_fmt  = {k:v for k,v in {'ValScore':'{:.3f}','PBR':'{:.2f}','PER':'{:.1f}','EV/EBITDA':'{:.1f}','12M Rtn':'{:.1%}'}.items()}
        st.dataframe(dc[h_cols].rename(columns=RENAME).style.format(h_fmt, na_rep='-'),
                     use_container_width=True, hide_index=True, height=180)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown('<div style="padding:80px 0;text-align:center;color:#5A7A9F;font-size:11px;letter-spacing:0.1em">ENTER TICKER OR COMPANY NAME TO GENERATE REPORT</div>', unsafe_allow_html=True)

# ══ VALUATION MAP ══
with tab4:
    v1, v2 = st.columns([1,3])
    with v1:
        sc_year = st.selectbox('YEAR', sorted(df['year'].unique(), reverse=True), key='sc_yr')

    df_v = df[(df['year']==sc_year) & df['pbr'].notna() & df['momentum_12m'].notna()].copy()
    # 상위 1% PBR 제거
    df_v = df_v[df_v['pbr'] < df_v['pbr'].quantile(0.97)]

    top30 = df_v.nlargest(30,'val_score').index
    df_v['구분'] = '일반'
    df_v.loc[top30, '구분'] = 'Top 30'
    df_v.loc[(df_v['risk_grade']=='위험')&(df_v['val_grade']=='저평가'), '구분'] = 'Value Trap'

    st.markdown('<div class="panel"><div class="ph">PBR vs 12M RETURN · VALUATION MAP</div><div class="pb">', unsafe_allow_html=True)
    CL_COLOR = {'EHS':'#E05454','HS':'#2E8B5A','NG':'#4A6FBF','LR':'#CC8800','WG':'#7B5EA7','FD':'#888880'}
    hover_data = ['stock_code','risk_grade','val_grade','val_score','final_signal']
    if 'corp_name' in df_v.columns:
        hover_data = ['corp_name'] + hover_data
    fig_v = px.scatter(df_v, x='pbr', y='momentum_12m',
                       color='cluster_label', symbol='구분',
                       symbol_map={'일반':'circle','Top 30':'star','Value Trap':'x'},
                       size='val_score', size_max=16,
                       color_discrete_map=CL_COLOR,
                       hover_data=hover_data,
                       labels={'pbr':'PBR','momentum_12m':'12M Return','cluster_label':''},
                       opacity=0.72)
    fig_v.add_hline(y=0,  line_dash='dot', line_color='#CCCCCA', line_width=1)
    fig_v.add_vline(x=1,  line_dash='dot', line_color='#CCCCCA', line_width=1)
    fig_v.add_shape(type='rect', x0=0, x1=1, y0=-2, y1=0,
                    fillcolor='rgba(46,139,90,0.04)', line=dict(width=0))
    fig_v.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
        height=460, margin=dict(l=8,r=8,t=8,b=8),
        font=dict(family='IBM Plex Sans,Malgun Gothic', size=11),
        yaxis=dict(tickformat='.0%', gridcolor='#EEEEEA'),
        xaxis=dict(gridcolor='#EEEEEA'),
        legend=dict(font=dict(size=10), x=1.01))
    st.plotly_chart(fig_v, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Top 30
    t30 = df_v.loc[top30].sort_values('val_score', ascending=False)
    st.markdown(f'<div class="panel"><div class="ph">TOP 30 BY VAL SCORE · {sc_year} <b>{len(t30)} NAMES</b></div><div class="pb">', unsafe_allow_html=True)
    t_cols = [c for c in ['corp_name','stock_code','cluster_label','risk_grade','val_grade',
                           'final_signal','val_score','pbr','per','ev_ebitda','momentum_12m'] if c in t30.columns]
    t_fmt  = {k:v for k,v in {'ValScore':'{:.3f}','PBR':'{:.2f}','PER':'{:.1f}','EV/EBITDA':'{:.1f}','12M Rtn':'{:.1%}'}.items()}
    st.dataframe(t30[t_cols].rename(columns=RENAME).style.format(t_fmt, na_rep='-'),
                 use_container_width=True, height=380)
    st.markdown('</div></div>', unsafe_allow_html=True)
