import os, base64, time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# Allow your Docebo and GitHub Pages origins to call this relay
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://docebo-netflix.github.io",
        "https://YOUR-DOCEBO-DOMAIN"  # e.g., https://netflixsandbox.docebosaas.com
    ],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

ENDPOINT = os.environ["WATERSHED_ENDPOINT"]   # e.g. https://.../lrs (NO trailing slash)
KEY = os.environ["WATERSHED_KEY"]
SECRET = os.environ["WATERSHED_SECRET"]
AUTH = "Basic " + base64.b64encode(f"{KEY}:{SECRET}".encode()).decode()

VERBS = {
    "initialized": "http://adlnet.gov/expapi/verbs/initialized",
    "terminated":  "http://adlnet.gov/expapi/verbs/terminated",
    "interacted":  "http://adlnet.gov/expapi/verbs/interacted",
    "experienced": "http://adlnet.gov/expapi/verbs/experienced",
    "viewed":      "http://adlnet.gov/expapi/verbs/viewed",
}

@app.post("/track")
async def track(req: Request):
    data = await req.json()
    eventType  = data.get("eventType", "experienced")
    userEmail  = data.get("userEmail", "anon@example.com")
    userName   = data.get("userName", "Anonymous")
    activityId = data.get("activityId", "https://docebo-netflix.github.io/xapi-tracking/")
    courseId   = data.get("courseId")
    durationSec= data.get("durationSec")

    verbId = VERBS.get(eventType, VERBS["experienced"])
    statement = {
        "actor": {
            "objectType": "Agent",
            "mbox": f"mailto:{userEmail}",
            "name": userName
        },
        "verb": { "id": verbId, "display": { "en-US": eventType } },
        "object": {
            "objectType": "Activity",
            "id": activityId,
            "definition": {
                "name": { "en-US": "XAPI Tracking Test Page" },
                "type": "http://adlnet.gov/expapi/activities/lesson"
            }
        },
        "context": {
            "platform": "Docebo",
            **({"contextActivities": {"grouping": [{"id": courseId}]}} if courseId else {})
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    if eventType == "terminated" and isinstance(durationSec, (int, float)):
        statement["result"] = { "duration": f"PT{int(round(durationSec))}S" }  # ISO-8601

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{ENDPOINT}/statements",
            headers={
                "Content-Type": "application/json",
                "X-Experience-API-Version": "1.0.3",
                "Authorization": AUTH
            },
            json=statement
        )
    return {"ok": r.is_success, "status": r.status_code, "body": r.text if not r.is_success else None}
