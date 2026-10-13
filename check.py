"""資料檢查：python3 check.py"""
import json, os, sys
vocab = json.load(open('vocab.json'))
dialogues = json.load(open('dialogues.json'))
errors, warnings = [], []
ids = [v['id'] for v in vocab] + [d['id'] for d in dialogues]
dup = {i for i in ids if ids.count(i) > 1}
if dup: errors.append(f'重複 id：{dup}')
for v in vocab:
    if v['pos'] == 'noun' and v['article'] not in ('der', 'die', 'das'):
        errors.append(f"{v['id']} {v['de']}：名詞沒有冠詞")
    if v['pos'] == 'noun' and not v['de'].startswith(v['article'] + ' '):
        errors.append(f"{v['id']} {v['de']}：de 欄位沒有以冠詞開頭")
    if v['pos'] == 'verb' and not v['conj']:
        errors.append(f"{v['id']} {v['de']}：動詞沒有變位")
    for k in ('de', 'zh', 'example_de', 'example_zh'):
        if not v.get(k): errors.append(f"{v['id']}：缺 {k}")
for d in dialogues:
    for l in d['lines']:
        if not (l.get('de') and l.get('zh') and l.get('speaker')):
            errors.append(f"{d['id']}：有一句缺欄位")
import os
for v in vocab:
    for f in (v['id'], v['id'] + '_ex'):
        if not os.path.exists(f'audio/{f}.mp3'): warnings.append(f'缺音檔 audio/{f}.mp3（跑 tools/gen_audio.py）')
for v in vocab:
    for p in (v['conj'] or {}):
        f = f"{v['id']}_c_" + {'er/sie/es': 'er', 'sie/Sie': 'Sie'}.get(p, p)
        if not os.path.exists(f'audio/{f}.mp3'): warnings.append(f'缺音檔 audio/{f}.mp3（跑 tools/gen_audio.py）')
for d in dialogues:
    for i, l in enumerate(d['lines']):
        if l['speaker'] not in d.get('voices', {}): errors.append(f"{d['id']}：角色 {l['speaker']} 沒有指定聲音（voices）")
        if not os.path.exists(f"audio/{d['id']}_{i:02d}.mp3"): warnings.append(f"缺音檔 audio/{d['id']}_{i:02d}.mp3（跑 tools/gen_audio.py）")
for w in json.load(open('wfragen.json')):
    if not os.path.exists(f"audio/{w['id']}.mp3"): warnings.append(f"缺音檔 audio/{w['id']}.mp3（跑 tools/gen_audio.py）")
    if w['answer'] not in ('Wie', 'Was', 'Woher', 'Wer'): errors.append(f"{w['id']}：answer 不是四個疑問詞之一")
for v in vocab:
    if v['conj'] and list(v['conj']) != ['ich', 'du', 'er/sie/es', 'wir', 'ihr', 'sie/Sie']:
        errors.append(f"{v['id']} {v['de']}：conj 要有六個人稱 ich/du/er/sie/es/wir/ihr/sie/Sie")
print(f'單字 {len(vocab)}、會話 {len(dialogues)}')
if warnings: print(f'⚠️ 缺 {len(warnings)} 個音檔（App 會改用裝置語音），例如：{warnings[0]}')
empty = [f for f in os.listdir('audio') if f.endswith('.mp3') and os.path.getsize(f'audio/{f}') == 0]
if empty: errors.append(f'有 {len(empty)} 個 0 位元組的空音檔，要刪掉')
print('\n'.join(errors) if errors else '✅ 資料檢查通過')
sys.exit(1 if errors else 0)
