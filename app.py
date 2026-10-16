"""統家便利商店 自動補貨系統（課堂示範版）

執行：streamlit run app.py
"""

from datetime import datetime, timedelta, timezone

import altair as alt
import pandas as pd
import streamlit as st

from replenish import (
    PRODUCTS, SAFETY_RATE, SPECIAL_MIN_DIFF, SPECIAL_RATE, STATUS_LOW, STATUS_NORMAL, STATUS_NOTE,
    STATUS_SPECIAL, STATUS_SUGGEST, STORE_NAME, calc, is_special, sales_dates, status_of,
)

PAGES = ["首頁", "自動補貨清單", "商品明細", "補貨單確認"]
SUCCESS_MSG = "補貨單已成功送出至統家總公司。"
SPECIAL_MSG = "此補貨量明顯高於平常需求，請確認是否為特殊訂單。"
TW = timezone(timedelta(hours=8))  # 線上版在瀏覽器執行時預設是 UTC，固定用台灣時間

st.set_page_config(page_title="統家自動補貨系統", page_icon="📦", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e6e8eb;
        border-radius: 10px;
        padding: 14px 18px;
    }
    [data-testid="stMetricLabel"] { color: #6b7280; }
    [data-testid="stSidebar"] { border-right: 1px solid #eceef1; }
    h1, h2, h3 { font-weight: 600; letter-spacing: 0.5px; }
    .muted { color: #6b7280; font-size: 0.9rem; }
    .formula {
        background: #f7f8fa;
        border: 1px solid #eceef1;
        border-radius: 10px;
        padding: 16px 20px;
        font-size: 1.02rem;
        line-height: 2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- 狀態（session_state） ----------

def init_state():
    if "final" in st.session_state:
        return
    st.session_state.final = {p["name"]: calc(p)["suggested"] for p in PRODUCTS}
    st.session_state.reason = {p["name"]: "" for p in PRODUCTS}
    st.session_state.confirmed = {p["name"]: False for p in PRODUCTS}
    st.session_state.submitted = False
    st.session_state.order_no = ""
    st.session_state.submitted_at = ""


def reset_demo():
    # 側邊欄頁面選單（page）不刪除，改成指定回首頁，畫面和選單才會同步
    for key in list(st.session_state.keys()):
        if key != "page":
            del st.session_state[key]
    st.session_state.page = "首頁"


def go(page):
    st.session_state.page = page


def build_rows():
    rows = []
    for p in PRODUCTS:
        c = calc(p)
        final = st.session_state.final[p["name"]]
        rows.append({
            **p, **c,
            "avg": c["total"] / 7,
            "final": final,
            "reason": st.session_state.reason[p["name"]],
            "status": status_of(p["stock"], c["forecast"], c["suggested"], final),
        })
    return rows


init_state()
rows = build_rows()
today = datetime.now(TW).date()


# ---------- 側邊欄 ----------

with st.sidebar:
    st.markdown("### 📦 統家自動補貨系統")
    st.markdown(f"<div class='muted'>{STORE_NAME}</div>", unsafe_allow_html=True)
    st.write("")
    page = st.radio("頁面", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    st.markdown(
        "<div class='muted'>系統只提供建議補貨量，<br>最後數量由店長確認。</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.button("重設示範資料", on_click=reset_demo, use_container_width=True)


# ---------- 1. 首頁 ----------

def page_dashboard():
    st.title("首頁")
    st.markdown(f"<div class='muted'>{STORE_NAME}　｜　每日定期盤點制＋安全庫存管理</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='muted' style='margin-top:6px'>本系統依近期銷售紀錄與現有庫存產生補貨建議，"
        "實際需求仍可能受天氣、活動、節慶等因素影響，最終補貨量由店長確認。</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    need = [r for r in rows if r["final"] > 0]
    count = {s: sum(r["status"] == s for r in rows)
             for s in [STATUS_NORMAL, STATUS_SUGGEST, STATUS_LOW, STATUS_SPECIAL]}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("今日日期", today.strftime("%Y/%m/%d"))
    c2.metric("今日需補貨品項", f"{len(need)} 項")
    c3.metric("低庫存商品數", f"{count[STATUS_LOW]} 項")
    c4.metric("特殊訂單數", f"{count[STATUS_SPECIAL]} 項")

    c1, c2, c3 = st.columns(3)
    c1.metric("今日建議補貨總量", f"{sum(r['suggested'] for r in rows)} 件")
    c2.metric("店長確認補貨總量", f"{sum(r['final'] for r in rows)} 件")
    c3.metric("補貨單狀態", "已送出" if st.session_state.submitted else "未送出")

    st.write("")
    st.subheader("補貨狀態摘要")
    cols = st.columns(4)
    for col, (s, n) in zip(cols, count.items()):
        with col.container(border=True):
            st.markdown(f"**{s}**")
            st.markdown(f"<span style='font-size:1.8rem;font-weight:600'>{n}</span> 項",
                        unsafe_allow_html=True)
            st.markdown(f"<div class='muted'>{STATUS_NOTE[s]}</div>", unsafe_allow_html=True)

    attention = [r for r in rows if r["status"] in (STATUS_LOW, STATUS_SPECIAL)]
    if attention:
        st.write("")
        st.subheader("需要注意的商品")
        st.dataframe(
            pd.DataFrame([{
                "商品名稱": r["name"], "現有庫存": r["stock"], "預測明日銷售": r["forecast"],
                "系統建議": r["suggested"], "店長最後補貨量": r["final"], "狀態": r["status"],
            } for r in attention]),
            hide_index=True, use_container_width=True,
        )

    st.write("")
    st.button("前往自動補貨清單 →", on_click=go, args=("自動補貨清單",), type="primary")


# ---------- 2. 自動補貨清單 ----------

def page_list():
    st.title("自動補貨清單")
    st.markdown(
        "<div class='muted'>系統已依公式算出建議補貨量。若有特殊情況，"
        "可直接修改「店長最後補貨量」並填寫原因。</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    df = pd.DataFrame([{
        "商品名稱": r["name"],
        "分類": r["category"],
        "現有庫存": r["stock"],
        "預測明日銷售": r["forecast"],
        "安全庫存": r["safety"],
        "系統建議補貨量": r["suggested"],
        "店長最後補貨量": r["final"],
        "特殊訂單原因": r["reason"],
        "狀態": r["status"],
    } for r in rows])

    editable = ["店長最後補貨量", "特殊訂單原因"]
    locked = st.session_state.submitted
    # 不設 key：stlite（線上版）內建的 Streamlit 在有 key 時會出錯；
    # 表格每次都從 session_state 重建，所以不需要 key 保存編輯狀態
    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        disabled=True if locked else [c for c in df.columns if c not in editable],
        column_config={
            "分類": st.column_config.TextColumn(width="small"),
            "預測明日銷售": st.column_config.NumberColumn(
                "預測明日", help="預測明日銷售（最近 7 天平均，計算過程見「商品明細」）"),
            "系統建議補貨量": st.column_config.NumberColumn("系統建議", help="系統建議補貨量"),
            "店長最後補貨量": st.column_config.NumberColumn("✏️ 店長最後補貨量", min_value=0, step=1,
                                                           format="%d",
                                                           help="可修改；預設為系統建議量"),
            "特殊訂單原因": st.column_config.TextColumn("✏️ 特殊原因",
                                                       help="特殊訂單原因，例如：颱風警報、學校活動"),
        },
    )

    changed = False
    for _, row in edited.iterrows():
        name = row["商品名稱"]
        qty = row["店長最後補貨量"]
        qty = 0 if pd.isna(qty) else int(qty)
        reason = "" if pd.isna(row["特殊訂單原因"]) else str(row["特殊訂單原因"])
        if qty != st.session_state.final[name]:
            st.session_state.final[name] = qty
            st.session_state.confirmed[name] = False  # 數量改了就要重新確認
            changed = True
        if reason != st.session_state.reason[name]:
            st.session_state.reason[name] = reason
            changed = True
    if changed:
        st.rerun()

    if locked:
        st.info("補貨單已送出，清單已鎖定。可從側邊欄「重設示範資料」重新開始。")

    specials = [r for r in rows if r["status"] == STATUS_SPECIAL]
    for r in specials:
        st.warning(f"**{r['name']}**：{SPECIAL_MSG}"
                   f"（系統建議 {r['suggested']} 件，店長輸入 {r['final']} 件）")
    if specials and not locked:
        st.caption("系統不會禁止特殊訂單，請到「補貨單確認」頁確認。")

    with st.expander("狀態說明"):
        for s, note in STATUS_NOTE.items():
            st.markdown(f"- **{s}**：{note}")
        st.markdown("- 低庫存判定：現有庫存 < 預測明日銷售 × 50%")
        st.markdown(f"- 特殊訂單判定：以下兩個條件同時成立"
                    f"（系統建議為 0 時，比例條件以 1 計算）\n"
                    f"    - 店長最後補貨量 > 系統建議 × {SPECIAL_RATE}\n"
                    f"    - 店長最後補貨量比系統建議多 {SPECIAL_MIN_DIFF} 件以上")
        st.markdown("- 若同時符合多個條件，系統會優先顯示較需要注意的狀態。"
                    "優先順序：特殊訂單 > 低庫存 > 建議補貨 > 正常。")

    st.write("")
    st.button("前往補貨單確認 →", on_click=go, args=("補貨單確認",), type="primary")


# ---------- 3. 商品明細 ----------

def page_detail():
    st.title("商品明細")
    names = [r["name"] for r in rows]
    name = st.selectbox("選擇商品", names, key="detail_item")
    r = next(x for x in rows if x["name"] == name)

    st.markdown(f"<div class='muted'>分類：{r['category']}　｜　狀態：{r['status']}　"
                f"— {STATUS_NOTE[r['status']]}</div>", unsafe_allow_html=True)
    st.write("")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("目前庫存", r["stock"])
    c2.metric("預測明日銷售", r["forecast"])
    c3.metric("安全庫存", r["safety"])
    c4.metric("系統建議補貨量", r["suggested"])
    c5.metric("店長最後補貨量", r["final"])

    st.write("")
    left, right = st.columns([3, 2])

    dates = sales_dates(today)
    sales_df = pd.DataFrame({
        "日期": [d.strftime("%m/%d") for d in dates],
        "銷售量": r["sales"],
    })

    with left:
        st.subheader("最近 7 天銷售")
        chart = (
            alt.Chart(sales_df)
            .mark_line(point=alt.OverlayMarkDef(size=60), color="#0f766e", strokeWidth=2.5)
            .encode(
                x=alt.X("日期:O", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
                y=alt.Y("銷售量:Q", title="銷售量（件）", scale=alt.Scale(zero=True)),
                tooltip=["日期", "銷售量"],
            )
            .properties(height=300)
        )
        rule = (
            alt.Chart(pd.DataFrame({"y": [r["forecast"]]}))
            .mark_rule(strokeDash=[6, 4], color="#9ca3af")
            .encode(y="y:Q")
        )
        st.altair_chart(chart + rule, use_container_width=True)
        st.caption(f"虛線：預測明日銷售 {r['forecast']} 件")

    with right:
        st.subheader("銷售紀錄")
        st.dataframe(sales_df, hide_index=True, use_container_width=True)

    st.subheader("計算公式")
    plus = " + ".join(str(s) for s in r["sales"])
    raw_need = r["forecast"] + r["safety"] - r["stock"]
    result = f"<b>{raw_need}</b>" if raw_need >= 0 else f"{raw_need} → 小於 0，設為 <b>0</b>"
    lines = [
        f"預測明日銷售 = 最近 7 天銷售總和 ÷ 7 = ({plus}) ÷ 7 = {r['total']} ÷ 7"
        f" = {r['avg']:.1f} ≈ <b>{r['forecast']}</b>",
        f"安全庫存 = 預測明日銷售 × {int(SAFETY_RATE * 100)}% = {r['forecast']} × {SAFETY_RATE:.1f}"
        f" = {r['forecast'] * SAFETY_RATE:.1f} ≈ <b>{r['safety']}</b>",
        f"建議補貨量 = 預測明日銷售 + 安全庫存 − 現有庫存"
        f" = {r['forecast']} + {r['safety']} − {r['stock']} = {result}",
    ]
    st.markdown(f"<div class='formula'>{'<br>'.join(lines)}</div>", unsafe_allow_html=True)
    st.caption("所有數量皆四捨五入取整數；假設今晚下單、明早到貨。")
    st.caption("本系統採用簡單 7 日移動平均，讓店長可以直接理解預測依據。")
    st.caption(f"本課堂示範版將安全庫存簡化設定為預測需求的 {int(SAFETY_RATE * 100)}%；"
               "實際企業可依商品銷售波動、供貨時間及缺貨成本調整。")


# ---------- 4. 補貨單確認 ----------

def page_confirm():
    st.title("補貨單確認")
    order = [r for r in rows if r["final"] > 0]

    st.markdown(
        f"<div class='muted'>門市：{STORE_NAME}　｜　下單日：{today:%Y/%m/%d}　｜　"
        f"預計到貨：{today + timedelta(days=1):%Y/%m/%d}</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    if st.session_state.submitted:
        st.success(SUCCESS_MSG)
        st.markdown(f"補貨單編號：**{st.session_state.order_no}**　｜　"
                    f"送出時間：{st.session_state.submitted_at}")

    c1, c2 = st.columns(2)
    c1.metric("合計品項", f"{len(order)} 項")
    c2.metric("合計數量", f"{sum(r['final'] for r in order)} 件")

    st.dataframe(
        pd.DataFrame([{
            "商品名稱": r["name"],
            "分類": r["category"],
            "系統建議補貨量": r["suggested"],
            "店長最後補貨量": r["final"],
            "備註": (f"特殊訂單：{r['reason']}" if r["reason"] else "特殊訂單")
            if r["status"] == STATUS_SPECIAL else "",
        } for r in order], columns=["商品名稱", "分類", "系統建議補貨量", "店長最後補貨量", "備註"]),
        hide_index=True, use_container_width=True,
    )

    if st.session_state.submitted:
        return

    specials = [r for r in order if is_special(r["final"], r["suggested"])]
    if specials:
        st.subheader("特殊訂單確認")
        for r in specials:
            with st.container(border=True):
                st.warning(SPECIAL_MSG)
                st.markdown(
                    f"**{r['name']}**：平常每日約賣 {r['forecast']} 件，系統建議 {r['suggested']} 件，"
                    f"店長輸入 **{r['final']}** 件。"
                    + (f"　原因：{r['reason']}" if r["reason"] else "　（未填寫原因）")
                )
                a, b = st.columns([1, 4])
                a.button("返回修改", key=f"back_{r['name']}", on_click=go, args=("自動補貨清單",))
                ok = b.checkbox("確認特殊訂單（由店長負責確認）", key=f"cb_{r['name']}",
                                value=st.session_state.confirmed[r["name"]])
                st.session_state.confirmed[r["name"]] = ok

    pending = [r["name"] for r in specials if not st.session_state.confirmed[r["name"]]]

    st.write("")
    a, b, _ = st.columns([1, 1, 3])
    a.button("返回修改", on_click=go, args=("自動補貨清單",), use_container_width=True)
    submit = b.button("送出補貨單", type="primary", use_container_width=True,
                      disabled=bool(pending) or not order)
    if pending:
        st.caption(f"尚有特殊訂單未確認：{'、'.join(pending)}")

    if submit:
        now = datetime.now(TW)
        st.session_state.submitted = True
        st.session_state.order_no = f"TJ-{now:%Y%m%d-%H%M%S}"
        st.session_state.submitted_at = now.strftime("%Y/%m/%d %H:%M")
        st.rerun()


{
    "首頁": page_dashboard,
    "自動補貨清單": page_list,
    "商品明細": page_detail,
    "補貨單確認": page_confirm,
}[page]()
