from init_db import db
from datetime import datetime

class Consent(db.Model):
    __tablename__ = "consents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)  
    gps = db.Column(db.Boolean, default=False)
    notifications = db.Column(db.Boolean, default=False)
    motion_activity = db.Column(db.Boolean, default=False)
    ts = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "gps": self.gps,
            "notifications": self.notifications,
            "motion_activity": self.motion_activity,
            "ts": self.ts.isoformat() if self.ts else None
        }

    def __repr__(self):
        return f"<Consent user_id={self.user_id}>"
