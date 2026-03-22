import os
import sqlite3
import sys

def main():
    # Automatically resolve the path to the images.db relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'img', 'images.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        print("Make sure you have launched the application or run the batch script at least once.")
        sys.exit(1)

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Retrieve all filenames ordered algebraically (chronologically by filename prefix)
        cursor.execute("SELECT filename FROM image_collection ORDER BY filename ASC")
        rows = cursor.fetchall()
        
        # Output the list
        for row in rows:
            print(row[0])
            
        print("-" * 30)
        print(f"Total: {len(rows)} file(s) registered.")
        
    except sqlite3.OperationalError as e:
        print(f"Error reading from the database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
