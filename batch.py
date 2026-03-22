import os
import sys

# Compute the absolute path of the directory containing batch.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the app directory to sys.path so we can import new_cli
app_dir = os.path.join(BASE_DIR, 'app')
sys.path.append(app_dir)

try:
    from main import init_db, get_db
except ImportError as e:
    print(f"Error: Could not import main. Details: {e}")
    sys.exit(1)

def main():
    # Initialize the database and get a connection
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    img_old_dir = os.path.join(BASE_DIR, 'img_old')
    count = 0

    if os.path.exists(img_old_dir):
        files = os.listdir(img_old_dir)
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                # Insert the filename into our simple image_collection table
                cursor.execute('INSERT INTO image_collection (filename) VALUES (?)', (f,))
                count += 1
                
        conn.commit()
        print(f"Successfully registered {count} old images from '{img_old_dir}' into the database.")
    else:
        print(f"Directory '{img_old_dir}' not found. Please make sure it exists.")

    conn.close()

if __name__ == "__main__":
    main()
