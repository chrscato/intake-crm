#!/usr/bin/env python
"""Geocoding Helper Script

Geocodes patient addresses in the intake-crm database using OpenStreetMap's
Nominatim service (free). Adds latitude and longitude columns to the referrals table.
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderRateLimited
except ImportError:
    print("❌ geopy is required but not installed")
    print("Install with: pip install geopy")
    sys.exit(1)


class AddressGeocoder:
    def __init__(self, user_agent: str = "intake-crm-geocoder/1.0"):
        """Initialize the geocoder with a custom user agent."""
        self.geocoder = Nominatim(
            user_agent=user_agent,
            timeout=10
        )
        self.request_count = 0
        self.success_count = 0
        self.failed_count = 0
    
    def _extract_fallback_addresses(self, address: str) -> list:
        """Extract progressively simpler address formats for fallback geocoding."""
        import re
        
        fallbacks = []
        
        # Original address
        fallbacks.append(address)
        
        # Try without apartment/unit numbers (remove Apt, Unit, #, etc.)
        no_apt = re.sub(r'\s+(apt|apartment|unit|suite|ste|#)\s*[a-z0-9]+\b', '', address, flags=re.IGNORECASE)
        if no_apt != address:
            fallbacks.append(no_apt.strip())
        
        # Try just city, state, zip
        # Look for patterns like "City, ST zip" or "City, ST"
        city_state_zip = re.search(r',\s*([^,]+),?\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?', address)
        if city_state_zip:
            city = city_state_zip.group(1).strip()
            state = city_state_zip.group(2).strip()
            zip_code = city_state_zip.group(3)
            
            if zip_code:
                fallbacks.append(f"{city}, {state} {zip_code}")
            fallbacks.append(f"{city}, {state}")
        
        # Try just state and zip
        state_zip = re.search(r'\b([A-Z]{2})\s*(\d{5}(?:-\d{4})?)', address)
        if state_zip:
            state = state_zip.group(1)
            zip_code = state_zip.group(2)
            fallbacks.append(f"{state} {zip_code}")
        
        # Try just zip code
        zip_only = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
        if zip_only:
            fallbacks.append(zip_only.group(1))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for fb in fallbacks:
            if fb not in seen and fb.strip():
                seen.add(fb)
                unique_fallbacks.append(fb.strip())
        
        return unique_fallbacks

    def geocode_address(self, address: str, retry_count: int = 3) -> Optional[Tuple[float, float]]:
        """Geocode a single address using Nominatim with fallback strategies.
        
        Args:
            address: The address string to geocode
            retry_count: Number of retries for failed requests
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding failed
        """
        if not address or not address.strip():
            return None
        
        address = address.strip()
        
        # Get fallback addresses
        fallback_addresses = self._extract_fallback_addresses(address)
        
        # Try each fallback address
        for i, fallback_addr in enumerate(fallback_addresses):
            if i == 0:
                print(f"🔍 Trying full address: {fallback_addr[:60]}...")
            else:
                print(f"🔄 Fallback {i}: {fallback_addr[:60]}...")
            
            for attempt in range(retry_count):
                try:
                    self.request_count += 1
                    
                    # Add small delay to be respectful to OSM servers
                    # Nominatim has a usage policy of max 1 request per second
                    time.sleep(1.1)
                    
                    location = self.geocoder.geocode(
                        fallback_addr,
                        exactly_one=True,
                        addressdetails=True,
                        limit=1
                    )
                    
                    if location:
                        lat, lon = location.latitude, location.longitude
                        print(f"✅ Found: {lat:.6f}, {lon:.6f}")
                        print(f"   📍 Matched: {location.address}")
                        if i > 0:
                            print(f"   💡 Used fallback strategy: {fallback_addr}")
                        self.success_count += 1
                        return (lat, lon)
                    else:
                        print(f"❌ No results for: {fallback_addr}")
                        break
                        
                except GeocoderRateLimited:
                    print(f"⏳ Rate limited, waiting 5 seconds...")
                    time.sleep(5)
                    continue
                    
                except GeocoderTimedOut:
                    print(f"⏰ Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2)
                    continue
                    
                except GeocoderUnavailable:
                    print(f"🚫 Service unavailable on attempt {attempt + 1}, retrying...")
                    time.sleep(5)
                    continue
                    
                except Exception as e:
                    print(f"❌ Unexpected error: {e}")
                    break
        
        print(f"❌ All fallback strategies failed for: {address}")
        self.failed_count += 1
        return None
    
    def print_stats(self):
        """Print geocoding statistics."""
        print(f"\n📊 Geocoding Statistics:")
        print(f"   Total requests: {self.request_count}")
        print(f"   Successful: {self.success_count}")
        print(f"   Failed: {self.failed_count}")
        if self.request_count > 0:
            success_rate = (self.success_count / self.request_count) * 100
            print(f"   Success rate: {success_rate:.1f}%")


def setup_database(db_path: Path) -> sqlite3.Connection:
    """Setup database with latitude and longitude columns."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add latitude and longitude columns if they don't exist
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN latitude REAL")
        print("✅ Added latitude column to referrals table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN longitude REAL")
        print("✅ Added longitude column to referrals table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN geocoded_at TIMESTAMP")
        print("✅ Added geocoded_at column to referrals table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN geocoding_status TEXT")
        print("✅ Added geocoding_status column to referrals table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create index for lat/lon queries
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_location ON referrals(latitude, longitude)")
        print("✅ Created location index")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    return conn


def get_addresses_to_geocode(conn: sqlite3.Connection, force_refresh: bool = False) -> list:
    """Get list of addresses that need geocoding."""
    cursor = conn.cursor()
    
    if force_refresh:
        # Get all referrals with patient addresses
        query = """
            SELECT id, patient_address, patient_name, order_number 
            FROM referrals 
            WHERE patient_address IS NOT NULL 
            AND patient_address != ''
            ORDER BY id
        """
    else:
        # Only get addresses that haven't been geocoded yet
        query = """
            SELECT id, patient_address, patient_name, order_number 
            FROM referrals 
            WHERE patient_address IS NOT NULL 
            AND patient_address != ''
            AND (latitude IS NULL OR longitude IS NULL)
            ORDER BY id
        """
    
    cursor.execute(query)
    return cursor.fetchall()


def update_geocoding_result(conn: sqlite3.Connection, referral_id: int, 
                          lat_lon: Optional[Tuple[float, float]]):
    """Update the database with geocoding results."""
    cursor = conn.cursor()
    
    if lat_lon:
        lat, lon = lat_lon
        cursor.execute("""
            UPDATE referrals 
            SET latitude = ?, longitude = ?, 
                geocoded_at = datetime('now'), 
                geocoding_status = 'success'
            WHERE id = ?
        """, (lat, lon, referral_id))
    else:
        cursor.execute("""
            UPDATE referrals 
            SET geocoded_at = datetime('now'), 
                geocoding_status = 'failed'
            WHERE id = ?
        """, (referral_id,))
    
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Geocode patient addresses using OpenStreetMap")
    parser.add_argument("--db-path", type=str, default="intake-crm.db", 
                       help="Path to SQLite database file")
    parser.add_argument("--limit", type=int, default=None, 
                       help="Limit number of addresses to geocode")
    parser.add_argument("--force-refresh", action="store_true", 
                       help="Re-geocode all addresses, even those already processed")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be geocoded without actually doing it")
    parser.add_argument("--user-agent", type=str, default="intake-crm-geocoder/1.0",
                       help="User agent string for Nominatim requests")
    
    args = parser.parse_args()
    
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"🗺️  Starting geocoding process...")
    print(f"   Database: {db_path}")
    print(f"   Force refresh: {args.force_refresh}")
    print(f"   Dry run: {args.dry_run}")
    
    # Setup database
    conn = setup_database(db_path)
    
    # Get addresses to geocode
    addresses = get_addresses_to_geocode(conn, args.force_refresh)
    
    if args.limit:
        addresses = addresses[:args.limit]
    
    if not addresses:
        print("✅ No addresses need geocoding")
        conn.close()
        return
    
    print(f"\n🔍 Found {len(addresses)} addresses to geocode")
    
    if args.dry_run:
        print("\n📋 DRY RUN - Would geocode these addresses:")
        for referral_id, address, patient_name, order_number in addresses:
            print(f"   ID {referral_id}: {patient_name} ({order_number}) - {address}")
        conn.close()
        return
    
    # Initialize geocoder
    geocoder = AddressGeocoder(user_agent=args.user_agent)
    
    print(f"\n🚀 Starting geocoding process...")
    print(f"   Using OpenStreetMap Nominatim service")
    print(f"   Rate limit: ~1 request per second (respectful usage)")
    
    # Process each address
    for i, (referral_id, address, patient_name, order_number) in enumerate(addresses, 1):
        print(f"\n📍 Processing {i}/{len(addresses)}: ID {referral_id}")
        print(f"   Patient: {patient_name}")
        print(f"   Order: {order_number}")
        print(f"   Address: {address}")
        
        # Geocode the address
        lat_lon = geocoder.geocode_address(address)
        
        # Update database
        update_geocoding_result(conn, referral_id, lat_lon)
        
        # Show progress
        if lat_lon:
            lat, lon = lat_lon
            print(f"✅ Updated database: {lat:.6f}, {lon:.6f}")
        else:
            print(f"❌ Failed to geocode, marked as failed in database")
    
    # Print final statistics
    geocoder.print_stats()
    
    # Show summary from database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) as geocoded,
            COUNT(CASE WHEN geocoding_status = 'failed' THEN 1 END) as failed
        FROM referrals 
        WHERE patient_address IS NOT NULL AND patient_address != ''
    """)
    
    total, geocoded, failed = cursor.fetchone()
    
    print(f"\n📊 Database Summary:")
    print(f"   Total addresses: {total}")
    print(f"   Successfully geocoded: {geocoded}")
    print(f"   Failed geocoding: {failed}")
    print(f"   Not yet processed: {total - geocoded - failed}")
    
    conn.close()
    print(f"\n✅ Geocoding complete!")


if __name__ == "__main__":
    main()