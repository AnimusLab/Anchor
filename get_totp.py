import os
import psycopg2
from urllib.parse import urlparse

with open("anchor-web/server/.env") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=")[1].strip().strip('\"\'')
            break

url = urlparse(db_url)
conn = psycopg2.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = conn.cursor()
cur.execute("SELECT totp_secret FROM regulatory_officials WHERE id='AUD-RB-INDIA-665'")
print(cur.fetchone()[0])
