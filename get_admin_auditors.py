import os
import jwt
import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

# Correct path to the .env file in anchor-web
with open("d:/anchor-web/server/.env") as f:
    for line in f:
        if line.startswith("ANCHOR_MASTER_KEY="):
            key = line.split("=")[1].strip().strip('\"\'')
            break

token = jwt.encode(
    {"sub": "root", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
    key,
    algorithm="HS256"
)

req = Request(
    "https://animuslab-anchor.hf.space/api/oversight/admin/auditors",
    headers={"Authorization": "Bearer " + token}
)

resp = urlopen(req).read().decode()
auditors = json.loads(resp)
for a in auditors:
    if a.get("id") == "AUD-RB-INDIA-665":
        print("SECRET:", a.get("totp_secret"))
