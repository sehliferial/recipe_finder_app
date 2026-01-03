import os
import sqlite3

def recreate_database():
    """إعادة إنشاء قاعدة البيانات"""
    # حذف الملفات القديمة
    if os.path.exists('recipes.db'):
        os.remove('recipes.db')
    if os.path.exists('recipes.db-journal'):
        os.remove('recipes.db-journal')
    
    print("✅ Old database deleted")
    
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

if __name__ == "__main__":
    recreate_database()