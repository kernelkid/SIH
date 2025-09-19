from init_db import db
from datetime import datetime

class Consent(db.Model):
    __tablename__ = "consents"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # Reference users.id
    consent_type = db.Column(db.String(50), nullable=False)
    consent_given = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship("User", backref="consents")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "consent_type": self.consent_type,
            "consent_given": self.consent_given,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<Consent user_id={self.user_id}>"
