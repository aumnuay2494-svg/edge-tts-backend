import os
import re
import tempfile
from typing import Optional

import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Edge TTS Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

VOICE_WHITELIST = {
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-XiaohanNeural",
    "zh-CN-XiaomengNeural",
    "zh-CN-XiaomoNeural",
    "zh-CN-XiaoruiNeural",
    "zh-CN-XiaoshuangNeural",
    "zh-CN-XiaoxuanNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-YunjianNeural",
    "zh-CN-YunyangNeural",
    "zh-CN-YunhaoNeural",
    "zh-CN-YunxiaNeural",
}

PERCENT_RE = re.compile(r"^[+-]?\d+%$")

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=12000)
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: Optional[str] = "+0Hz"


def clean_percent(value: str, default: str = "+0%") -> str:
    value = (value or default).strip()
    if not PERCENT_RE.match(value):
        return default
    # Edge accepts roughly -100% to +100%; keep UI values conservative.
    try:
        n = int(value.replace("%", ""))
        n = max(-100, min(100, n))
        return f"{n:+d}%"
    except Exception:
        return default

@app.get("/")
async def root():
    return {
        "ok": True,
        "service": "Edge TTS Backend",
        "usage": "POST /tts with JSON: {text, voice, rate, volume}",
    }

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/voices")
async def voices():
    return {"voices": sorted(VOICE_WHITELIST)}

@app.post("/tts")
async def tts(req: TTSRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is empty")
    if len(text) > 12000:
        raise HTTPException(status_code=400, detail="text too long; max 12000 chars")

    voice = req.voice if req.voice in VOICE_WHITELIST else "zh-CN-XiaoxiaoNeural"
    rate = clean_percent(req.rate, "+0%")
    volume = clean_percent(req.volume, "+0%")

    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
        )
        await communicate.save(path)
        with open(path, "rb") as f:
            audio = f.read()
        if not audio:
            raise HTTPException(status_code=502, detail="empty audio from edge-tts")
        safe_name = "edge_tts.mp3"
        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}"',
                "Cache-Control": "no-store",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))
