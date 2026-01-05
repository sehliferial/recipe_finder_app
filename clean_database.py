import os
import sqlite3
import shutil
from datetime import datetime

def backup_before_clean():
    """إنشاء نسخة احتياطية قبل التنظيف"""
    if os.path.exists('recipes.db'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f'recipes_backup_before_clean_{timestamp}.db'
        shutil.copy2('recipes.db', backup_name)
        print(f"✅ Backup created before cleaning: {backup_name}")
        return backup_name
    return None

def recreate_database():
    """إعادة إنشاء قاعدة البيانات (تحذف كل البيانات!)"""
    
    print("=" * 50)
    print("⚠️ WARNING: This will delete ALL existing data!")
    print("=" * 50)
    
    # طلب تأكيد
    confirmation = input("Are you sure? Type 'YES' to continue: ")
    if confirmation != 'YES':
        print("❌ Operation cancelled")
        return
    
    # نسخة احتياطية
    backup_before_clean()
    
    # حذف الملفات القديمة
    if os.path.exists('recipes.db'):
        os.remove('recipes.db')
        print("✅ Old database deleted")
    
    if os.path.exists('recipes.db-journal'):
        os.remove('recipes.db-journal')
        print("✅ Journal file deleted")
    
    # إنشاء قاعدة بيانات جديدة
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # إنشاء الجداول
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL UNIQUE,
        psw TEXT NOT NULL,
        api_key TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ingredients TEXT NOT NULL,
        results_count INTEGER DEFAULT 0,
        search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS view_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        recipe_title TEXT NOT NULL,
        recipe_data TEXT NOT NULL,
        viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        recipe_title TEXT NOT NULL,
        recipe_data TEXT NOT NULL,
        recipe_image TEXT,
        ingredients TEXT,
        saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, recipe_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ New database created with updated schema")
    print("=" * 50)
    print("📊 New empty database is ready")
    print("=" * 50)

if __name__ == "__main__":
    recreate_database()
