import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import LED_DATA, TEMPERATURES, CURRENTS

# ─── 페이지 설정 ───────────────────────────────────────────
st.set_page_config(
    page_title="LED I-V 특성 분석기",
    page_icon="💡",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stSelectbox label, .stMultiSelect label { font-weight: 600; }
    .result-box {
        background: #1e2130;
        border-radius: 10px;
        padding: 20px;
        margin: 8px 0;
        border-left: 4px solid #00e5ff;
    }
    .result-title {
        font-size: 13px;
        color: #888;
        margin-bottom: 4px;
    }
    .result-value {
        font-size: 26px;
        font-weight: 700;
        color: #00e5ff;
    }
    .result-unit {
        font-size: 14px;
        color: #aaa;
        margin-left: 4px;
    }
    h1 { color: #ffffff; }
    h2, h3 { color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# ─── 헤더 ──────────────────────────────────────────────────
st.title("💡 LED I-V 특성 분석기")
st.markdown("**데이터시트 기반 탐구 보고서** | 온도 변화에 따른 LED 전압-전류 특성 분석")
st.markdown("---")

# ─── 사이드바: 파라미터 선택 ────────────────────────────────
with st.sidebar:
    st.header("⚙️ 분석 파라미터 선택")
    st.markdown("아래 값을 선택하면 결과가 자동으로 업데이트됩니다.")

    st.subheader("① LED 종류 선택")
    selected_leds = st.multiselect(
        "비교할 LED 색깔 (복수 선택 가능)",
        options=list(LED_DATA.keys()),
        default=["적색 (Red)"]
    )

    st.subheader("② 온도 선택")
    selected_temps = st.multiselect(
        "비교할 온도 (°C)",
        options=TEMPERATURES,
        default=[-20, 25, 85],
        format_func=lambda x: f"{x}°C"
    )

    st.subheader("③ 기준 전류 선택")
    selected_current = st.selectbox(
        "결과값 계산 기준 전류 (mA)",
        options=CURRENTS,
        index=3,
        format_func=lambda x: f"{x} mA"
    )

    st.markdown("---")
    st.caption("📚 출처: Vishay 데이터시트, ResearchGate 논문 (RGB LED 온도 특성 연구)")

# ─── 입력 검증 ──────────────────────────────────────────────
if not selected_leds:
    st.warning("LED를 하나 이상 선택해주세요.")
    st.stop()
if not selected_temps:
    st.warning("온도를 하나 이상 선택해주세요.")
    st.stop()

# ─── 결과값 계산 ────────────────────────────────────────────
st.subheader(f"📊 분석 결과 — 기준 전류: {selected_current} mA")

cols = st.columns(len(selected_leds))

for idx, led_name in enumerate(selected_leds):
    led = LED_DATA[led_name]
    with cols[idx]:
        st.markdown(f"### {led_name}")
        st.markdown(f"소재: `{led['material']}` | 밴드갭: `{led['bandgap_ev']} eV`")

        vf_values = []
        for temp in selected_temps:
            vf = led["temp_data"][temp][selected_current]
            vf_values.append(vf)
            st.markdown(f"""
            <div class="result-box">
                <div class="result-title">{temp}°C 순방향 전압</div>
                <div class="result-value">{vf:.2f}<span class="result-unit">V</span></div>
            </div>
            """, unsafe_allow_html=True)

        # 온도 계수 계산 (선택된 온도 범위 내)
        if len(selected_temps) >= 2:
            t_min = min(selected_temps)
            t_max = max(selected_temps)
            vf_min = led["temp_data"][t_min][selected_current]
            vf_max = led["temp_data"][t_max][selected_current]
            delta_v = vf_max - vf_min
            delta_t = t_max - t_min
            coeff = (delta_v / delta_t) * 1000  # mV/°C
            st.markdown(f"""
            <div class="result-box" style="border-left-color: #ff6b35;">
                <div class="result-title">계산된 온도 계수</div>
                <div class="result-value" style="color:#ff6b35;">{coeff:.1f}<span class="result-unit">mV/°C</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="result-box" style="border-left-color: #7c3aed;">
                <div class="result-title">{t_min}°C → {t_max}°C 전압 변화량</div>
                <div class="result-value" style="color:#a78bfa;">{delta_v*1000:.0f}<span class="result-unit">mV</span></div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ─── 그래프 1: I-V 곡선 ─────────────────────────────────────
st.subheader("📈 I-V 특성 곡선")

fig_iv = go.Figure()

line_styles = ["solid", "dash", "dot", "dashdot"]
temp_style = {t: line_styles[i % len(line_styles)] for i, t in enumerate(selected_temps)}

for led_name in selected_leds:
    led = LED_DATA[led_name]
    for temp in selected_temps:
        vf_list = [led["temp_data"][temp][i] for i in CURRENTS]
        fig_iv.add_trace(go.Scatter(
            x=vf_list,
            y=CURRENTS,
            mode="lines+markers",
            name=f"{led_name} | {temp}°C",
            line=dict(color=led["color_hex"], dash=temp_style[temp], width=2.5),
            marker=dict(size=7),
            hovertemplate="전압: %{x:.2f}V<br>전류: %{y}mA<extra>" + f"{led_name} {temp}°C</extra>"
        ))

fig_iv.update_layout(
    template="plotly_dark",
    xaxis_title="순방향 전압 Vf (V)",
    yaxis_title="전류 I (mA)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
    margin=dict(l=40, r=20, t=40, b=40),
    plot_bgcolor="#1e2130",
    paper_bgcolor="#1e2130",
)
st.plotly_chart(fig_iv, use_container_width=True)

# ─── 그래프 2: 온도별 순방향 전압 비교 막대 ───────────────────
st.subheader(f"🌡️ 온도별 순방향 전압 비교 (전류: {selected_current} mA)")

fig_bar = go.Figure()

for led_name in selected_leds:
    led = LED_DATA[led_name]
    vf_vals = [led["temp_data"][t][selected_current] for t in selected_temps]
    fig_bar.add_trace(go.Bar(
        name=led_name,
        x=[f"{t}°C" for t in selected_temps],
        y=vf_vals,
        marker_color=led["color_hex"],
        text=[f"{v:.2f}V" for v in vf_vals],
        textposition="outside",
        hovertemplate="온도: %{x}<br>전압: %{y:.2f}V<extra>" + led_name + "</extra>"
    ))

fig_bar.update_layout(
    template="plotly_dark",
    barmode="group",
    xaxis_title="온도 (°C)",
    yaxis_title="순방향 전압 Vf (V)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400,
    margin=dict(l=40, r=20, t=40, b=40),
    plot_bgcolor="#1e2130",
    paper_bgcolor="#1e2130",
)
st.plotly_chart(fig_bar, use_container_width=True)

# ─── 그래프 3: 온도 계수 비교 ───────────────────────────────
if len(selected_leds) > 1 and len(selected_temps) >= 2:
    st.subheader("🔬 LED 색깔별 온도 계수 비교")

    coeff_list = []
    color_list = []
    for led_name in selected_leds:
        led = LED_DATA[led_name]
        t_min = min(selected_temps)
        t_max = max(selected_temps)
        vf_min = led["temp_data"][t_min][selected_current]
        vf_max = led["temp_data"][t_max][selected_current]
        coeff = ((vf_max - vf_min) / (t_max - t_min)) * 1000
        coeff_list.append(round(coeff, 2))
        color_list.append(led["color_hex"])

    fig_coeff = go.Figure(go.Bar(
        x=selected_leds,
        y=coeff_list,
        marker_color=color_list,
        text=[f"{c} mV/°C" for c in coeff_list],
        textposition="outside",
        hovertemplate="%{x}<br>온도 계수: %{y} mV/°C<extra></extra>"
    ))

    fig_coeff.update_layout(
        template="plotly_dark",
        yaxis_title="온도 계수 (mV/°C)",
        height=380,
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor="#1e2130",
        paper_bgcolor="#1e2130",
    )
    st.plotly_chart(fig_coeff, use_container_width=True)

# ─── 데이터 테이블 ──────────────────────────────────────────
st.subheader("📋 전체 데이터 테이블")

for led_name in selected_leds:
    led = LED_DATA[led_name]
    st.markdown(f"**{led_name}** (소재: {led['material']})")
    rows = []
    for temp in selected_temps:
        row = {"온도 (°C)": f"{temp}°C"}
        for cur in CURRENTS:
            row[f"{cur}mA"] = f"{led['temp_data'][temp][cur]:.2f}V"
        rows.append(row)
    df = pd.DataFrame(rows).set_index("온도 (°C)")
    st.dataframe(df, use_container_width=True)
    st.markdown("")

# ─── 고찰 자동 생성 ─────────────────────────────────────────
st.markdown("---")
st.subheader("📝 자동 분석 요약")

if len(selected_temps) >= 2:
    t_min = min(selected_temps)
    t_max = max(selected_temps)
    for led_name in selected_leds:
        led = LED_DATA[led_name]
        vf_low = led["temp_data"][t_min][selected_current]
        vf_high = led["temp_data"][t_max][selected_current]
        delta = (vf_low - vf_high) * 1000
        coeff = delta / (t_max - t_min)
        st.info(
            f"**{led_name}** ({led['material']}): "
            f"{t_min}°C → {t_max}°C 구간에서 순방향 전압이 "
            f"**{vf_low:.2f}V → {vf_high:.2f}V** 로 **{delta:.0f}mV** 감소하였으며, "
            f"온도 계수는 **{coeff:.1f} mV/°C** 입니다. "
            f"이는 온도 상승 시 밴드갭 에너지(약 {led['bandgap_ev']}eV) 감소로 인한 현상입니다."
        )

st.markdown("---")
st.caption("💡 본 앱은 고등학교 진로탐구 보고서용 데이터 분석 도구입니다. | 데이터 출처: Vishay 데이터시트, ResearchGate 논문")
