"""
CLI tool for managing authentication.
"""
import sys
from supabase_auth_client import auth_client


def main():
    print("🔐 Somnomat Authentication CLI\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python auth_cli.py signup <email> <password> [name]")
        print("  python auth_cli.py signin <email> <password>")
        print("  python auth_cli.py signout")
        print("  python auth_cli.py whoami")
        print("  python auth_cli.py devices")
        print("  python auth_cli.py link <device_id>")
        print("  python auth_cli.py create-device <name> [mac] [boardtype]")
        return
    
    command = sys.argv[1].lower()
    
    if command == "signup":
        if len(sys.argv) < 4:
            print("❌ Usage: python auth_cli.py signup <email> <password> [name]")
            return
        
        email = sys.argv[2]
        password = sys.argv[3]
        name = sys.argv[4] if len(sys.argv) > 4 else None
        
        metadata = {"name": name} if name else {}
        result = auth_client.sign_up(email, password, metadata)
        
        if "user" in result:
            print(f"\n✅ Account created!")
            print(f"   Email: {result['user'].email}")
            print(f"   ID: {result['user'].id}")
            print(f"\n💡 Note: You are now signed in and can create devices")
    
    elif command == "signin":
        if len(sys.argv) < 4:
            print("❌ Usage: python auth_cli.py signin <email> <password>")
            return
        
        email = sys.argv[2]
        password = sys.argv[3]
        
        result = auth_client.sign_in(email, password)
        
        if "user" in result:
            print(f"\n✅ Signed in!")
            print(f"   Email: {result['user'].email}")
            print(f"   ID: {result['user'].id}")
    
    elif command == "signout":
        auth_client.sign_out()
    
    elif command == "whoami":
        user = auth_client.get_current_user()
        if user:
            print(f"\n👤 Current User:")
            print(f"   Email: {user.email}")
            print(f"   ID: {user.id}")
            print(f"   Created: {user.created_at}")
        else:
            print("❌ Not signed in")
            print("\n💡 Sign in first: python auth_cli.py signin <email> <password>")
    
    elif command == "devices":
        user = auth_client.get_current_user()
        if not user:
            print("❌ Not signed in")
            print("💡 Sign in first: python auth_cli.py signin <email> <password>")
            return
        
        devices = auth_client.get_user_devices()
        if devices:
            print(f"\n📱 Your Devices ({len(devices)}):")
            for d in devices:
                device_info = d.get('devices', {})
                print(f"   • {device_info.get('name', 'Unknown')} (ID: {d['device_id']}) - Role: {d['role']}")
        else:
            print("📱 No devices linked to your account")
            print("\n💡 Create a device: python auth_cli.py create-device <name>")
    
    elif command == "link":
        if len(sys.argv) < 3:
            print("❌ Usage: python auth_cli.py link <device_id>")
            return
        
        user = auth_client.get_current_user()
        if not user:
            print("❌ Not signed in")
            print("💡 Sign in first: python auth_cli.py signin <email> <password>")
            return
        
        device_id = int(sys.argv[2])
        result = auth_client.link_device_to_user(device_id)
        
        if result:
            print(f"\n✅ Device {device_id} successfully linked to your account")
    
    elif command == "create-device":
        if len(sys.argv) < 3:
            print("❌ Usage: python auth_cli.py create-device <name> [mac] [boardtype]")
            return
        
        # Check if user is signed in
        user = auth_client.get_current_user()
        if not user:
            print("❌ Not signed in!")
            print("💡 Sign in first: python auth_cli.py signin <email> <password>")
            return
        
        name = sys.argv[2]
        mac = sys.argv[3] if len(sys.argv) > 3 else None
        boardtype = int(sys.argv[4]) if len(sys.argv) > 4 else None
        
        # Create device with authenticated client
        try:
            # Prepare device data
            device_data = {
                "name": name,
            }
            
            if mac:
                device_data["mac"] = mac
            if boardtype:
                device_data["boardtype"] = boardtype
            
            # Use the authenticated client to create device
            response = auth_client.client.table("devices").insert(device_data).execute()
            
            if response.data:
                device = response.data[0]
                print(f"\n✅ Device created: {device['name']} (ID: {device['id']})")
                
                # Check if auto-link worked (via trigger)
                # If not, manually link
                import time
                time.sleep(0.5)  # Give trigger time to execute
                
                devices = auth_client.get_user_devices()
                device_ids = [d['device_id'] for d in devices]
                
                if device['id'] not in device_ids:
                    print("🔗 Linking device to your account...")
                    link_result = auth_client.link_device_to_user(device['id'], role="owner")
                    
                    if link_result:
                        print(f"✅ Device automatically linked to your account as owner")
                    else:
                        print(f"⚠️  Device created but auto-link failed. Run:")
                        print(f"   python auth_cli.py link {device['id']}")
                else:
                    print(f"✅ Device automatically linked to your account as owner")
            else:
                print("❌ Failed to create device")
        
        except Exception as e:
            error_msg = str(e)
            
            if "row-level security policy" in error_msg.lower():
                print(f"❌ Permission denied: Row Level Security blocked the request")
                print(f"\n🔧 Fix: Run this SQL in Supabase SQL Editor:")
                print(f"""
DROP POLICY IF EXISTS "Users can insert their own devices" ON devices;

CREATE POLICY "Authenticated users can create devices"
    ON devices FOR INSERT
    TO authenticated
    WITH CHECK (true);
                """)
            else:
                print(f"❌ Error creating device: {e}")
                print("\n💡 Make sure you're signed in and have proper permissions")
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()