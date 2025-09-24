import os
from typing import List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson.objectid import ObjectId

# Attempt to use system CA certificates for TLS connections (e.g., MongoDB Atlas)
try:
    import certifi  # type: ignore
    _CA_FILE = certifi.where()
except Exception:  # pragma: no cover - optional dependency
    certifi = None  # type: ignore
    _CA_FILE = None

@dataclass
class ReportRecord:
    report_id: str
    created_at: str
    issue_type: str
    text: Optional[str]
    voice_text: Optional[str]
    image_path: Optional[str]
    location: dict
    complaint_text: str
    status: str
    fake: bool
    fake_score: float

class CivicDB:
    def __init__(self):
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB", "civic_eye")
        try:
            # Build connection kwargs. Use CA bundle for Atlas/SRV URIs to avoid SSL handshake issues.
            conn_kwargs = {
                "serverSelectionTimeoutMS": 5000,
            }
            # Heuristic: SRV scheme or mongodb.net host implies TLS is required
            if mongodb_uri.startswith("mongodb+srv://") or "mongodb.net" in mongodb_uri:
                if _CA_FILE:
                    conn_kwargs["tlsCAFile"] = _CA_FILE
                else:
                    logging.getLogger(__name__).warning(
                        "certifi is not installed; TLS handshake with Atlas may fail. "
                        "Install with: pip install certifi"
                    )
            self.client = MongoClient(mongodb_uri, **conn_kwargs)
            # Force a ping early so connection issues show up immediately
            self.client.admin.command("ping")
            self.db = self.client[db_name]
            logging.getLogger(__name__).info("Connected to MongoDB: %s/%s", mongodb_uri, db_name)
        except Exception as exc:
            logging.getLogger(__name__).exception("MongoDB connection failed: %s", exc)
            self.client = None
            self.db = None

    def is_connected(self) -> bool:
        return self.db is not None
        
    def find_user(self, username: str) -> Optional[dict]:
        """Find a user by username"""
        if self.db is None:
            return None
        try:
            return self.db.users.find_one({"username": username})
        except Exception:
            logging.getLogger(__name__).exception("Error finding user")
            return None
    
    def verify_password(self, user: dict, password: str) -> bool:
        """Verify password hash"""
        try:
            return bcrypt.verify(password, user.get("password", ""))
        except Exception:
            logging.getLogger(__name__).exception("Password verification failed")
            return False
    
    def create_user(self, username: str, email: str, password: str, name: str) -> bool:
        """Create a new user"""
        if self.db is None:
            logging.getLogger(__name__).error("Cannot create user: DB not connected")
            return False
        if self.find_user(username):
            return False
        try:
            user = {
                "username": username,
                "email": email,
                "password": bcrypt.hash(password),
                "name": name,
                "role": "citizen",
                "created_at": datetime.utcnow()
            }
            result = self.db.users.insert_one(user)
            return bool(result.inserted_id)
        except Exception:
            logging.getLogger(__name__).exception("Error creating user")
            return False
    
    def save_report(self, record: ReportRecord) -> bool:
        """Save a new report"""
        if self.db is None:
            logging.getLogger(__name__).error("Cannot save report: DB not connected")
            return False
        try:
            result = self.db.reports.insert_one({
                "report_id": record.report_id,
                "created_at": record.created_at,
                "issue_type": record.issue_type,
                "text": record.text,
                "voice_text": record.voice_text,
                "image_path": record.image_path,
                "location": record.location,
                "complaint_text": record.complaint_text,
                "status": record.status,
                "fake": record.fake,
                "fake_score": record.fake_score
            })
            return bool(result.inserted_id)
        except Exception:
            logging.getLogger(__name__).exception("Error saving report")
            return False
    
    def get_report(self, report_id: str) -> Optional[ReportRecord]:
        """Get a report by ID"""
        if self.db is None:
            return None
        try:
            doc = self.db.reports.find_one({"report_id": report_id})
            if not doc:
                return None
            # Drop Mongo's internal _id before constructing dataclass
            doc.pop("_id", None)
            return ReportRecord(**doc)
        except Exception:
            logging.getLogger(__name__).exception("Error getting report")
            return None
    
    def list_reports(self, limit: int = 100) -> List[ReportRecord]:
        """List recent reports"""
        if self.db is None:
            return []
        try:
            docs = self.db.reports.find().sort("created_at", -1).limit(limit)
            cleaned = []
            for doc in docs:
                doc.pop("_id", None)
                cleaned.append(ReportRecord(**doc))
            return cleaned
        except Exception:
            logging.getLogger(__name__).exception("Error listing reports")
            return []
    
    def update_status(self, report_id: str, new_status: str) -> bool:
        """Update report status"""
        if self.db is None:
            logging.getLogger(__name__).error("Cannot update status: DB not connected")
            return False
        result = self.db.reports.update_one(
            {"report_id": report_id},
            {"$set": {"status": new_status}}
        )
        return result.modified_count > 0
    
    def list_authorities(self) -> List[dict]:
        """List all authority users"""
        if self.db is None:
            return []
        return list(self.db.users.find({"role": "authority"}))
