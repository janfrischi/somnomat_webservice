"""
Authentication client for Supabase with best practices.
Separate from the main API client to handle user authentication.
"""
import os
import json
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

# Initialize Supabase client (uses anon key for auth)
SUPABASE_URL = os.getenv("SUPABASE_URL_CALMEA")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_CALMEA")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL_CALMEA and SUPABASE_KEY_CALMEA must be set in .env file")

# Session file path
SESSION_FILE = Path.home() / ".somnomat_session.json"


class SupabaseAuthClient:
    """Wrapper for Supabase client with authentication."""
    
    def __init__(self):
        """Initialize the auth client with a fresh Supabase instance."""
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.user = None
        self.session = None
        
        # Try to load existing session
        self._load_session()
    
    # ==================== Session Persistence ====================
    
    def _save_session(self):
        """Save session to file for persistence across CLI calls."""
        if self.session:
            try:
                session_data = {
                    "access_token": self.session.access_token,
                    "refresh_token": self.session.refresh_token,
                    "user": {
                        "id": self.user.id,
                        "email": self.user.email,
                        "user_metadata": self.user.user_metadata if hasattr(self.user, 'user_metadata') else {}
                    }
                }
                
                print(f"💾 Saving session to: {SESSION_FILE}")  # ← ADD THIS
                
                with open(SESSION_FILE, 'w') as f:
                    json.dump(session_data, f)
                
                # Make file readable only by user (for security)
                os.chmod(SESSION_FILE, 0o600)
                
                print(f"✅ Session saved successfully")  # ← ADD THIS
                
            except Exception as e:
                print(f"⚠️  Warning: Could not save session: {e}")
    
    def _load_session(self):
        """Load session from file if it exists."""
        if SESSION_FILE.exists():
            print(f"📂 Loading session from: {SESSION_FILE}")  # ← ADD THIS
            
            try:
                with open(SESSION_FILE, 'r') as f:
                    session_data = json.load(f)
                
                # Set the session in the Supabase client
                access_token = session_data.get("access_token")
                
                if access_token:
                    print(f"🔑 Found access token, setting session...")  # ← ADD THIS
                    
                    # Set the auth token
                    self.client.auth.set_session(
                        access_token=access_token,
                        refresh_token=session_data.get("refresh_token")
                    )
                    
                    # Try to get current user to verify session is valid
                    try:
                        user_response = self.client.auth.get_user()
                        if user_response and user_response.user:
                            self.user = user_response.user
                            self.session = self.client.auth.get_session()
                            print(f"✅ Session loaded for: {self.user.email}")  # ← ADD THIS
                            return True
                    except Exception as e:
                        print(f"❌ Session expired or invalid: {e}")  # ← ADD THIS
                        # Session expired, remove it
                        self._clear_session()
                        return False
                    
            except Exception as e:
                print(f"❌ Error loading session: {e}")  # ← ADD THIS
                # If session file is corrupted, remove it
                self._clear_session()
                return False
        else:
            print(f"📂 No session file found at: {SESSION_FILE}")  # ← ADD THIS
    
        return False
    
    def _clear_session(self):
        """Clear session file."""
        if SESSION_FILE.exists():
            try:
                SESSION_FILE.unlink()
            except:
                pass
    
    # ==================== Authentication Methods ====================
    
    def sign_up(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sign up a new user.
        
        Args:
            email: User's email
            password: User's password (min 6 characters)
            user_metadata: Optional metadata like {'name': 'John Doe'}
        
        Returns:
            User data and session
        """
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata or {}
                }
            })
            
            if response.user:
                self.user = response.user
                self.session = response.session
                self._save_session()
                print(f"✅ User {email} signed up successfully!")
                return {"user": response.user, "session": response.session}
            
            return {"error": "Sign up failed"}
        
        except Exception as e:
            print(f"❌ Sign up error: {e}")
            return {"error": str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user.
        
        Args:
            email: User's email
            password: User's password
        
        Returns:
            User data and session
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                self.user = response.user
                self.session = response.session
                self._save_session()
                print(f"✅ User {email} signed in successfully!")
                return {"user": response.user, "session": response.session}
            
            return {"error": "Sign in failed"}
        
        except Exception as e:
            print(f"❌ Sign in error: {e}")
            return {"error": str(e)}
    
    def sign_out(self) -> bool:
        """Sign out the current user."""
        try:
            self.client.auth.sign_out()
            self.user = None
            self.session = None
            self._clear_session()
            print("✅ User signed out successfully!")
            return True
        except Exception as e:
            print(f"❌ Sign out error: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user."""
        # If we already have user in memory, return it
        if self.user:
            return self.user
        
        # Try to get user from session
        try:
            user_response = self.client.auth.get_user()
            if user_response and user_response.user:
                self.user = user_response.user
                return user_response.user
            return None
        except Exception as e:
            # Session might be expired
            self._clear_session()
            return None
    
    def get_session(self) -> Optional[Dict[str, Any]]:
        """Get the current session."""
        try:
            session = self.client.auth.get_session()
            self.session = session
            return session
        except Exception as e:
            return None
    
    def reset_password_email(self, email: str) -> bool:
        """Send a password reset email.
        
        Args:
            email: User's email
        
        Returns:
            True if email sent successfully
        """
        try:
            self.client.auth.reset_password_email(email)
            print(f"✅ Password reset email sent to {email}")
            return True
        except Exception as e:
            print(f"❌ Password reset error: {e}")
            return False
    
    def update_user(self, **attributes) -> Optional[Dict[str, Any]]:
        """Update user attributes.
        
        Args:
            **attributes: User attributes to update (email, password, data, etc.)
        
        Returns:
            Updated user data
        """
        try:
            response = self.client.auth.update_user(attributes)
            if response.user:
                self.user = response.user
                self._save_session()
                print("✅ User updated successfully!")
                return response.user
            return None
        except Exception as e:
            print(f"❌ Update user error: {e}")
            return None
    
    def refresh_session(self) -> Optional[Dict[str, Any]]:
        """Refresh the current session."""
        try:
            response = self.client.auth.refresh_session()
            self.session = response.session
            self._save_session()
            return response.session
        except Exception as e:
            print(f"❌ Refresh session error: {e}")
            self._clear_session()
            return None
    
    # ==================== Device Management ====================
    
    def create_device(self, name: str, mac: Optional[str] = None, boardtype: Optional[int] = None, 
                      hardware_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new device and auto-link to current user.
        
        Args:
            name: Device name
            mac: MAC address (optional)
            boardtype: Board type ID (optional)
            hardware_version: Hardware version (optional)
        
        Returns:
            Created device data
        """
        if not self.user:
            print("❌ No authenticated user!")
            return None
        
        try:
            # Prepare device data
            device_data = {"name": name}
            
            if mac:
                device_data["mac"] = mac
            if boardtype is not None:
                device_data["boardtype"] = boardtype
            if hardware_version:
                device_data["hardware_version"] = hardware_version
            
            # Create device using authenticated client
            response = self.client.table("devices").insert(device_data).execute()
            
            if response.data:
                device = response.data[0]
                print(f"✅ Device created: {device['name']} (ID: {device['id']})")
                
                # The database trigger should auto-link, but verify
                import time
                time.sleep(0.3)  # Give trigger time to execute
                
                # Check if auto-linked
                has_access = self.has_device_access(device['id'])
                
                if not has_access:
                    # Manually link if trigger didn't work
                    self.link_device_to_user(device['id'], role="owner")
                
                return device
            
            return None
        
        except Exception as e:
            print(f"❌ Error creating device: {e}")
            return None
    
    # ==================== User-Device Association ====================
    
    def link_device_to_user(self, device_id: int, role: str = "owner") -> Optional[Dict[str, Any]]:
        """Link a device to the current user.
        
        Args:
            device_id: ID of the device to link
            role: Role of the user for this device (owner, viewer, admin)
        
        Returns:
            The created user_devices record
        """
        if not self.user:
            print("❌ No authenticated user!")
            return None
        
        try:
            response = self.client.table("user_devices") \
                .insert({
                    "user_id": self.user.id,
                    "device_id": device_id,
                    "role": role
                }) \
                .execute()
            
            print(f"✅ Device {device_id} linked to user as {role}")
            return response.data[0] if response.data else None
        
        except Exception as e:
            print(f"❌ Link device error: {e}")
            return None
    
    def get_user_devices(self) -> list:
        """Get all devices for the current user."""
        if not self.user:
            print("❌ No authenticated user!")
            return []
        
        try:
            response = self.client.table("user_devices") \
                .select("*, devices(*)") \
                .eq("user_id", self.user.id) \
                .execute()
            
            return response.data
        
        except Exception as e:
            print(f"❌ Get user devices error: {e}")
            return []
    
    def unlink_device(self, device_id: int) -> bool:
        """Unlink a device from the current user.
        
        Args:
            device_id: ID of the device to unlink
        
        Returns:
            True if successful
        """
        if not self.user:
            print("❌ No authenticated user!")
            return False
        
        try:
            self.client.table("user_devices") \
                .delete() \
                .eq("user_id", self.user.id) \
                .eq("device_id", device_id) \
                .execute()
            
            print(f"✅ Device {device_id} unlinked from user")
            return True
        
        except Exception as e:
            print(f"❌ Unlink device error: {e}")
            return False
    
    def has_device_access(self, device_id: int, required_role: Optional[str] = None) -> bool:
        """Check if current user has access to a device.
        
        Args:
            device_id: ID of the device to check
            required_role: Optional specific role required (e.g., 'owner')
        
        Returns:
            True if user has access
        """
        if not self.user:
            return False
        
        try:
            query = self.client.table("user_devices") \
                .select("role") \
                .eq("user_id", self.user.id) \
                .eq("device_id", device_id)
            
            if required_role:
                query = query.eq("role", required_role)
            
            response = query.execute()
            return bool(response.data)
        
        except Exception as e:
            print(f"❌ Check device access error: {e}")
            return False
    
    # ==================== Helper Methods ====================
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.get_current_user() is not None
    
    def require_auth(self):
        """Decorator/helper to require authentication."""
        if not self.is_authenticated():
            raise PermissionError("Authentication required!")
        return True
    
    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """Get authorization header for API requests.
        
        Returns:
            Dict with Authorization header or None
        """
        if self.session and hasattr(self.session, 'access_token'):
            return {"Authorization": f"Bearer {self.session.access_token}"}
        return None


# Global authenticated client instance (optional)
# You can create instances as needed instead
auth_client = SupabaseAuthClient()