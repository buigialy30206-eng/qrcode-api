"""
QR Code Generator API
Pure Python — qrcode + Pillow. Zero external APIs.
Returns PNG image.
"""

import base64
import io

import qrcode
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse

import time as _t, threading as _th
_rl_win, _rl_max, _rl_hits, _rl_lk = 60, 60, {}, _th.Lock()

async def _rate_limit(request):
    from fastapi import Request, HTTPException
    ip = (request.headers.get('X-Forwarded-For','') or request.headers.get('X-Real-IP','') or (request.client.host if request.client else '127.0.0.1')).split(',')[0].strip()
    now = _t.time()
    with _rl_lk:
        e = _rl_hits.get(ip)
        if e:
            if now - e['s'] > _rl_win: e['s'], e['c'] = now, 1
            else:
                e['c'] += 1
                if e['c'] > _rl_max: raise HTTPException(429, 'Too many requests')
        else: _rl_hits[ip] = {'s': now, 'c': 1}
    return True

app = FastAPI(title="QR Code Generator API", version="1.0.0", dependencies=[Depends(_rate_limit)])
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])






@app.get("/")
async def root():
    return {"service": "QR Code Generator API", "version": "1.0.0"}


@app.get("/generate")
async def generate(
    text: str = Query(..., description="Text or URL to encode"),
    size: int = Query(300, ge=100, le=1000, description="Image size in pixels"),
    format: str = Query("png", description="Output format: png, base64"),
):
    """Generate QR code image."""
    qr = qrcode.QRCode(version=None, box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))

    if format == "base64":
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return JSONResponse({"qr_code": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()})

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
