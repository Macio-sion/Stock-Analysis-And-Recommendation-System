"""智能股票推荐系统 - 前端展示页（Streamlit）。

运行：streamlit run app.py
覆盖后端全部功能点：市场概览 / 股票详情 / 完整推荐流程 / 数据接入 / 自定义算法 / 任务队列。
"""
import uuid
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.patches import Arc

from src.codegen.generator import generate_code
from src.codegen.validator import validate_code
from src.data.sentiment_client import fetch_sentiment
from src.data.tushare_client import client as tushare_client
from src.queue.service import get_status, submit_task
from src.queue.task_queue import dequeue_task
from src.queue.worker import _execute_task
from src.sandbox.executor import execute
from src.workflow.graph import graph

STRATEGY_TYPES = ["价值型", "成长型", "技术型", "情绪型", "均衡型", "自定义"]

# 首页市场概览股票池（代表性 A 股）
WATCHLIST = [
    {"code": "600519.SH", "name": "贵州茅台"},
    {"code": "000001.SZ", "name": "平安银行"},
    {"code": "600036.SH", "name": "招商银行"},
    {"code": "601318.SH", "name": "中国平安"},
    {"code": "000858.SZ", "name": "五粮液"},
    {"code": "300750.SZ", "name": "宁德时代"},
]

# 热门股票（参数卡片上方快捷列表，5 条）
HOT_STOCKS = [(s["code"], s["name"]) for s in WATCHLIST[:5]]

# ===== 主题色 =====
PRIMARY = "#1e3a8a"
ACCENT = "#f59e0b"
UP = "#dc2626"      # A 股红涨
DOWN = "#16a34a"    # A 股绿跌
NEUTRAL = "#64748b"

st.set_page_config(page_title="智能股票推荐系统", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")

# matplotlib 中文字体
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "PingFang SC", "Heiti SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ===== 全局样式（含移动端适配）=====
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%); }
    header[data-testid="stHeader"] { background: transparent; }

    .hero {
        background: linear-gradient(120deg, #1e3a8a 0%, #1e40af 60%, #2563eb 100%);
        border-radius: 18px; padding: 28px 32px; margin-bottom: 18px;
        color: #fff; box-shadow: 0 8px 24px rgba(30,58,138,0.25);
    }
    .hero h1 { color: #fff; margin: 0; font-size: 2rem; letter-spacing: 1px; }
    .hero p { color: #cbd5e1; margin: 8px 0 0; font-size: 1rem; }

    .panel {
        background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
        padding: 20px 24px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .panel h3 { margin: 0 0 12px; color: #1e3a8a; font-size: 1.15rem; border-left: 4px solid #f59e0b; padding-left: 10px; }

    .metric-card {
        background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
        padding: 18px 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .metric-card .label { color: #64748b; font-size: 0.85rem; }
    .metric-card .value { font-size: 1.9rem; font-weight: 700; margin-top: 4px; }

    .verdict {
        border-radius: 16px; padding: 26px 30px; text-align: center; color: #fff;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12); margin: 14px 0;
    }
    .verdict .big { font-size: 2.4rem; font-weight: 800; letter-spacing: 2px; }
    .verdict .sub { font-size: 1rem; opacity: 0.9; margin-top: 6px; }

    .tag { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; margin: 2px 4px 2px 0; }
    .tag-bull { background: #fee2e2; color: #dc2626; }
    .tag-bear { background: #dcfce7; color: #16a34a; }
    .tag-neutral { background: #e2e8f0; color: #475569; }

    .stock-card {
        background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
        padding: 16px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow .2s ease, transform .2s ease;
    }
    .stock-link { display: block; text-decoration: none; color: inherit; }
    .stock-link:hover { text-decoration: none; }
    .stock-link:hover .stock-card { box-shadow: 0 6px 18px rgba(30,58,138,0.12); transform: translateY(-2px); }
    .stock-head { display: flex; justify-content: space-between; align-items: flex-start; }
    .stock-name { font-weight: 700; color: #1e3a8a; font-size: 1.02rem; }
    .stock-code { color: #94a3b8; font-size: 0.78rem; }
    .stock-price { text-align: right; }
    .stock-price .price { font-size: 1.45rem; font-weight: 800; line-height: 1.1; }
    .stock-price .chg { font-size: 0.82rem; font-weight: 600; }
    .stock-spark { margin-top: 10px; }

    div[data-testid="stExpander"] { border-radius: 12px; border: 1px solid #e5e7eb; }
    div.stButton > button { border-radius: 10px; font-weight: 600; }

    /* ===== 移动端适配 ===== */
    @media (max-width: 768px) {
        .hero { padding: 20px 18px; border-radius: 14px; }
        .hero h1 { font-size: 1.4rem; }
        .hero p { font-size: 0.85rem; }
        .panel { padding: 16px 14px; }
        .metric-card .value { font-size: 1.4rem; }
        .verdict .big { font-size: 1.8rem; }
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.6rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }
        [data-testid="stTabs"] button { font-size: 0.72rem !important; padding: 6px 8px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ===== 顶部 =====
st.markdown("""
<div class="hero">
    <h1>📈 智能股票推荐系统</h1>
    <p>技术面 · 基本面 · 舆情面 三维分析 ｜ 多空辩论 · 研究经理裁决 ｜ 策略执行与在线算法</p>
</div>
""", unsafe_allow_html=True)


# ===== 辅助函数 =====
def score_color(score):
    try:
        s = float(score)
    except (TypeError, ValueError):
        return NEUTRAL
    if s >= 70:
        return UP
    if s >= 40:
        return ACCENT
    return DOWN


def action_color(action):
    if "买入" in str(action):
        return UP
    if "持有" in str(action) or "观望" in str(action):
        return ACCENT
    return DOWN


def rating_color(rating):
    if "看多" in str(rating):
        return UP
    if "看空" in str(rating):
        return DOWN
    return NEUTRAL


def metric_card(label, value, color=NEUTRAL):
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value" style="color:{color}">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def verdict_card(title, sub, color):
    st.markdown(f"""
    <div class="verdict" style="background:{color}">
        <div class="big">{title}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def arg_list(items, tag_class="tag-neutral"):
    if not items:
        return "<span style='color:#94a3b8'>暂无</span>"
    tags = "".join(f"<span class='tag {tag_class}'>{x}</span>" for x in items)
    return tags


def svg_sparkline(values, width=180, height=42, color=None):
    """纯 SVG 迷你走势图，无需额外依赖，响应式缩放。"""
    vals = [float(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        vmax = vmin + 1
    pts = []
    for i, v in enumerate(vals):
        x = i / (len(vals) - 1) * width
        y = height - (v - vmin) / (vmax - vmin) * (height - 6) - 3
        pts.append(f"{x:.1f},{y:.1f}")
    color = color or (UP if vals[-1] >= vals[0] else DOWN)
    polyline = " ".join(pts)
    area = f"0,{height} {polyline} {width},{height}"
    return (
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
        f'<polygon points="{area}" fill="{color}" opacity="0.1"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def stock_name(code):
    for s in WATCHLIST:
        if s["code"] == code:
            return s["name"]
    return code


def stock_card(name, code, price, chg, closes):
    color = UP if chg >= 0 else DOWN
    arrow = "▲" if chg >= 0 else "▼"
    spark = svg_sparkline(closes, color=color)
    st.markdown(f"""
    <a class="stock-link" href="?stock={code}">
    <div class="stock-card">
        <div class="stock-head">
            <div>
                <div class="stock-name">{name}</div>
                <div class="stock-code">{code}</div>
            </div>
            <div class="stock-price" style="color:{color}">
                <div class="price">{price:.2f}</div>
                <div class="chg">{arrow} {chg:+.2f}%</div>
            </div>
        </div>
        <div class="stock-spark">{spark}</div>
    </div>
    </a>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner="正在加载市场数据...")
def load_watchlist(start_date, end_date):
    """拉取股票池近端行情，返回卡片所需精简字段。"""
    items = []
    for s in WATCHLIST:
        try:
            df = tushare_client.get_daily(s["code"], start_date, end_date)
        except Exception:  # noqa: BLE001
            continue
        if df is None or df.empty:
            continue
        df = df.sort_values("trade_date").reset_index(drop=True)
        latest = df.iloc[-1]
        try:
            price = round(float(latest["close"]), 2)
            chg = round(float(latest.get("pct_chg") or 0), 2)
        except (TypeError, ValueError):
            continue
        items.append({
            "name": s["name"],
            "code": s["code"],
            "price": price,
            "chg": chg,
            "closes": df["close"].astype(float).tolist(),
        })
    return items


def price_chart_df(df):
    """构造收盘价 + 均线的图表 DataFrame（供 st.line_chart 使用，带悬浮提示）。"""
    df = df.sort_values("trade_date").reset_index(drop=True).copy()
    df["日期"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    close = df["close"].astype(float)
    df["收盘价"] = close
    df["MA5"] = close.rolling(5).mean()
    df["MA20"] = close.rolling(20).mean()
    df["MA60"] = close.rolling(60).mean()
    return df.set_index("日期")[["收盘价", "MA5", "MA20", "MA60"]]


def score_bar_df(scores):
    """构造三维度评分横向条形图 DataFrame。"""
    return pd.DataFrame({
        "维度": ["技术面", "基本面", "舆情面"],
        "得分": [
            float(scores.get("technical", 0)),
            float(scores.get("fundamental", 0)),
            float(scores.get("sentiment", 0)),
        ],
    }).set_index("维度")


def gauge_chart(score):
    """综合得分半圆仪表盘。"""
    try:
        score = max(0, min(100, float(score)))
    except (TypeError, ValueError):
        score = 0
    color = score_color(score)
    fig, ax = plt.subplots(figsize=(4, 2.4), dpi=100)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.35, 1.1)
    ax.axis("off")
    ax.add_patch(Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=180, color="#e2e8f0", lw=13))
    ax.add_patch(Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=180 * score / 100,
                     color=color, lw=13, capstyle="round"))
    ax.text(0, 0.12, f"{score:.0f}", ha="center", va="center", fontsize=32, fontweight="bold", color=color)
    ax.text(0, -0.42, "综合得分", ha="center", va="center", fontsize=9, color="#64748b")
    fig.patch.set_facecolor("#ffffff")
    plt.tight_layout()
    return fig


def render_recommendation(result, strategy_type, ts_code, start_date, end_date):
    """渲染完整推荐结果（阶段一/二/三），详情页与推荐流程页复用。"""
    st.markdown('<div class="panel"><h3>阶段一 · 基础分析（三分析师并行）</h3>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        metric_card("技术面得分", result.get("technical_score"), score_color(result.get("technical_score")))
    with m2:
        metric_card("基本面得分", result.get("fundamental_score"), score_color(result.get("fundamental_score")))
    with m3:
        metric_card("舆情面得分", result.get("sentiment_score"), score_color(result.get("sentiment_score")))

    st.bar_chart(score_bar_df({
        "technical": result.get("technical_score", 0),
        "fundamental": result.get("fundamental_score", 0),
        "sentiment": result.get("sentiment_score", 0),
    }), horizontal=True, use_container_width=True)

    tr = result.get("technical_report", {})
    fr = result.get("fundamental_report", {})
    sr = result.get("sentiment_report", {})

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("**📐 技术面**")
        st.markdown(f"- 趋势：**{tr.get('trend', '—')}**")
        st.markdown(f"- RSI6：`{tr.get('key_metrics', {}).get('rsi6', '—')}`")
        st.markdown(f"- MACD：`{tr.get('key_metrics', {}).get('macd_signal', '—')}`")
        st.caption(tr.get("summary", ""))
    with r2:
        st.markdown("**💰 基本面**")
        st.markdown(f"- 估值：**{fr.get('valuation_status', '—')}**")
        st.markdown(f"- ROE：`{fr.get('metrics', {}).get('roe', '—')}`")
        st.markdown(f"- PE：`{fr.get('metrics', {}).get('pe', '—')}`")
        st.caption(fr.get("summary", ""))
    with r3:
        st.markdown("**🗣️ 舆情面**")
        st.markdown(f"- 情绪：**{sr.get('polarity', '—')}**")
        st.markdown(f"- 热点：{arg_list(sr.get('hot_topics', []))}")
        st.caption(sr.get("summary", ""))

    with st.expander("📈 查看技术走势图（收盘价 + 均线，悬浮查看数据点）"):
        try:
            daily = tushare_client.get_daily(ts_code, start_date, end_date)
            if len(daily):
                st.line_chart(price_chart_df(daily), use_container_width=True)
            else:
                st.caption("无行情数据")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"走势图渲染失败：{exc}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel"><h3>阶段二 · 信息综合与辩论</h3>', unsafe_allow_html=True)
    bull = result.get("bull_report", {})
    bear = result.get("bear_report", {})
    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown("#### 🐂 多头观点")
        st.markdown(f"**置信度：{bull.get('confidence', '—')}**")
        st.markdown(bull.get("summary", ""))
        st.markdown(f"核心逻辑：{bull.get('core_thesis', '—')}")
        st.markdown(f"风险承认：{bull.get('risk_acknowledgment', '—')}")
        with st.expander("详细论据"):
            st.json(bull)
    with bc2:
        st.markdown("#### 🐻 空头观点")
        st.markdown(f"**置信度：{bear.get('confidence', '—')}**")
        st.markdown(bear.get("summary", ""))
        st.markdown(f"核心逻辑：{bear.get('core_thesis', '—')}")
        st.markdown(f"风险承认：{bear.get('risk_acknowledgment', '—')}")
        with st.expander("详细论据"):
            st.json(bear)

    comp = result.get("comprehensive_report", {})
    st.markdown(f"#### 🧭 研究经理裁决")
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        metric_card("综合评分", comp.get("comprehensive_score"), score_color(comp.get("comprehensive_score")))
    with rc2:
        metric_card("综合评级", comp.get("rating", "—"), rating_color(comp.get("rating", "—")))
    with rc3:
        sb = comp.get("score_breakdown", {})
        metric_card("辩论调整分", sb.get("debate_adjust", "—"), NEUTRAL)
    st.markdown(comp.get("summary", ""))
    st.markdown(f"核心驱动：{arg_list(comp.get('core_drivers', []), 'tag-bull')}")
    st.markdown(f"主要风险：{arg_list(comp.get('main_risks', []), 'tag-bear')}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel"><h3>阶段三 · 策略执行与最终推荐</h3>', unsafe_allow_html=True)
    rec = result.get("recommendation", {})
    verdict_card(rec.get("action", "—"), f"加权综合得分：{rec.get('score', '—')} ｜ 策略：{strategy_type}",
                 action_color(rec.get("action", "")))
    g1, g2 = st.columns([1, 1.6])
    with g1:
        st.pyplot(gauge_chart(rec.get("score", 0)), use_container_width=True)
    with g2:
        st.markdown("**推荐理由**")
        for reason in rec.get("reasons", []):
            st.markdown(f"- {reason}")
        st.markdown(f"**风险提示**：{arg_list(comp.get('main_risks', []), 'tag-bear')}")
    with st.expander("查看完整结构化结果"):
        st.json(result)
    st.markdown('</div>', unsafe_allow_html=True)


# ===== 详情页 / 主界面路由 =====
qs = st.query_params
selected_stock = qs.get("stock")


if selected_stock:
    # ---------- 股票详情页 ----------
    name = stock_name(selected_stock)
    if st.button("← 返回市场概览"):
        st.query_params.clear()
        st.rerun()

    st.markdown(f"## {name} <span style='color:#64748b;font-size:1rem'>{selected_stock}</span>",
                unsafe_allow_html=True)

    _today = datetime.now()
    _start = (_today - timedelta(days=180)).strftime("%Y%m%d")
    _end = _today.strftime("%Y%m%d")

    try:
        daily = tushare_client.get_daily(selected_stock, _start, _end)
    except Exception as exc:  # noqa: BLE001
        st.error(f"行情获取失败：{exc}")
        daily = pd.DataFrame()

    if len(daily):
        daily = daily.sort_values("trade_date").reset_index(drop=True)
        last = daily.iloc[-1]
        prev_close = float(last.get("pre_close") or 0)
        price = float(last["close"])
        chg = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0.0
        high = float(daily["high"].max())
        low = float(daily["low"].min())
        vol = float(last.get("vol") or 0)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            metric_card("最新价", f"{price:.2f}", UP if chg >= 0 else DOWN)
        with m2:
            metric_card("涨跌幅", f"{chg:+.2f}%", UP if chg >= 0 else DOWN)
        with m3:
            metric_card("区间最高", f"{high:.2f}", UP)
        with m4:
            metric_card("区间最低", f"{low:.2f}", DOWN)

        st.line_chart(price_chart_df(daily), use_container_width=True)

        if st.button(f"🚀 对 {name} 运行完整推荐", type="primary", use_container_width=True):
            with st.spinner("执行中（含 LLM 多空辩论，约 1-3 分钟）..."):
                try:
                    result = graph.invoke({
                        "workflow_id": f"wf_{uuid.uuid4().hex[:8]}",
                        "ts_code": selected_stock,
                        "symbol": selected_stock,
                        "start_date": _start,
                        "end_date": _end,
                        "strategy_config": {"strategy_type": "均衡型"},
                    })
                    render_recommendation(result, "均衡型", selected_stock, _start, _end)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"执行失败：{exc}")
    else:
        st.info("暂无该股票的行情数据。")

else:
    # ---------- 主界面（tabs） ----------
    tab_home, tab_rec, tab_data, tab_algo, tab_queue = st.tabs(
        ["🏠 市场概览", "📊 完整推荐流程", "📡 数据接入验证", "🧪 自定义算法", "⚙️ 任务队列"]
    )

    # ===== 0. 市场概览 =====
    with tab_home:
        st.markdown("### 市场概览")
        st.caption("点击卡片查看股票详情")
        _today = datetime.now()
        _start = (_today - timedelta(days=180)).strftime("%Y%m%d")
        _end = _today.strftime("%Y%m%d")
        watch = load_watchlist(_start, _end)
        if not watch:
            st.info("暂无市场数据，请检查 Tushare 连接与 token 配置。")
        else:
            cols = st.columns(3)
            for i, item in enumerate(watch):
                with cols[i % 3]:
                    stock_card(item["name"], item["code"], item["price"], item["chg"], item["closes"])

    # ===== 1. 完整推荐流程 =====
    with tab_rec:
        st.markdown("### 输入参数")

        # 热门股票快捷列表
        st.markdown("**🔥 热门股票**")
        if "rec_ts" not in st.session_state:
            st.session_state["rec_ts"] = "000001.SZ"
        hot_cols = st.columns(len(HOT_STOCKS))
        for i, (code, nm) in enumerate(HOT_STOCKS):
            if hot_cols[i].button(nm, key=f"hot_{i}", use_container_width=True):
                st.session_state["rec_ts"] = code
                st.rerun()

        c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.2])
        ts_code = c1.text_input("股票代码", value=st.session_state["rec_ts"], key="rec_ts")
        start_date = c2.text_input("开始日期", value="20250101", help="格式 YYYYMMDD")
        end_date = c3.text_input("结束日期", value="20250630", help="格式 YYYYMMDD")
        strategy_type = c4.selectbox("策略类型", STRATEGY_TYPES)

        if st.button("🚀 运行完整推荐", type="primary", use_container_width=True):
            with st.spinner("执行中（含 LLM 多空辩论，约 1-3 分钟）..."):
                try:
                    result = graph.invoke({
                        "workflow_id": f"wf_{uuid.uuid4().hex[:8]}",
                        "ts_code": ts_code,
                        "symbol": ts_code,
                        "start_date": start_date,
                        "end_date": end_date,
                        "strategy_config": {"strategy_type": strategy_type},
                    })
                except Exception as exc:  # noqa: BLE001
                    st.error(f"执行失败：{exc}")
                    st.stop()
            render_recommendation(result, strategy_type, ts_code, start_date, end_date)

    # ===== 2. 数据接入验证 =====
    with tab_data:
        st.markdown("### 数据源连接验证")
        c1, c2, c3 = st.columns(3)
        ts_code = c1.text_input("股票代码", value="000001.SZ", key="data_ts")
        start_date = c2.text_input("开始日期", value="20250101", key="data_s")
        end_date = c3.text_input("结束日期", value="20250630", key="data_e")

        if st.button("📡 拉取数据", type="primary"):
            st.markdown('<div class="panel"><h3>① Tushare 日线行情</h3>', unsafe_allow_html=True)
            try:
                daily = tushare_client.get_daily(ts_code, start_date, end_date)
                metric_card("行情记录数", len(daily), PRIMARY)
                if len(daily):
                    st.line_chart(price_chart_df(daily), use_container_width=True)
                    st.dataframe(daily.head(8), use_container_width=True)
            except Exception as exc:  # noqa: BLE001
                st.error(f"行情获取失败：{exc}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><h3>② Tushare 财务指标</h3>', unsafe_allow_html=True)
            try:
                fina = tushare_client.get_fina_indicator(ts_code)
                metric_card("财务记录数", len(fina), PRIMARY)
                if len(fina):
                    cols = ["end_date", "roe", "eps", "gross_margin"]
                    cols = [c for c in cols if c in fina.columns]
                    st.dataframe(fina[cols].head(8), use_container_width=True)
            except Exception as exc:  # noqa: BLE001
                st.error(f"财务获取失败：{exc}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><h3>③ akshare 舆情新闻</h3>', unsafe_allow_html=True)
            try:
                senti = fetch_sentiment(ts_code, start_date, end_date)
                news = senti.get("news_list", [])
                metric_card("新闻条数", len(news), PRIMARY)
                if news:
                    st.dataframe(news[:8], use_container_width=True)
            except Exception as exc:  # noqa: BLE001
                st.error(f"舆情获取失败：{exc}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ===== 3. 自定义算法 =====
    with tab_algo:
        st.markdown("### 自定义算法（代码生成 → 校验 → 沙箱执行）")
        description = st.text_area(
            "算法描述",
            value="根据三维度得分加权计算，基本面60%、技术30%、舆情10%，得分>=70买入，40-69观望，<40回避",
        )

        c1, c2, c3 = st.columns(3)
        scores = {
            "technical_score": c1.slider("技术得分", 0, 100, 60),
            "fundamental_score": c2.slider("基本面得分", 0, 100, 70),
            "sentiment_score": c3.slider("舆情得分", 0, 100, 60),
        }

        if st.button("🧪 生成并执行", type="primary", use_container_width=True):
            st.markdown('<div class="panel"><h3>① 代码生成</h3>', unsafe_allow_html=True)
            with st.spinner("LLM 生成代码中..."):
                gen = generate_code(description)
            code = gen.get("code", "")
            st.code(code, language="python")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><h3>② AST 静态校验</h3>', unsafe_allow_html=True)
            val = validate_code(code)
            if val["passed"]:
                st.success("✅ 校验通过，未发现危险代码")
            else:
                st.error(f"🚫 校验拦截：{val['risk_points']}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><h3>③ 沙箱执行</h3>', unsafe_allow_html=True)
            entry = gen.get("entry_point") or "recommend"
            exe = execute(code, entry_point=entry, scores=scores)
            ec = exe.get("exit_code")
            ec_color = DOWN if ec == 0 else UP
            metric_card("exit_code", ec, ec_color)
            res = exe.get("result")
            if res:
                action = res.get("action", "—")
                verdict_card(action, f"算法评分：{res.get('score', '—')}", action_color(action))
                st.pyplot(gauge_chart(res.get("score", 0)), use_container_width=True)
            st.markdown("**执行日志**")
            for log in exe.get("logs", []):
                st.text(f"[{log['level']}] {log['message']}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ===== 4. 任务队列 =====
    with tab_queue:
        st.markdown("### 任务队列（同步提交 + 异步 Worker）")
        c1, c2, c3 = st.columns(3)
        ts_code = c1.text_input("股票代码", value="000001.SZ", key="q_ts")
        start_date = c2.text_input("开始日期", value="20250101", key="q_s")
        end_date = c3.text_input("结束日期", value="20250630", key="q_e")

        b1, b2 = st.columns(2)
        if b1.button("① 提交任务（入队）", type="primary", use_container_width=True):
            wid = submit_task(ts_code, start_date, end_date, symbol=ts_code)
            st.session_state["queue_wid"] = wid
            st.success(f"已入队，workflow_id = `{wid}`")
            st.info(f"当前状态：**{get_status(wid)['status']}**")

        if b2.button("② Worker 消费并执行", use_container_width=True):
            task = dequeue_task(timeout=1)
            if task is None:
                st.warning("队列为空，请先提交任务")
            else:
                with st.spinner("Worker 执行中（含 LLM 推理）..."):
                    result = _execute_task(task)
                wid = task["workflow_id"]
                st.session_state["queue_wid"] = wid
                st.success(f"执行完成，workflow_id = `{wid}`")
                rec = result.get("recommendation", {})
                verdict_card(rec.get("action", "—"), f"得分：{rec.get('score', '—')}",
                             action_color(rec.get("action", "")))
                st.pyplot(gauge_chart(rec.get("score", 0)), use_container_width=True)

        if "queue_wid" in st.session_state:
            st.markdown('<div class="panel"><h3>任务状态查询</h3>', unsafe_allow_html=True)
            st.json(get_status(st.session_state["queue_wid"]))
            st.markdown('</div>', unsafe_allow_html=True)
