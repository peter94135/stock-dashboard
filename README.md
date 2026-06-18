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
- 依題材分區，每區一張即時報價表（Last / Day Volume / Day~Year Change / P/E / Market Cap）
- 新增／刪除題材、新增／刪除股票，點欄位標題排序，漲綠跌紅
- 自動更新（30 秒～5 分鐘可選）
- 設定存於瀏覽器 localStorage；若設定 Firebase 則同步到雲端

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

## 資料來源說明
- 盤中約 15 分鐘延遲，非逐筆即時。
- 線上版的 P/E、市值若公開 proxy 取不到，會顯示「—」，其餘行情照常。
