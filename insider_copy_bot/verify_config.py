from pathlib import Path
import json, re

env = Path('.env').read_text()
masked = []
for line in env.splitlines():
    if '=' in line and not line.strip().startswith('#'):
        k,v = line.split('=',1)
        if 'KEY' in k or 'SECRET' in k or 'TOKEN' in k:
            if len(v) > 8:
                v = v[:4] + '***' + v[-4:]
            else:
                v = '***'
        masked.append(f'{k}={v}')
    else:
        masked.append(line)
print('.env (masked):')
print('\n'.join(masked))

print('\nMODE value:')
m = re.search(r'^MODE=(.*)$', env, re.M)
print(m.group(1) if m else 'NOT_SET')

print('\nWHITELIST_TRADERS:')
m = re.search(r'^WHITELIST_TRADERS=(.*)$', env, re.M)
print(m.group(1) if m else 'NOT_SET')

print('\nSIGNAL_ONLY mode active:')
m = re.search(r'^SIGNAL_ONLY=(.*)$', env, re.M)
print(m.group(1) if m else 'NOT_SET')

print('\nTracked wallet addresses:')
wallets = json.loads(Path('data/tracked_wallets.json').read_text())
for w in wallets:
    print(w['address'])