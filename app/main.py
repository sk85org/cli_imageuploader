from flask import Flask, request, jsonify
from functools import wraps
import datetime
import secrets
import os
import sqlite3

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Compute absolute project base directory (imageuploader)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use /img and /db if they exist (e.g. inside Docker), otherwise use local folders
_default_img = "/img" if os.path.exists("/img") else os.path.join(BASE_DIR, "img")
UPLOAD_DIST = os.environ.get("UPLOAD_DIST", _default_img)

_default_db = "/db" if os.path.exists("/db") else os.path.join(BASE_DIR, "db")
DB_DIR = os.environ.get("DB_DIR", _default_db)

# Save the SQLite DB
DB_PATH = os.path.join(DB_DIR, "images.db")

import sys

app = Flask(__name__)

# Require API_KEY environment variable for security
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("CRITICAL ERROR: API_KEY environment variable is not set.", file=sys.stderr)
    print("Please set an API key to secure the upload and delete endpoints.", file=sys.stderr)
    print("Example: API_KEY='your-secure-key' uv run flask ...", file=sys.stderr)
    sys.exit(1)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get("x-api-key") and request.headers.get("x-api-key") == API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized. Please provide a valid 'x-api-key' header."}), 401
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    return "running"
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure the upload and db directories exist
    os.makedirs(UPLOAD_DIST, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS image_collection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def imgpath(filename):
    return os.path.join(UPLOAD_DIST, filename)

def save_image_safely(file_storage, filepath, extension):
    if not PILLOW_AVAILABLE or extension.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
        file_storage.save(filepath)
        return
        
    try:
        # Open directly from memory stream to avoid writing to disk twice
        image = Image.open(file_storage.stream)
        
        # Remove exif metadata if it exists
        if "exif" in image.info:
            image.info.pop("exif")
            
        format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}
        fmt = format_map.get(extension.lower(), 'JPEG')
        
        if fmt == 'JPEG':
            if image.mode in ('RGBA', 'P', 'LA'):
                image = image.convert('RGB')
            try:
                # Try to preserve the original compression quality to prevent drastic file size changes
                image.save(filepath, format=fmt, quality='keep')
            except Exception:
                # Fallback if keep fails
                image.save(filepath, format=fmt, quality=95)
        else:
            image.save(filepath, format=fmt)
    except Exception as e:
        print(f"Failed to process image with Pillow: {e}")
        # Fallback: save the original file directly to disk if Pillow processing fails
        file_storage.stream.seek(0)
        file_storage.save(filepath)

@app.route("/api/upload", methods=["POST"])
@require_api_key
def upload_file():
    # Handle normal form-data upload
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify({"error": "file is required in form-data."}), 400

    file = request.files["file"]

    _, extension = os.path.splitext(file.filename)
    extension = extension.lower()
        
    if extension not in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
        return jsonify({"error": f"Unsupported file format ({extension}) for {file.filename}. Allowed: gif, jpg, png, svg"}), 400

    time = datetime.datetime.now()
    filename = (
        time.strftime("%Y%m%d-%H-%M-%S-")
        + secrets.token_urlsafe(15)
        + extension
    )

    save_image_safely(file, imgpath(filename), extension)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO image_collection (filename) VALUES (?)", (filename,))
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"message": "File uploaded successfully", "filename": filename, "_id": str(inserted_id)})

@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("filename", "")
    
    sql = "SELECT id, filename FROM image_collection"
    params = []
    
    if query:
        sql += " WHERE filename LIKE ?"
        params.append(f"%{query}%")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    images = []
    for row in rows:
        images.append({
            "_id": str(row["id"]),
            "filename": row["filename"]
        })
        
    return jsonify({"results": images, "total": len(images)})

@app.route("/api/images/<id>", methods=["DELETE"])
@require_api_key
def delete(id):
    try:
        obj_id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM image_collection WHERE id = ?", (obj_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return jsonify({"error": "Image not found"}), 404
        
    filename = result["filename"]
    cursor.execute("DELETE FROM image_collection WHERE id = ?", (obj_id,))
    conn.commit()
    conn.close()
    
    file_path = imgpath(filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({"message": f"Image {filename} deleted successfully", "id": id})
        except Exception as e:
            return jsonify({"error": f"Failed to delete file from disk: {str(e)}"}), 500
    else:
        return jsonify({"message": f"Record deleted, but file {filename} was not found on disk", "id": id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
