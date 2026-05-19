import sys
sys.path.append("d:/anchor-web/server")

from database import SessionLocal
from models import Organization, Hub, EnterpriseUser, RegulatoryOfficial, LedgerEntry, ForensicRequest, EnforcementNotice, AuditTrailEntry

db = SessionLocal()
try:
    print("Organizations:", db.query(Organization).count())
    for org in db.query(Organization).all():
        print(f"  - {org.id}: {org.display_name} ({org.region})")
        
    print("Hubs:", db.query(Hub).count())
    for hub in db.query(Hub).all():
        print(f"  - {hub.id}: {hub.display_name} (Key: {hub.regional_key})")
        
    print("Enterprise Users:", db.query(EnterpriseUser).count())
    for u in db.query(EnterpriseUser).all():
        print(f"  - {u.id}: {u.email} ({u.hub_id})")
        
    print("Regulatory Officials:", db.query(RegulatoryOfficial).count())
    for r in db.query(RegulatoryOfficial).all():
        print(f"  - {r.id}: {r.email} ({r.department})")
        
    print("Ledger Entries:", db.query(LedgerEntry).count())
    print("Forensic Requests:", db.query(ForensicRequest).count())
    print("Enforcement Notices:", db.query(EnforcementNotice).count())
    print("Audit Trail Entries:", db.query(AuditTrailEntry).count())
finally:
    db.close()
