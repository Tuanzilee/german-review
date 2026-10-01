"""資料檢查：python3 check.py"""
import json, sys
vocab = json.load(open('vocab.json'))
dialogues = json.load(open('dialogues.json'))
errors = []
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
print(f'單字 {len(vocab)}、會話 {len(dialogues)}')
print('\n'.join(errors) if errors else '✅ 全部通過')
sys.exit(1 if errors else 0)
