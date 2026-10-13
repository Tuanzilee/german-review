"""產生 App 用的預錄音檔（微軟神經語音）。

優先用 Azure 語音正式服務（跟 edge-tts 是同一套聲音）；沒有金鑰時才退回 edge-tts。
Azure 金鑰放在 repo 外的 ~/.config/german-review/azure.env（不要 commit、不要貼到對話）：
    AZURE_SPEECH_KEY=…
    AZURE_SPEECH_REGION=eastasia

用法：
    ~/.venvs/tts/bin/python tools/gen_audio.py
（edge-tts 備援要先 python3 -m venv ~/.venvs/tts && ~/.venvs/tts/bin/pip install edge-tts）

只會產生「新增或文字有改過」的音檔；audio/index.json 記錄每個檔案當初念的文字和聲音。
"""
import asyncio, json, os, re, urllib.request
from xml.sax.saxutils import escape

# 讀 repo 外的 Azure 設定檔
ENV_FILE = os.path.expanduser('~/.config/german-review/azure.env')
if os.path.exists(ENV_FILE):
    for line in open(ENV_FILE):
        if '=' in line and not line.lstrip().startswith('#'):
            k, val = line.strip().split('=', 1)
            os.environ.setdefault(k.strip(), val.strip())
AZURE_KEY = os.environ.get('AZURE_SPEECH_KEY')
AZURE_REGION = os.environ.get('AZURE_SPEECH_REGION', 'eastasia')
if not AZURE_KEY:
    import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'audio')
VOICES = {'m': 'de-DE-ConradNeural', 'f': 'de-DE-SeraphinaMultilingualNeural', 'k': 'de-DE-KatjaNeural'}
RATE = '-10%'          # Seraphina 原速偏快，整體放慢一點
# 單字、例句用 Katja：Seraphina 是多語語音，單獨一個字時會誤判成英文（如 Koreanisch 念成英文腔）
WORD_VOICE = 'k'


def tts_text(text):
    # 拼字句「L – I – N」改成逗號，一個字母一個字母念
    return re.sub(r'\s[–-]\s', ', ', text)


def jobs():
    vocab = json.load(open(os.path.join(ROOT, 'vocab.json')))
    dialogues = json.load(open(os.path.join(ROOT, 'dialogues.json')))
    for v in vocab:
        # tts / tts_ex：畫面顯示的拼法和要念的不同時才填（例：課本拼 Tschüs，音檔念短音 Tschüss）
        yield f"{v['id']}.mp3", v.get('tts', v['de']), WORD_VOICE
        yield f"{v['id']}_ex.mp3", v.get('tts_ex', v['example_de']), WORD_VOICE
        # 動詞變位練習用：「du kommst」這種代名詞＋動詞
        for p, form in (v.get('conj') or {}).items():
            pron = {'er/sie/es': 'er', 'sie/Sie': 'Sie'}.get(p, p)
            yield f"{v['id']}_c_{pron}.mp3", f"{pron} {form}", WORD_VOICE
    # 疑問詞配對練習的整句
    for w in json.load(open(os.path.join(ROOT, 'wfragen.json'))):
        yield f"{w['id']}.mp3", w['q'], WORD_VOICE
    for d in dialogues:
        for i, line in enumerate(d['lines']):
            yield f"{d['id']}_{i:02d}.mp3", line.get('tts', line['de']), d['voices'][line['speaker']]


def azure_save(text, voice, path):
    ssml = (f"<speak version='1.0' xml:lang='de-DE'><voice name='{voice}'>"
            f"<prosody rate='{RATE}'>{escape(text)}</prosody></voice></speak>")
    req = urllib.request.Request(
        f'https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1',
        data=ssml.encode('utf-8'), method='POST',
        headers={'Ocp-Apim-Subscription-Key': AZURE_KEY, 'Content-Type': 'application/ssml+xml',
                 'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3', 'User-Agent': 'german-review'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    if not data:
        raise RuntimeError('Azure 回傳空音檔')
    open(path, 'wb').write(data)


async def main():
    os.makedirs(AUDIO, exist_ok=True)
    index_path = os.path.join(AUDIO, 'index.json')
    index = json.load(open(index_path)) if os.path.exists(index_path) else {}
    todo = [(f, t, v) for f, t, v in jobs()
            if index.get(f) != {'text': t, 'voice': VOICES[v]} or not os.path.exists(os.path.join(AUDIO, f))]
    print(f'需要產生 {len(todo)} 個音檔')
    sem = asyncio.Semaphore(4)

    print('使用 Azure 語音正式服務' if AZURE_KEY else '沒有 Azure 金鑰，改用 edge-tts')

    async def one(f, text, v):
        async with sem:
            for attempt in range(3):
                try:
                    if AZURE_KEY:
                        await asyncio.to_thread(azure_save, tts_text(text), VOICES[v], os.path.join(AUDIO, f))
                    else:
                        await edge_tts.Communicate(tts_text(text), VOICES[v], rate=RATE).save(os.path.join(AUDIO, f))
                    index[f] = {'text': text, 'voice': VOICES[v]}
                    return
                except Exception as e:
                    # 失敗時 edge-tts 會留下 0 位元組的空檔，要刪掉，App 才會改用裝置語音
                    path = os.path.join(AUDIO, f)
                    if os.path.exists(path) and os.path.getsize(path) == 0:
                        os.remove(path)
                    if attempt == 2:
                        print(f'失敗：{f}（{str(e)[:60]}）')
                    await asyncio.sleep(2)

    await asyncio.gather(*(one(*j) for j in todo))
    # 只保留目前資料還用得到的紀錄
    wanted = {f for f, _, _ in jobs()}
    index = {k: index[k] for k in sorted(index) if k in wanted}
    json.dump(index, open(index_path, 'w'), ensure_ascii=False, indent=1)
    stale = sorted(set(os.listdir(AUDIO)) - wanted - {'index.json'})
    if stale:
        print('這些音檔已沒有對應資料，可手動移到垃圾桶：', ' '.join(stale))
    print(f'完成，共 {len(index)} 個音檔')


asyncio.run(main())
