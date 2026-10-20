# 統家門市補貨工作台

新版以原生 HTML / CSS / JavaScript 製作，保留原始 8 項示範商品、7 日移動平均、20% 安全庫存及特殊需求門檻。無外部前端相依套件，不再等待 stlite / Pyodide 載入。

## 啟動新版

在此資料夾執行：

    python -m http.server 8766 --bind 127.0.0.1

瀏覽 http://127.0.0.1:8766 。也可以直接開啟 index.html，但建議使用伺服器，以便瀏覽器穩定保存資料。

## 新版功能

- 合併首頁與補貨清單，三項摘要、搜尋、分類、低庫存與調整篩選。
- 明顯的數量輸入框，輸入 0 表示不補貨；允許最高 999,999 件，拒絕空值、負值及小數。
- 商品側開明細、七日歷史與明日預測圖、計算依據、修改原因。
- 大量特殊需求必須填寫原因並再次確認；修改數量或原因後，先前確認失效。
- 草稿與訂單紀錄儲存在目前瀏覽器 localStorage。送出後鎖定，重整仍保留。
- 訂單 CSV 匯出含系統建議、最終數量、原因及狀態。
- 台灣日期；跨日重新開啟會產生新草稿，保留歷史紀錄。
- 響應式版面、鍵盤操作、原生 modal 焦點管理。

## 示範範圍

這是課堂示範，沒有串接總部、ERP、物流或資料庫。「建立示範訂單」只代表本機保存成功，不能當作總部接單。清除瀏覽器資料會刪除紀錄，應先匯出。

原始資料不含進貨價，故不虛構訂貨金額。模型假設盤點後至明早到貨前無額外需求、無在途量；正式使用應補上前置時間、在途庫存、效期、箱入數、容量與鮮食品類規則。安全庫存 20% 是簡化假設，並非服務水準保證。

## 計算

    預測 = 四捨五入(七日銷售總和 / 7)
    安全庫存 = 四捨五入(預測 * 20%)
    建議 = max(0, 預測 + 安全庫存 - 可用庫存)

特殊需求同時滿足：確認量 > max(建議量, 1) × 3，而且確認量 − 建議量 >= 20。

低庫存獨立判定為：可用庫存 < 預測日需求 × 50%，不再被特殊需求狀態覆蓋。

## 驗證

    node --check app.js
    node test.cjs

測試涵蓋初始 6 項 / 72 件、低庫存、負數小數與空值、特殊需求確認失效、送出鎖定、重複送單、空訂單及儲存失敗回復。

## 靜態部署

將 index.html、styles.css、desktop.css、app.js 放入網站的發布資料夾即可。既有 Cloudflare Pages 專案可使用：

    New-Item -ItemType Directory -Force dist
    Copy-Item index.html,styles.css,desktop.css,app.js dist
    npx wrangler pages deploy dist --project-name tongjia-auto-replenish --branch main

此指令會更新正式站台；本次程式改版不會自行執行。

## 原始 Python 版本

app.py、replenish.py 與 requirements.txt 保留供模型與課堂程式對照；新版入口為 index.html。舊版仍可用 streamlit run app.py 啟動，但不包含新版介面與本機訂單保存功能。

## 檔案

- index.html：新版介面入口
- styles.css：基礎版面與設計樣式
- desktop.css：桌面視覺設計
- app.js：示範資料、補貨規則、互動、儲存與 CSV
- test.cjs：關鍵業務流程回歸測試
