import json, sys
sys.stdout.reconfigure(encoding='utf-8')
nb = json.load(open(r'c:\Projetos\Departamento_Medico_ML\Departamento_Medico_Local.ipynb', encoding='utf-8'))
for i, c in enumerate(nb['cells']):
    if c['cell_type'] != 'code':
        continue
    src = ''.join(c['source'])[:100].replace('\n', ' | ')
    print(f'--- CELL {i}: {src}')
    for o in c.get('outputs', []):
        if 'text' in o:
            t = ''.join(o['text'])
        elif 'data' in o and 'text/plain' in o['data']:
            t = ''.join(o['data']['text/plain'])
        else:
            t = f"[{o.get('output_type')}] (imagem/figura)"
        if len(t) > 3000:
            t = t[:1500] + '\n...[TRUNCADO]...\n' + t[-1500:]
        print('OUT:', t)
    print()
