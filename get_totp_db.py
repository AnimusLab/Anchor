import sys
sys.path.append("d:/anchor-web/server")

from database import SessionLocal
from models import RegulatoryOfficial

db = SessionLocal()
try:
    user = db.query(RegulatoryOfficial).filter(RegulatoryOfficial.id == "AUD-RB-INDIA-665").first()
    if user:
        print("TOTP_SECRET:", user.totp_secret)
        # Generate the current OTP
        try:
            import pyotp
            totp = pyotp.TOTP(user.totp_secret)
            print("CURRENT_OTP:", totp.now())
        except ImportError:
            print("pyotp not installed, could not generate OTP code.")
    else:
        print("User AUD-RB-INDIA-665 not found in the database.")
finally:
    db.close()
