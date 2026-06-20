# 股票題材儀表板

依題材分區的即時股價儀表板，支援美股、日股（`.T`）、台股（`.TW` / `.TWO`）。
資料來自 Yahoo Finance，題材／股票設定可用 Firebase 跨裝置同步。

## 兩種使用方式

### 1) 線上版（GitHub Pages）
直接開網址即可，股價透過公開 CORS proxy 取得（免費、零設定，尖峰偶爾較慢）。
題材設定若已設好 Firebase 會自動跨裝置同步。

### 2) 本機版（最穩定、最快）
在這個資料夾雙擊 **`啟動儀表板.command`**（或執行 `python3 server.py`），
會用你自己的網路 IP 直連 Yahoo，避開限流與 CORS。瀏覽器開 <http://localhost:8765/>。

## 功能
- 上方題材按鈕（tabs），一次顯示一個題材的即時報價表（Last / Day Volume / Day~Year Change / P/E / Market Cap）
- **只抓「目前選取題材」的股票**，所以切換很快、不會一次抓上百檔（學自 hgvf.github.io 的分類載入做法）
- 報價快取在 localStorage，切換題材／重開即時顯示，背景再更新
- 介面為英文，題材名稱維持中文；股票代號連到 TradingView
- 新增／刪除題材、新增／刪除股票，點欄位標題排序，漲綠跌紅
- 自動更新（30 秒～5 分鐘可選，只更新目前題材）
- 設定存於瀏覽器 localStorage；若設定 Firebase 則同步到雲端
- 主控台輸入 `importHgvfThemes()`（需登入為編輯者）可一鍵把內建 21 個題材覆蓋寫入雲端

## 設定 Firebase 雲端同步（選用）
1. 到 <https://console.firebase.google.com/> 建立專案。
2. 左側 **Build → Firestore Database → 建立資料庫**（地點選 asia-east1，先用「測試模式」）。
3. 專案設定（齒輪）→ 一般 → 你的應用程式 → 新增「Web 應用程式」→ 複製 `firebaseConfig`。
4. 把 `index.html` 裡的 `FIREBASE_CONFIG` 換成你的設定，commit & push。
5. Firestore 規則（Rules）建議：

   ```
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /dashboards/{doc} {
         allow read, write: if true;   // 任何人可讀寫（個人用、低風險）。要鎖定見下方。
       }
     }
   }
   ```

   > 注意：上面規則代表「知道網址的人都能改你的題材」。若要鎖成只有你能改，
   > 可改用 Google 登入並把 write 規則設為 `if request.auth.uid == "你的UID"`。

## 讓線上版也能顯示 P/E、市值（Cloudflare Worker，選用、免費）
Yahoo 的 P/E、市值 API 需要 crumb 授權，公開 proxy 拿不到。部署一個免費 Worker 即可解決：
1. <https://dash.cloudflare.com/> 註冊／登入（免費，不需綁卡）。
2. 左側 **Workers & Pages → Create application → Create Worker** → 命名 → **Deploy**。
3. 進入該 Worker → **Edit code** → 把 `worker.js` 內容整段貼上 → **Deploy**。
4. 複製 Worker 網址（`https://<名稱>.<子網域>.workers.dev`），填到 `index.html` 的 `WORKER_URL`，commit & push。
   - 之後線上版會優先走 Worker（完整 P/E/市值，股價也更快更穩），失敗才回退公開 proxy。

## 資料來源說明
- 盤中約 15 分鐘延遲，非逐筆即時。
- 未設定 Worker 時，線上版的 P/E、市值會顯示「—」（其餘行情照常）；本機版則完整。
