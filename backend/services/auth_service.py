import httpx
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db["users"]
        self.sessions_collection = db["user_sessions"]
    
    async def exchange_session_id(self, session_id: str) -> Dict[str, Any]:
        """Exchange session_id for user data from Emergent Auth"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                    headers={"X-Session-ID": session_id}
                )
                response.raise_for_status()
                user_data = response.json()
            
            # Store or update user
            user_id = await self._upsert_user(user_data)
            
            # Create session
            session_token = f"session_{uuid.uuid4().hex}"
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            await self.sessions_collection.insert_one({
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            })
            
            return {
                "user_id": user_id,
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data.get("picture"),
                "session_token": session_token
            }
            
        except Exception as e:
            logger.error(f"Session exchange failed: {str(e)}")
            raise ValueError(f"Authentication failed: {str(e)}")
    
    async def _upsert_user(self, user_data: Dict[str, Any]) -> str:
        """Create or update user, return user_id"""
        email = user_data["email"]
        
        # Check if user exists
        existing_user = await self.users_collection.find_one(
            {"email": email},
            {"_id": 0}
        )
        
        if existing_user:
            # Update user data
            await self.users_collection.update_one(
                {"email": email},
                {"$set": {
                    "name": user_data["name"],
                    "picture": user_data.get("picture")
                }}
            )
            return existing_user["user_id"]
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await self.users_collection.insert_one({
                "user_id": user_id,
                "email": email,
                "name": user_data["name"],
                "picture": user_data.get("picture"),
                "created_at": datetime.now(timezone.utc)
            })
            return user_id
    
    async def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Verify session token and return user data"""
        logger.info(f"Verifying session token: {session_token}")
        session = await self.sessions_collection.find_one(
            {"session_token": session_token},
            {"_id": 0}
        )
        
        logger.info(f"Session found: {session}")
        if not session:
            logger.warning("Session not found")
            return None
        
        # Check expiry
        expires_at = session["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            return None
        
        # Get user data
        user = await self.users_collection.find_one(
            {"user_id": session["user_id"]},
            {"_id": 0}
        )
        
        return user
    
    async def logout(self, session_token: str) -> bool:
        """Delete session"""
        result = await self.sessions_collection.delete_one(
            {"session_token": session_token}
        )
        return result.deleted_count > 0