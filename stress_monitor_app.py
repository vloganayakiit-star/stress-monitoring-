"""
IoT-Based Smart Academic Stress & Health Monitoring System
Streamlit Implementation based on the research paper by Ms. S. Sharu et al.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Academic Stress Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #ffffff 0%, #f0f4f8 50%, #e8edf5 100%);
color: #1e293b;
}

/* Sidebar */
section[data-testid="stSidebar"] {
background: rgba(240, 244, 248, 0.98) !important;
border-right: 1px solid rgba(99, 130, 180, 0.2);
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(99, 179, 237, 0.2);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
}
.metric-label {
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-top: 6px;
}
.metric-unit {
    font-size: 0.85rem;
    color: #64748b;
    font-family: 'Space Mono', monospace;
}

/* Stress badge */
.badge-normal    { color: #4ade80; border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.08); }
.badge-moderate  { color: #fbbf24; border-color: rgba(251,191,36,0.3);  background: rgba(251,191,36,0.08); }
.badge-high      { color: #f87171; border-color: rgba(248,113,113,0.3); background: rgba(248,113,113,0.08); }
.stress-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 999px;
    border: 1px solid;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
}

/* Alert box */
.alert-box {
    background: rgba(248,113,113,0.1);
    border: 1px solid rgba(248,113,113,0.4);
    border-left: 4px solid #f87171;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #fca5a5;
    font-size: 0.88rem;
}
.info-box {
    background: rgba(99,179,237,0.08);
    border: 1px solid rgba(99,179,237,0.25);
    border-left: 4px solid #63b3ed;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #93c5fd;
    font-size: 0.88rem;
}

/* Section headers */
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #3b6cb7;

    margin: 24px 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(99,179,237,0.2);
}

/* Table styling */
.dataframe { font-size: 0.85rem !important; }

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CORE LOGIC — from the paper
# ─────────────────────────────────────────────
W1, W2, W3 = 0.5, 0.3, 0.2
HR_THRESHOLD = 100  # BPM

def compute_stress_index(hr, temp, ad):
    """Weighted Stress Index from the paper: SI = W1*HR + W2*Temp + W3*AD"""
    return round(W1 * hr + W2 * temp + W3 * ad, 2)

def classify_stress(hr, si):
    """Threshold-based classification from the paper."""
    if hr > HR_THRESHOLD or si > 60:
        return "High Stress", "badge-high", "🔴"
    elif hr > 88 or si > 50:
        return "Moderate", "badge-moderate", "🟡"
    else:
        return "Normal", "badge-normal", "🟢"

def accuracy_metrics():
    """Return paper's reported evaluation metrics."""
    return {
        "Accuracy":  87.5,
        "Precision": 85.2,
        "Recall":    82.4,
        "F1-Score":  83.7,
    }


# ─────────────────────────────────────────────
# SIMULATION — generate realistic student data
# ─────────────────────────────────────────────
SESSION_PROFILES = {
    "Normal Study":       {"hr_mean": 78,  "hr_std": 5,  "temp_mean": 36.6, "temp_std": 0.3, "ad_mean": 0.3},
    "Assignment Work":    {"hr_mean": 92,  "hr_std": 6,  "temp_mean": 36.9, "temp_std": 0.3, "ad_mean": 0.6},
    "Exam Preparation":   {"hr_mean": 105, "hr_std": 8,  "temp_mean": 37.2, "temp_std": 0.4, "ad_mean": 0.8},
    "Relaxation":         {"hr_mean": 74,  "hr_std": 4,  "temp_mean": 36.4, "temp_std": 0.2, "ad_mean": 0.1},
}

def generate_sample(session: str):
    p = SESSION_PROFILES[session]
    hr   = max(55, min(150, np.random.normal(p["hr_mean"], p["hr_std"])))
    temp = max(35.5, min(38.5, np.random.normal(p["temp_mean"], p["temp_std"])))
    ad   = max(0, min(1, np.random.normal(p["ad_mean"], 0.1)))
    return round(hr, 1), round(temp, 2), round(ad, 3)

def generate_historical_data(n_students=20, n_days=7):
    """Generate synthetic dataset matching paper's 84,000-record dataset."""
    records = []
    base_time = datetime.now() - timedelta(days=n_days)
    sessions  = list(SESSION_PROFILES.keys())
    for student_id in range(1, n_students + 1):
        for day in range(n_days):
            for hour in range(6):
                session = sessions[(hour + day) % len(sessions)]
                for _ in range(100):  # ~100 readings/hour
                    t = base_time + timedelta(days=day, hours=hour, seconds=random.randint(0, 3600))
                    hr, temp, ad = generate_sample(session)
                    si = compute_stress_index(hr, temp, ad)
                    label, _, _ = classify_stress(hr, si)
                    records.append({
                        "student_id": f"S{student_id:02d}",
                        "timestamp": t,
                        "session": session,
                        "heart_rate": hr,
                        "temperature": temp,
                        "activity_deviation": ad,
                        "stress_index": si,
                        "stress_level": label,
                    })
    return pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "live_data"    not in st.session_state: st.session_state.live_data    = []
if "alerts"       not in st.session_state: st.session_state.alerts       = []
if "monitoring"   not in st.session_state: st.session_state.monitoring   = False
if "hist_df"      not in st.session_state: st.session_state.hist_df      = None
if "tick"         not in st.session_state: st.session_state.tick         = 0


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 Stress Monitor")
    st.markdown("<div style='color:#64748b;font-size:0.78rem;margin-bottom:16px;'>IoT-Based Academic Health System</div>", unsafe_allow_html=True)
    st.divider()

    page = st.radio("Navigation", ["📡 Live Monitor", "📊 Data Analysis", "📐 Methodology", "📈 Model Evaluation"], label_visibility="collapsed")

    st.divider()
    st.markdown("<div class='section-header'>Simulation Settings</div>", unsafe_allow_html=True)
    selected_session = st.selectbox("Session Type", list(SESSION_PROFILES.keys()))
    student_id       = st.selectbox("Student ID", [f"S{i:02d}" for i in range(1, 21)])
    refresh_rate     = st.slider("Refresh interval (s)", 1, 5, 2)

    st.divider()
    st.markdown("<div class='section-header'>System Info</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.78rem;color:#64748b;line-height:1.8;'>
    🔧 Edge Device: ESP32<br>
    📡 Protocol: MQTT/HTTP<br>
    ☁️ Cloud: Dashboard<br>
    🎓 Students: 20<br>
    📅 Duration: 7 days
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE: LIVE MONITOR
# ─────────────────────────────────────────────
if "Live Monitor" in page:
    st.markdown("## 📡 Real-Time Physiological Monitoring")
    st.markdown("<div style='color:#64748b;font-size:0.88rem;margin-bottom:20px;'>Simulating ESP32 edge device → Cloud pipeline as described in the paper</div>", unsafe_allow_html=True)

    col_start, col_stop, col_clear = st.columns([1, 1, 4])
    with col_start:
        if st.button("▶ Start", use_container_width=True, type="primary"):
            st.session_state.monitoring = True
    with col_stop:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.monitoring = False

    if st.session_state.monitoring:
        hr, temp, ad = generate_sample(selected_session)
        si = compute_stress_index(hr, temp, ad)
        label, badge_cls, emoji = classify_stress(hr, si)
        ts = datetime.now()

        st.session_state.live_data.append({
            "time": ts, "hr": hr, "temp": temp, "ad": ad, "si": si, "label": label
        })
        if len(st.session_state.live_data) > 120:
            st.session_state.live_data = st.session_state.live_data[-120:]

        if label == "High Stress":
            st.session_state.alerts.append(f"[{ts.strftime('%H:%M:%S')}] ⚠️ {student_id} — HR={hr} BPM | SI={si} | {selected_session}")
            if len(st.session_state.alerts) > 10:
                st.session_state.alerts = st.session_state.alerts[-10:]

        # ── Metric cards ──
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        hr_color   = "#f87171" if hr > HR_THRESHOLD else "#4ade80"
        temp_color = "#fbbf24" if temp > 37.2 else "#4ade80"
        ad_color   = "#fbbf24" if ad > 0.6 else "#4ade80"
        si_color   = "#f87171" if si > 60 else ("#fbbf24" if si > 50 else "#4ade80")

        with c1:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='color:{hr_color}'>{hr}</div>
                <div class='metric-unit'>BPM</div>
                <div class='metric-label'>Heart Rate</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='color:{temp_color}'>{temp}</div>
                <div class='metric-unit'>°C</div>
                <div class='metric-label'>Body Temperature</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='color:{ad_color}'>{ad:.3f}</div>
                <div class='metric-unit'>normalized</div>
                <div class='metric-label'>Activity Deviation</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='color:{si_color}'>{si}</div>
                <div class='metric-unit'>index</div>
                <div class='metric-label'>Stress Index (SI)</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"<br><center><span class='stress-badge {badge_cls}'>{emoji} {label}</span></center><br>", unsafe_allow_html=True)

        # ── Live chart ──
        if len(st.session_state.live_data) > 2:
            df_live = pd.DataFrame(st.session_state.live_data)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                subplot_titles=("Heart Rate (BPM)", "Body Temperature (°C)", "Stress Index"),
                                vertical_spacing=0.08)
            fig.add_trace(go.Scatter(x=df_live["time"], y=df_live["hr"], mode="lines",
                                     line=dict(color="#63b3ed", width=2), name="HR"), row=1, col=1)
            fig.add_hline(y=HR_THRESHOLD, line=dict(color="#f87171", dash="dash", width=1),
                          annotation_text="Threshold", row=1, col=1)
            fig.add_trace(go.Scatter(x=df_live["time"], y=df_live["temp"], mode="lines",
                                     line=dict(color="#fbbf24", width=2), name="Temp"), row=2, col=1)
            colors = ["#f87171" if l == "High Stress" else ("#fbbf24" if l == "Moderate" else "#4ade80")
                      for l in df_live["label"]]
            fig.add_trace(go.Scatter(x=df_live["time"], y=df_live["si"], mode="lines+markers",
                                     line=dict(color="#a78bfa", width=2),
                                     marker=dict(color=colors, size=5), name="SI"), row=3, col=1)
            fig.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                               font=dict(color="#94a3b8", size=11), showlegend=False,
                               margin=dict(l=10, r=10, t=40, b=10))
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", zeroline=False)
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", zeroline=False)
            st.plotly_chart(fig, use_container_width=True)

        # ── Alerts ──
        if st.session_state.alerts:
            st.markdown("<div class='section-header'>Recent Alerts</div>", unsafe_allow_html=True)
            for a in reversed(st.session_state.alerts[-5:]):
                st.markdown(f"<div class='alert-box'>{a}</div>", unsafe_allow_html=True)

        time.sleep(refresh_rate)
        st.rerun()

    else:
        st.markdown("<div class='info-box'>▶ Press <b>Start</b> to begin simulation. The ESP32 edge device will sample sensors and compute the Stress Index in real time.</div>", unsafe_allow_html=True)
        # Show formula preview
        st.markdown("---")
        st.markdown("#### Stress Index Formula (from paper)")
        st.latex(r"SI = (W_1 \times HR) + (W_2 \times Temp) + (W_3 \times AD)")
        st.latex(r"W_1 = 0.5,\quad W_2 = 0.3,\quad W_3 = 0.2")
        st.markdown("**Decision Rule:** `HR > 100 BPM` → High Stress Alert")


# ─────────────────────────────────────────────
# PAGE: DATA ANALYSIS
# ─────────────────────────────────────────────
elif "Data Analysis" in page:
    st.markdown("## 📊 Dataset Analysis")
    st.markdown("<div style='color:#64748b;font-size:0.88rem;margin-bottom:20px;'>Synthetic dataset matching paper's 84,000 records — 20 students × 7 days × 6 hours/day</div>", unsafe_allow_html=True)

    if st.session_state.hist_df is None:
        with st.spinner("Generating dataset..."):
            st.session_state.hist_df = generate_historical_data()

    df = st.session_state.hist_df

    # Summary metrics
    total   = len(df)
    high_pct = round((df["stress_level"] == "High Stress").mean() * 100, 1)
    avg_hr  = round(df["heart_rate"].mean(), 1)
    avg_si  = round(df["stress_index"].mean(), 2)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, unit, label in zip(
        [c1, c2, c3, c4],
        [f"{total:,}", f"{avg_hr}", f"{avg_si}", f"{high_pct}%"],
        ["records", "BPM", "index", "of records"],
        ["Total Records", "Avg Heart Rate", "Avg Stress Index", "High Stress"]
    ):
        with col:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='color:#63b3ed'>{val}</div>
                <div class='metric-unit'>{unit}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Session comparison (matches paper Table 4.2) ──
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Average HR by Session Type")
        session_stats = df.groupby("session")["heart_rate"].mean().reset_index()
        session_stats.columns = ["Session", "Avg HR (BPM)"]
        session_stats["Avg HR (BPM)"] = session_stats["Avg HR (BPM)"].round(1)
        session_order = ["Relaxation", "Normal Study", "Assignment Work", "Exam Preparation"]
        session_stats["Session"] = pd.Categorical(session_stats["Session"], categories=session_order, ordered=True)
        session_stats = session_stats.sort_values("Session")

        colors_bar = ["#4ade80", "#63b3ed", "#fbbf24", "#f87171"]
        fig_bar = go.Figure(go.Bar(
            x=session_stats["Session"], y=session_stats["Avg HR (BPM)"],
            marker_color=colors_bar, text=session_stats["Avg HR (BPM)"],
            textposition="outside"
        ))
        fig_bar.add_hline(y=HR_THRESHOLD, line=dict(color="#f87171", dash="dash"), annotation_text="Threshold (100 BPM)")
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                               font=dict(color="#94a3b8"), yaxis_title="BPM",
                               margin=dict(l=10, r=10, t=20, b=10), height=320, showlegend=False)
        fig_bar.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig_bar.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown("#### Stress Level Distribution")
        dist = df["stress_level"].value_counts().reset_index()
        dist.columns = ["Level", "Count"]
        color_map = {"Normal": "#4ade80", "Moderate": "#fbbf24", "High Stress": "#f87171"}
        fig_pie = go.Figure(go.Pie(
            labels=dist["Level"], values=dist["Count"],
            marker=dict(colors=[color_map[l] for l in dist["Level"]]),
            hole=0.5, textinfo="label+percent"
        ))
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"),
                               margin=dict(l=10, r=10, t=20, b=10), height=320, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── HR distribution ──
    st.markdown("#### Heart Rate Distribution by Session")
    fig_box = go.Figure()
    session_colors = {"Normal Study": "#63b3ed", "Assignment Work": "#fbbf24",
                      "Exam Preparation": "#f87171", "Relaxation": "#4ade80"}
    for session in session_order:
        subset = df[df["session"] == session]["heart_rate"]
        fig_box.add_trace(go.Box(y=subset, name=session, marker_color=session_colors.get(session, "#94a3b8"),
                                  boxmean=True))
    fig_box.add_hline(y=HR_THRESHOLD, line=dict(color="#f87171", dash="dash", width=1.5),
                       annotation_text="High Stress Threshold")
    fig_box.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                           font=dict(color="#94a3b8"), yaxis_title="Heart Rate (BPM)",
                           margin=dict(l=10, r=10, t=20, b=10), height=340, showlegend=False)
    fig_box.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig_box.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_box, use_container_width=True)

    # ── Raw data table ──
    st.markdown("#### Sample Records")
    show_df = df[["timestamp", "student_id", "session", "heart_rate", "temperature",
                  "activity_deviation", "stress_index", "stress_level"]].head(50)
    show_df["timestamp"] = show_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(show_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# PAGE: METHODOLOGY
# ─────────────────────────────────────────────
elif "Methodology" in page:
    st.markdown("## 📐 System Methodology")

    tab1, tab2, tab3 = st.tabs(["Architecture", "Stress Index Calculator", "Dataset Info"])

    with tab1:
        st.markdown("### Multi-Layer IoT Architecture")
        layers = [
            ("🔵 Layer 1 — Sensing",       "Wearable sensors: MAX30102 (HR), DS18B20 (Temp), MPU6050 (Activity)\nSampling: HR @ 1/s, Temp @ 1/5s, Activity @ 1/s"),
            ("🟡 Layer 2 — Edge Processing","ESP32 microcontroller\nComputes SI = 0.5×HR + 0.3×Temp + 0.2×AD\nApplies threshold rule: HR > 100 BPM → High Stress"),
            ("🟠 Layer 3 — Communication",  "Wi-Fi transmission via MQTT / HTTP protocol\nData sent to cloud server in real time"),
            ("🔴 Layer 4 — Cloud Analytics","Data storage, visualization, trend analysis\nCloud dashboard with alert notifications"),
            ("🟢 Layer 5 — Application",    "Web dashboard for institutional monitoring\nReal-time stress status per student\nAutomated alert to users when SI exceeds threshold"),
        ]
        for title, desc in layers:
            with st.expander(title, expanded=True):
                st.markdown(f"<pre style='color:#94a3b8;font-size:0.85rem;background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;'>{desc}</pre>", unsafe_allow_html=True)

    with tab2:
        st.markdown("### Interactive Stress Index Calculator")
        st.markdown("<div class='info-box'>Enter sensor readings to compute SI and stress classification using the paper's weighted model.</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            hr_input   = st.slider("Heart Rate (BPM)", 55, 150, 85)
        with c2:
            temp_input = st.slider("Body Temperature (°C)", 35.5, 38.5, 36.7, step=0.1)
        with c3:
            ad_input   = st.slider("Activity Deviation", 0.0, 1.0, 0.3, step=0.01)

        si_result = compute_stress_index(hr_input, temp_input, ad_input)
        label, badge_cls, emoji = classify_stress(hr_input, si_result)

        st.markdown(f"""
        **Calculation:**
        > SI = (0.5 × {hr_input}) + (0.3 × {temp_input}) + (0.2 × {ad_input:.2f})
        > SI = {0.5*hr_input:.2f} + {0.3*temp_input:.2f} + {0.2*ad_input:.3f} = **{si_result}**
        """)
        st.markdown(f"<center><span class='stress-badge {badge_cls}'>{emoji} {label}</span></center>", unsafe_allow_html=True)

        # Weight breakdown
        fig_w = go.Figure(go.Bar(
            x=["Heart Rate\n(W₁=0.5)", "Temperature\n(W₂=0.3)", "Activity Deviation\n(W₃=0.2)"],
            y=[0.5 * hr_input, 0.3 * temp_input, 0.2 * ad_input],
            marker_color=["#63b3ed", "#fbbf24", "#a78bfa"],
            text=[f"{0.5*hr_input:.1f}", f"{0.3*temp_input:.1f}", f"{0.2*ad_input:.2f}"],
            textposition="outside"
        ))
        fig_w.update_layout(title="Weighted Component Contributions to SI",
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                             font=dict(color="#94a3b8"), margin=dict(l=10, r=10, t=40, b=10),
                             height=300, showlegend=False)
        fig_w.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_w, use_container_width=True)

    with tab3:
        st.markdown("### Dataset Description")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Participants**")
            st.table(pd.DataFrame({
                "Parameter": ["No. of students", "Age range", "Department", "Monitoring days", "Hours/day", "Total records"],
                "Value": ["20", "18–21 years", "Information Technology", "7", "6", "~84,000"]
            }))
        with col2:
            st.markdown("**Sensor Sampling Rates**")
            st.table(pd.DataFrame({
                "Parameter": ["Heart Rate", "Body Temperature", "Activity Deviation"],
                "Unit": ["BPM", "°C", "Normalized"],
                "Rate": ["1 / sec", "1 / 5 sec", "1 / sec"]
            }))
        st.markdown("**Session Types Monitored**")
        st.table(pd.DataFrame({
            "Session": ["Normal Study", "Assignment Work", "Exam Preparation", "Relaxation"],
            "Avg HR (BPM)": [78, 92, 105, 74],
            "Stress Status": ["Normal", "Moderate", "High Stress", "Normal"]
        }))


# ─────────────────────────────────────────────
# PAGE: MODEL EVALUATION
# ─────────────────────────────────────────────
elif "Model Evaluation" in page:
    st.markdown("## 📈 Model Evaluation")
    st.markdown("<div style='color:#64748b;font-size:0.88rem;margin-bottom:20px;'>Threshold-based classification performance as reported in the paper</div>", unsafe_allow_html=True)

    metrics = accuracy_metrics()

    # Gauge charts for each metric
    cols = st.columns(4)
    colors_gauge = {"Accuracy": "#63b3ed", "Precision": "#fbbf24", "Recall": "#a78bfa", "F1-Score": "#4ade80"}
    for col, (name, val) in zip(cols, metrics.items()):
        with col:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=val,
                title={"text": name, "font": {"size": 13, "color": "#94a3b8"}},
                number={"suffix": "%", "font": {"size": 22, "color": colors_gauge[name]}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#475569"},
                    "bar": {"color": colors_gauge[name]},
                    "bgcolor": "rgba(255,255,255,0.04)",
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [0, 60],  "color": "rgba(248,113,113,0.1)"},
                        {"range": [60, 80], "color": "rgba(251,191,36,0.1)"},
                        {"range": [80, 100],"color": "rgba(74,222,128,0.1)"},
                    ],
                }
            ))
            fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=200,
                                 margin=dict(l=20, r=20, t=40, b=10),
                                 font=dict(color="#94a3b8"))
            col.plotly_chart(fig_g, use_container_width=True)

    # Confusion matrix
    st.markdown("### Confusion Matrix (Estimated)")
    # Back-calculate from metrics (approximate for n=20 students)
    n = 160  # representative test samples
    tp = int(n * 0.875 * 0.852 / (0.852 + (1 - 0.824)))
    fp = int(tp * (1 / 0.852 - 1))
    fn = int(tp * (1 / 0.824 - 1))
    tn = n - tp - fp - fn

    cm = np.array([[tn, fp], [fn, tp]])
    fig_cm = go.Figure(go.Heatmap(
        z=cm, x=["Predicted Normal", "Predicted Stress"],
        y=["Actual Normal", "Actual Stress"],
        text=cm, texttemplate="%{text}",
        colorscale=[[0, "rgba(13,21,48,0.8)"], [1, "rgba(99,179,237,0.6)"]],
        showscale=False
    ))
    fig_cm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                          font=dict(color="#94a3b8", size=13),
                          margin=dict(l=80, r=40, t=20, b=60), height=300)
    st.plotly_chart(fig_cm, use_container_width=True)

    # Comparison vs baselines
    st.markdown("### Method Comparison")
    comp_df = pd.DataFrame({
        "Method": ["Questionnaire (baseline)", "Manual Observation", "Proposed IoT System (paper)", "IoT + ML (future)"],
        "Accuracy (%)": [62, 70, 87.5, 94],
        "Real-time": ["❌", "❌", "✅", "✅"],
        "Objective": ["❌", "❌", "✅", "✅"],
        "Automated": ["❌", "❌", "✅", "✅"],
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    fig_comp = go.Figure(go.Bar(
        x=comp_df["Method"], y=comp_df["Accuracy (%)"],
        marker_color=["#475569", "#64748b", "#63b3ed", "#4ade80"],
        text=comp_df["Accuracy (%)"].astype(str) + "%",
        textposition="outside"
    ))
    fig_comp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
                            font=dict(color="#94a3b8"), yaxis_title="Accuracy (%)", yaxis_range=[0, 100],
                            margin=dict(l=10, r=10, t=20, b=10), height=320, showlegend=False)
    fig_comp.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig_comp.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_comp, use_container_width=True)
