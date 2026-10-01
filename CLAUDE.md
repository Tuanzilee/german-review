# CLAUDE.md — german-review

## Repo 用途
hai 的基礎德文複習 PWA（手機為主）。單頁 `index.html` + runtime fetch 兩個 JSON，無 build、無框架。架構仿 `stats-quiz`。

## 檔案結構
```
index.html      ← 全部 UI 與邏輯（源 = 部署檔，直接改）
vocab.json      ← 單字庫
dialogues.json  ← 會話庫
sw.js           ← Service Worker（網路優先 + 離線快取）
manifest.json / icon-192.png / icon-512.png
```

## 資料 schema
`vocab.json` 每筆：
```
id          L{課}_W{週}_V{三位數}，例 L1_W2_V007（不要改既有 id，進度綁 id）
lektion     課次（1–3）
week        上課週次
source      plaud | textbook | both
de          德文（名詞含冠詞，如 "die Straße"）
zh          中文意思
pos         noun / verb / phrase / question / pronoun / prep / adj / lang / country
article     der | die | das | null（名詞必填）
plural      複數形或 null
conj        動詞變位 {ich, du, er/sie/es, Sie} 或 null
example_de / example_zh  例句
tags        ["期中"] / ["期末"]
```
`dialogues.json` 每筆：`id`（L1_D01）、`lektion`、`week`、`title`、`scene`、`lines[{speaker, de, zh}]`。

## 每週新增內容（hai 說「更新德文 W{n}」）
1. 用 Plaud 連接器找當週德語錄音（名稱含「德語」），讀 note 摘要；需要細節再讀 transcript
2. 課本 PDF：`~/Desktop/P. 進行中專案/FJU psy/02_修課/1151/_課本/Schritte-International-Neu-A1-1（大二德文）.pdf`
   - 掃描檔，要 `pdftoppm -f N -l N -r 75 -png` 轉圖再讀；**PDF 頁碼 = 課本頁碼 + 2**
3. 錄音抓「老師教了什麼」，課本校正拼字／冠詞／複數；追加到 JSON 尾端，id 接續編號
4. 會話：依課堂情境自己改寫短對話，**不要逐字搬課本對話**（repo 公開、課綱禁止非法重製）
5. 跑檢查：`python3 check.py`
6. bump `sw.js` 的 `CACHE` 版本號
7. commit & push（Pages 1–2 分鐘後更新）
8. 把不確定的條目列給 hai 確認

## 勘誤
hai 指出哪個字錯 → 用 `de` 或 `id` 找到該筆 → 改欄位 → bump `sw.js` → commit「修正 L1_W2_V007 …」→ push。

## 範圍設定
`index.html` 的 `SCOPES`：期中範圍 = Lektion 1–2（W8 期中），期末考 Lektion 2–3。加新週次時記得在 `SCOPES` 補 `w4`、`w5`… 的按鈕。
