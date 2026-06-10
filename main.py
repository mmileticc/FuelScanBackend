from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import random


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = "https://jybatqpvokssutompyto.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp5YmF0cXB2b2tzc3V0b21weXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwMTUwMjIsImV4cCI6MjA5NjU5MTAyMn0.W-zZN3dLJDn18m3qoL0EP8s4g2K32vFO7tyIWD-oN_Q"

class ScanRequest(BaseModel):
    url: str

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Nedostaje Authorization header")

    token = authorization.split(" ", 1)[1].strip()

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )

    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Nevažeći token")

    user = res.json()
    return {"uid": user["id"], "email": user.get("email")}

@app.post("/parse-receipt")
async def parse_receipt(data: ScanRequest, user=Depends(get_current_user)):
    rnd = random.randint(1, 100)
    rndPrice = random.randint(180, 220)
    return {
        "status": "success",
        "user_id": user["uid"],
        "station": "NIS Petrol – Bulevar",
        "fuel_type": "Euro Premium BMB 95",
        "liters": rnd,
        "price_per_l": rndPrice,
        "total": rnd * rndPrice,
        "date": "2026-06-09T14:23:00",
        "raw_url": data.url,
    }
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)