from fastapi import FastAPI, Header, HTTPException
from core.config import READ_TOKEN, ADMIN_TOKEN

app = FastAPI(title='Apotheon Website Connector', version='0.5.0')

def require_read(auth: str = Header(None)):
    if auth != f'Bearer {READ_TOKEN}':
        raise HTTPException(status_code=401)

def require_admin(auth: str = Header(None)):
    if auth != f'Bearer {ADMIN_TOKEN}':
        raise HTTPException(status_code=401)

@app.get('/health')
def health():
    return {'ok': True}
