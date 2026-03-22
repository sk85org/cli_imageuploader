import os
import sys
import shutil

# Compute the absolute path of the directory containing batch.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Add the app directory to sys.path so we can import from main
sys.path.append(BASE_DIR)

try:
    from main import init_db, get_db, UPLOAD_DIST
except ImportError as e:
    print(f"Error: Could not import main. Details: {e}")
    sys.exit(1)

def main():
    # 1. /images_old から /images (UPLOAD_DIST) へのコピー
    # Docker環境では /images_old を、ローカル環境ではプロジェクトルート下の images_old を想定
    img_old_dir = "/images_old" if os.path.exists("/images_old") else os.path.join(PROJECT_DIR, 'images_old')
    
    copy_count = 0
    if os.path.exists(img_old_dir):
        files = os.listdir(img_old_dir)
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                src = os.path.join(img_old_dir, f)
                dst = os.path.join(UPLOAD_DIST, f)
                # 上書きを防ぐため、存在しない場合のみコピー
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    copy_count += 1
        print(f"Copied {copy_count} images from '{img_old_dir}' to '{UPLOAD_DIST}'.")
    else:
        print(f"Directory '{img_old_dir}' not found. Skipping copy.")

    # 2. /images (UPLOAD_DIST) にある画像ファイル一覧をデータベースに登録
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    reg_count = 0
    if os.path.exists(UPLOAD_DIST):
        files = os.listdir(UPLOAD_DIST)
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                cursor.execute('INSERT INTO image_collection (filename) VALUES (?)', (f,))
                reg_count += 1
        
        conn.commit()
        print(f"Successfully registered {reg_count} new images from '{UPLOAD_DIST}' into the database.")
    else:
        print(f"Directory '{UPLOAD_DIST}' not found. No files registered.")

    conn.close()

if __name__ == "__main__":
    main()
