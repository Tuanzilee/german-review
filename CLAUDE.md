# CLAUDE.md — german-review

## Repo 用途
hai 的基礎德文複習 PWA（手機為主）。單頁 `index.html` + runtime fetch 兩個 JSON，無 build、無框架。架構仿 `stats-quiz`。

## 檔案結構
```
index.html      ← 全部 UI 與邏輯（源 = 部署檔，直接改）
vocab.json      ← 單字庫
dialogues.json  ← 會話庫
wfragen.json    ← 疑問詞配對題
sw.js           ← Service Worker（網路優先 + 離線快取）
manifest.json / icon-192.png / icon-512.png
audio/          ← 預錄音檔（{id}.mp3 單字、{id}_ex.mp3 例句、{id}_c_{人稱}.mp3 變位、{會話id}_{兩位數行號}.mp3）＋ index.json
tools/gen_audio.py ← 產生音檔（edge-tts 微軟神經語音，只補新增／改過文字的）
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
tts / tts_ex  （選填）音檔要念的文字，跟畫面拼法不同時才填；會話每句也可加 tts
accept      （選填）拼字練習也算對的其他正確拼法，例 Tschüs 的 ["Tschüss"]
spell_tip   （選填）拼錯時顯示的規則提示；tags 含「易錯」的會進首頁「⚠️ 考卷易錯」範圍
```

## 練習模式
- 單字卡（Leitner 5 盒）、聽力 4 選 1、會話跟讀
- ✍️ 拼字：看中文＋聽音檔 → 打德文；大小寫要對（老師強調名詞大寫），忽略句尾標點；`de` 含「…」或「/」的句型框架不出題；錯題本裡的字優先
- 🔤 動詞變位：所有有 `conj` 的動詞 × 人稱，du heißt／du sprichst／du bist 每輪必出；答完顯示規則說明（`conjWhy`）與音檔 `{id}_c_{ich|du|er|Sie}.mp3`
- ❓ 疑問詞配對：`wfragen.json`（id WF01…、q、zh、answer），音檔 `WF01.mp3`
- 考卷易錯（2026-10-06 W4 學習單）：-isch 寫成 -ish、Deutsch 漏 t、j 寫成 y、疑問詞配錯動詞 → 對應易錯範圍＋spell_tip＋疑問詞配對
- 會話 L1_D10 是 hai 的自我介紹稿（Ming、über 30、Neu-Taipeh、Psychologie、Vibe-Coding mit KI、Vorträge），期末 200 字作業初稿；老師的 Marie 範文是老師自編教材，**不要原文放進公開 repo**
- 老師 W4 說必背三樣：單字拼字、代名詞＋動詞搭配（du bist）、一般動詞詞尾變化（考前要整理）→ 對應拼字、變位兩個模式
`dialogues.json` 每筆：`id`（L1_D01）、`lektion`、`week`、`title`、`scene`、`voices`（每個角色的聲音，`m`＝Conrad 男聲、`f`＝Seraphina 女聲，依角色性別指定）、`lines[{speaker, de, zh}]`。

## 語音
hai 選定：單字／例句用 Katja（`de-DE-KatjaNeural`），會話依角色分 Conrad（`de-DE-ConradNeural`）／Seraphina（`de-DE-SeraphinaMultilingualNeural`），整體 `-10%` 語速。App 先播 `audio/` 的 mp3，載入失敗才退回裝置內建語音。

產生音檔：`~/.venvs/tts/bin/python tools/gen_audio.py`（venv 不存在就先 `python3 -m venv ~/.venvs/tts && ~/.venvs/tts/bin/pip install edge-tts`）。edge-tts 借用 Edge 朗讀服務、非正式 API，若失效要告訴 hai，不要自己換別的付費服務。

## 每週新增內容（hai 說「更新德文 W{n}」）
1. 用 Plaud 連接器找當週德語錄音（名稱含「德語」或「德文」）。**Plaud 常把德文聽成英文，摘要不可信**：讀逐字稿，靠老師的中文講解＋課本還原德文；hai 錄音時按的 Highlights 最可靠
2. 課本 PDF：`~/Desktop/P. 進行中專案/FJU psy/02_修課/1151/_課本/Schritte-International-Neu-A1-1（大二德文）.pdf`
   - 掃描檔，要 `pdftoppm -f N -l N -r 75 -png` 轉圖再讀；**PDF 頁碼 = 課本頁碼 + 2**
3. 錄音抓「老師教了什麼」，課本校正拼字／冠詞／複數；追加到 JSON 尾端，id 接續編號
4. 會話：依課堂情境自己改寫短對話，**不要逐字搬課本對話**（repo 公開、課綱禁止非法重製）
5. 產生音檔：`~/.venvs/tts/bin/python tools/gen_audio.py`；新會話記得填 `voices`
   新動詞要填 `conj`，必要時在 `index.html` 的 `conjWhy` 補例外說明
6. 跑檢查：`python3 check.py`（會檢查音檔齊全）
7. bump `sw.js` 的 `CACHE` 版本號
8. commit & push（Pages 1–2 分鐘後更新）
9. 把不確定的條目列給 hai 確認

## 勘誤
hai 指出哪個字錯 → 用 `de` 或 `id` 找到該筆 → 改欄位 → 若改到德文就重跑 `tools/gen_audio.py` → bump `sw.js` → commit「修正 L1_W2_V007 …」→ push。

## 範圍設定
`index.html` 的 `SCOPES`：期中範圍 = Lektion 1–2（W8 期中），期末考 Lektion 2–3。加新週次時記得在 `SCOPES` 補 `w4`、`w5`… 的按鈕。

> 踩坑：Seraphina 是多語語音，**單獨一個字**會自動判斷語言，Koreanisch、Englisch 這類字會念成英文腔。單字一律用純德語的 Katja；Seraphina 只用在整句會話。
> 發音決策：Tschüs 畫面維持課本拼法，音檔念短音 Tschüss（hai 選定，對齊老師「ü 短促」）。
> Nicos Weg（DW 影集，老師 W3 起分段播放）：首頁只放官方連結 https://learngerman.dw.com/en/nicos-weg/c-36519789 ，**不要把影片台詞抄進公開 repo**（DW 版權）。hai 2026-10-06 決定暫不加數字／同情境會話，等老師放完再說。
