import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import requests
import uuid

app = FastAPI(title="Public APIs Tools Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Public APIs Tools Hub Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Basic health endpoint"""
    response = {
        "backend": "✅ Running",
        "database": "ℹ️ Not required for this demo",
    }
    return response


# ------- Tools metadata (frontend may use this to list tools) ------
@app.get("/api/tools")
def list_tools():
    tools = [
        {
            "slug": "ip-lookup",
            "name": "IP Lookup",
            "description": "Find your public IP and geolocation details",
            "endpoint": "/api/ip",
            "category": "Networking"
        },
        {
            "slug": "url-shortener",
            "name": "URL Shortener",
            "description": "Shorten long links using TinyURL",
            "endpoint": "/api/shorten",
            "category": "Links"
        },
        {
            "slug": "qr-generator",
            "name": "QR Code Generator",
            "description": "Create a QR code from any text or URL",
            "endpoint": "/api/qr",
            "category": "Utilities"
        },
        {
            "slug": "exchange-rates",
            "name": "Exchange Rates",
            "description": "Get latest exchange rates (exchangerate.host)",
            "endpoint": "/api/exchange",
            "category": "Finance"
        },
        {
            "slug": "weather",
            "name": "Weather",
            "description": "Current weather by city (Open-Meteo)",
            "endpoint": "/api/weather",
            "category": "Weather"
        },
        {
            "slug": "random-joke",
            "name": "Random Joke",
            "description": "Get a random joke",
            "endpoint": "/api/joke",
            "category": "Fun"
        },
        {
            "slug": "random-quote",
            "name": "Random Quote",
            "description": "Get an inspirational quote",
            "endpoint": "/api/quote",
            "category": "Fun"
        },
        {
            "slug": "cat-image",
            "name": "Random Cat Image",
            "description": "Grab a cute cat photo",
            "endpoint": "/api/cat",
            "category": "Images"
        },
        {
            "slug": "dog-image",
            "name": "Random Dog Image",
            "description": "Grab a cute dog photo",
            "endpoint": "/api/dog",
            "category": "Images"
        },
        {
            "slug": "uuid",
            "name": "UUID Generator",
            "description": "Generate a v4 UUID",
            "endpoint": "/api/uuid",
            "category": "Utilities"
        },
        {
            "slug": "lorem-ipsum",
            "name": "Lorem Ipsum",
            "description": "Generate placeholder text",
            "endpoint": "/api/lorem",
            "category": "Content"
        },
        {
            "slug": "email-validator",
            "name": "Email Validator",
            "description": "Validate email format and MX using RFC rules",
            "endpoint": "/api/validate-email",
            "category": "Validation"
        },
        {
            "slug": "placeholder-image",
            "name": "Placeholder Image URL",
            "description": "Get on-the-fly placeholder image (Picsum)",
            "endpoint": "https://picsum.photos/seed/{seed}/{w}/{h}",
            "category": "Images"
        },
    ]
    return {"tools": tools}


# --------------------- Tool Endpoints ---------------------

@app.get("/api/ip")
def ip_lookup():
    # Try multiple free sources
    sources = [
        "https://ipapi.co/json/",
        "https://ipwho.is/",
        "https://api.ipify.org?format=json",
    ]
    last_error = None
    for url in sources:
        try:
            r = requests.get(url, timeout=8)
            if r.ok:
                data = r.json() if "json" in r.headers.get("content-type", "") else {"raw": r.text}
                return {"source": url, "data": data}
        except Exception as e:
            last_error = str(e)
            continue
    raise HTTPException(status_code=502, detail=f"All sources failed: {last_error}")


@app.get("/api/shorten")
def shorten_url(url: str = Query(..., description="URL to shorten")):
    try:
        resp = requests.get("https://tinyurl.com/api-create.php", params={"url": url}, timeout=10)
        if resp.ok:
            return {"original": url, "short": resp.text.strip()}
        raise HTTPException(status_code=502, detail="TinyURL failed")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/qr")
def qr_redirect(text: str = Query(..., description="Text to encode")):
    # Use goqr public API to return a PNG QR code
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={requests.utils.quote(text)}"
    return RedirectResponse(qr_url)


@app.get("/api/exchange")
def exchange_rates(base: str = Query("USD")):
    url = f"https://api.exchangerate.host/latest?base={base.upper()}"
    try:
        r = requests.get(url, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=502, detail="exchangerate.host failed")
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/weather")
def weather(city: str = Query(...)):
    try:
        # Geocode city name -> lat/lon via Open-Meteo geocoding
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        if not geo.ok or not geo.json().get("results"):
            raise HTTPException(status_code=404, detail="City not found")
        g = geo.json()["results"][0]
        lat, lon = g["latitude"], g["longitude"]
        meteo = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=10,
        )
        if not meteo.ok:
            raise HTTPException(status_code=502, detail="Open-Meteo failed")
        data = meteo.json()
        data["location"] = {"name": g.get("name"), "country": g.get("country"), "lat": lat, "lon": lon}
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/joke")
def random_joke():
    sources = [
        "https://official-joke-api.appspot.com/random_joke",
        "https://v2.jokeapi.dev/joke/Any?type=single",
    ]
    for url in sources:
        try:
            r = requests.get(url, timeout=8)
            if r.ok:
                j = r.json()
                if "setup" in j and "punchline" in j:
                    return {"text": f"{j['setup']} {j['punchline']}"}
                if "joke" in j:
                    return {"text": j["joke"]}
        except Exception:
            continue
    raise HTTPException(status_code=502, detail="All joke sources failed")


@app.get("/api/quote")
def random_quote():
    try:
        r = requests.get("https://api.quotable.io/random", timeout=8)
        if r.ok:
            q = r.json()
            return {"content": q.get("content"), "author": q.get("author")}
        raise HTTPException(status_code=502, detail="quotable failed")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/cat")
def cat_image():
    # Cataas supports direct image, return redirect so browser loads it
    return RedirectResponse("https://cataas.com/cat?type=small")


@app.get("/api/dog")
def dog_image():
    res = requests.get("https://dog.ceo/api/breeds/image/random", timeout=8)
    if not res.ok:
        raise HTTPException(status_code=502, detail="dog.ceo failed")
    return res.json()


@app.get("/api/uuid")
def uuid_gen():
    return {"uuid": str(uuid.uuid4())}


@app.get("/api/lorem")
def lorem(paragraphs: int = Query(2, ge=1, le=10)):
    try:
        r = requests.get(f"https://loripsum.net/api/{paragraphs}/short/plaintext", timeout=8)
        if r.ok:
            return {"text": r.text}
        raise HTTPException(status_code=502, detail="loripsum failed")
    except Exception as e:
        # fallback simple generator
        text = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. ") * 30
        paras = [text.strip() for _ in range(paragraphs)]
        return {"text": "\n\n".join(paras)}


@app.get("/api/validate-email")
def validate_email(email: str = Query(...)):
    try:
        from email_validator import validate_email as ve, EmailNotValidError
        try:
            info = ve(email, check_deliverability=True)
            return {
                "email": info.email,
                "normalized": info.normalized,
                "domain": info.domain,
                "local": info.local_part,
                "mx": [mx.hostname for mx in (info.mx or [])],
                "valid": True,
            }
        except EmailNotValidError as e:
            return JSONResponse(status_code=200, content={"email": email, "valid": False, "reason": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
