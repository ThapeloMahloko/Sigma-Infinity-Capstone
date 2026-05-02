"""
Database Migration Script

Migrates sensor data from long format (many rows with N/A values)
to wide format (one row per timestamp with all sensors filled).

This script:
1. Groups data by timestamp
2. Collapses N/A values using MAX() aggregation
3. Generates new sequential IDs
4. Creates a clean, optimized database
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Database.Sql import DATABASE_PATH, SensorReading, Base, engine, SessionLocal, get_session


def backup_old_database():
    """Create a backup of the old database before migration."""
    if DATABASE_PATH.exists():
        backup_path = DATABASE_PATH.parent / f"{DATABASE_PATH.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"✓ Backup created: {backup_path}")
        return backup_path
    return None


def migrate_data():
    """
    Migrate sensor data from old table to new table with aggregation.
    
    This handles the transformation from long format to wide format by:
    - Grouping by timestamp
    - Using MAX() to collapse NULL values
    - Generating new sequential IDs
    """
    print("\n" + "="*70)
    print("SENSOR DATA MIGRATION - Long Format → Wide Format")
    print("="*70)
    
    # Create backup
    backup_path = backup_old_database()
    
    try:
        # Connect to existing database
        old_conn = sqlite3.connect(str(DATABASE_PATH))
        old_cursor = old_conn.cursor()
        
        # Check if sensor_readings table exists
        old_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_readings'"
        )
        if not old_cursor.fetchone():
            print("✗ No existing sensor_readings table found. Migration not needed.")
            old_conn.close()
            return False
        
        print("\n1️⃣  Reading and aggregating old data...")
        
        # Read and aggregate data in one step
        # This query groups by timestamp and uses MAX() to get actual values, ignoring NULLs
        query = """
        SELECT 
            timestamp,
            MAX(soil_moisture) AS soil_moisture,
            MAX(temperature) AS temperature,
            MAX(humidity) AS humidity,
            MAX(water_level) AS water_level,
            MAX(ambient_light) AS ambient_light,
            MAX(rainfall) AS rainfall,
            MAX(motion_detection) AS motion_detection,
            MAX(ultrasonic_distance) AS ultrasonic_distance,
            MAX(pump_status) AS pump_status,
            MAX(fan_status) AS fan_status
        FROM sensor_readings
        GROUP BY timestamp
        ORDER BY timestamp ASC
        """
        
        df_cleaned = pd.read_sql(query, old_conn)
        old_conn.close()
        
        print(f"✓ Aggregated {len(df_cleaned)} unique timestamps")
        print(f"  Original row estimate: {len(df_cleaned) * 10} rows (approximate)")
        
        # Drop the old database file
        print("\n2️⃣  Creating new database with clean schema...")
        DATABASE_PATH.unlink()
        
        # Create new engine and database with fresh schema
        new_engine = sqlite3.connect(str(DATABASE_PATH))
        
        # The ORM will create the new table with proper schema
        Base.metadata.create_all(engine)
        
        print("✓ New database created with fresh schema")
        
        # Insert aggregated data
        print("\n3️⃣  Inserting aggregated data with new IDs...")
        
        with get_session() as session:
            for idx, row in df_cleaned.iterrows():
                reading = SensorReading(
                    timestamp=pd.to_datetime(row['timestamp']),
                    soil_moisture=row['soil_moisture'] if pd.notna(row['soil_moisture']) else None,
                    temperature=row['temperature'] if pd.notna(row['temperature']) else None,
                    humidity=row['humidity'] if pd.notna(row['humidity']) else None,
                    water_level=row['water_level'] if pd.notna(row['water_level']) else None,
                    ambient_light=row['ambient_light'] if pd.notna(row['ambient_light']) else None,
                    rainfall=row['rainfall'] if pd.notna(row['rainfall']) else None,
                    motion_detection=row['motion_detection'] if pd.notna(row['motion_detection']) else None,
                    ultrasonic_distance=row['ultrasonic_distance'] if pd.notna(row['ultrasonic_distance']) else None,
                    pump_status=row['pump_status'] if pd.notna(row['pump_status']) else None,
                    fan_status=row['fan_status'] if pd.notna(row['fan_status']) else None,
                )
                session.add(reading)
            
            session.commit()
        
        print(f"✓ Inserted {len(df_cleaned)} records with new sequential IDs")
        
        # Verify migration
        print("\n4️⃣  Verifying migration...")
        with get_session() as session:
            total_readings = session.query(SensorReading).count()
            latest_reading = session.query(SensorReading).order_by(SensorReading.id.desc()).first()
        
        print(f"✓ Total readings: {total_readings}")
        print(f"✓ Latest ID: {latest_reading.id}")
        print(f"✓ Latest timestamp: {latest_reading.timestamp}")
        
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE!")
        print("="*70)
        print(f"\nDatabase location: {DATABASE_PATH}")
        print(f"Backup saved to:  {backup_path}")
        print("\n📊 Benefits:")
        print("  • Sequential IDs (1, 2, 3, ...)")
        print("  • One row per unique timestamp")
        print("  • Smaller database file size")
        print("  • Faster dashboard queries")
        print("  • No more 'staircase' effect in old data")
        print("\n⚠️  Note: New data will use the aggregation logic in save_message().")
        print("   Each new sensor reading will be merged into the same timestamp.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if backup_path:
            print(f"\n⚠️  Restoring from backup: {backup_path}")
            import shutil
            shutil.copy2(backup_path, DATABASE_PATH)
            print("✓ Backup restored")
        return False


if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)
