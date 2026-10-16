"""假資料與補貨計算邏輯（規格 D、F）。"""

from datetime import date, timedelta

STORE_NAME = "統家便利商店 示範門市"

SAFETY_RATE = 0.20      # 安全庫存 = 預測 × 20%
LOW_STOCK_RATE = 0.50   # 低庫存：現有庫存 < 預測 × 50%
SPECIAL_RATE = 3        # 特殊訂單：店長量 > 預測 × 3

STATUS_NORMAL = "🟢 正常"
STATUS_SUGGEST = "🔵 建議補貨"
STATUS_LOW = "🟠 低庫存"
STATUS_SPECIAL = "🔴 特殊訂單"

STATUS_NOTE = {
    STATUS_NORMAL: "庫存足夠，不需補貨。",
    STATUS_SUGGEST: "系統計算後需要補貨。",
    STATUS_LOW: "目前庫存明顯低於預測需求。",
    STATUS_SPECIAL: "店長修改後的數量明顯高於平常需求。",
}

# 最近 7 天銷售量（由舊到新）與今晚盤點的現有庫存
PRODUCTS = [
    {"name": "鮪魚御飯糰", "category": "鮮食", "sales": [30, 28, 32, 35, 30, 40, 43], "stock": 6},
    {"name": "三明治", "category": "鮮食", "sales": [15, 14, 16, 18, 15, 17, 17], "stock": 3},
    {"name": "茶葉蛋", "category": "鮮食", "sales": [20, 22, 18, 25, 21, 19, 22], "stock": 15},
    {"name": "鮮奶", "category": "乳品", "sales": [12, 10, 14, 11, 13, 12, 12], "stock": 9},
    {"name": "礦泉水", "category": "飲料", "sales": [18, 20, 22, 19, 21, 24, 23], "stock": 22},
    {"name": "雨衣", "category": "日用品", "sales": [4, 5, 6, 3, 7, 5, 5], "stock": 3},
    {"name": "無糖綠茶", "category": "飲料", "sales": [25, 30, 28, 26, 32, 35, 34], "stock": 50},
    {"name": "泡麵", "category": "食品", "sales": [8, 6, 9, 7, 10, 8, 8], "stock": 40},
]


def sales_dates(today=None):
    """最近 7 天的日期（不含今天），由舊到新。"""
    today = today or date.today()
    return [today - timedelta(days=i) for i in range(7, 0, -1)]


def calc(product):
    """每一步都先四捨五入成整數，畫面上的算式才會剛好對得起來。"""
    total = sum(product["sales"])
    forecast = round(total / 7)
    safety = round(forecast * SAFETY_RATE)
    suggested = max(0, forecast + safety - product["stock"])
    return {"total": total, "forecast": forecast, "safety": safety, "suggested": suggested}


def is_special(final_qty, forecast):
    return final_qty > forecast * SPECIAL_RATE


def status_of(stock, forecast, suggested, final_qty):
    """優先順序：特殊訂單 > 低庫存 > 建議補貨 > 正常。"""
    if is_special(final_qty, forecast):
        return STATUS_SPECIAL
    if stock < forecast * LOW_STOCK_RATE:
        return STATUS_LOW
    if suggested > 0:
        return STATUS_SUGGEST
    return STATUS_NORMAL
