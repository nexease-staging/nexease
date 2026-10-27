"""Prepare local environment files without overwriting existing credentials."""
from pathlib import Path
import secrets
from cryptography.fernet import Fernet
from dotenv import dotenv_values
root=Path(__file__).resolve().parents[1]
path=root/'.env'
if not path.exists():path.write_text((root/'.env.example').read_text(),encoding='utf-8')
values=dotenv_values(path);example=dotenv_values(root/'.env.example')
text=path.read_text(encoding='utf-8')
for key,value in example.items():
 if key not in values:text+='\n'+key+'='+str(value or '')
values=dotenv_values(stream=__import__('io').StringIO(text))
for key,new in [('OWNER_ENCRYPTION_KEY',Fernet.generate_key().decode()),('DJANGO_SECRET_KEY',secrets.token_urlsafe(50))]:
 if values.get(key) in (None,'','REPLACE_WITH_A_LONG_RANDOM_SECRET'):
  lines=text.splitlines();text='\n'.join((key+'='+new) if line.startswith(key+'=') else line for line in lines)+'\n'
path.write_text(text,encoding='utf-8')
f=root/'frontend'/'.env.local'
if not f.exists():f.write_text('NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1\n',encoding='utf-8')
print('Environment files prepared. Existing credentials preserved. Owner encryption key generated if missing; keep .env backed up privately.')
print('Now edit .env to configure MongoDB Atlas. AI and payments remain disabled until explicitly enabled. Never commit .env.')
