import sqlite3
import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

class DatabaseManager:
    def __init__(self, db_name='recipes.db'):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """إنشاء اتصال بقاعدة البيانات"""
        self.connection = sqlite3.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        return self.connection, self.cursor
        
    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        if self.connection:
            self.connection.close()
            
    def create_tables_if_not_exist(self):
        """إنشاء الجداول إذا لم تكن موجودة (بدون حذف القديمة)"""
        # جدول المستخدمين
        create_users_table = '''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL UNIQUE,
            psw TEXT NOT NULL,
            api_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        
        # جدول البحث التاريخي
        create_search_history_table = '''
        CREATE TABLE IF NOT EXISTS search_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ingredients TEXT NOT NULL,
            results_count INTEGER DEFAULT 0,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        '''
        
        # جدول المشاهدة
        create_view_history_table = '''
        CREATE TABLE IF NOT EXISTS view_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            recipe_title TEXT NOT NULL,
            recipe_data TEXT NOT NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        '''
        
        # جدول المفضلة
        create_favorites_table = '''
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
        '''
        
        # تنفيذ إنشاء الجداول
        self.cursor.execute(create_users_table)
        self.cursor.execute(create_search_history_table)
        self.cursor.execute(create_view_history_table)
        self.cursor.execute(create_favorites_table)
        self.connection.commit()
        
        print("✅ Tables checked/created without deleting existing data")
        
    def initialize_database(self):
        """تهيئة الجداول في قاعدة البيانات (تحذف القديمة) - استخدام بحذر!"""
        # حذف الجداول القديمة أولاً
        self.cursor.execute("DROP TABLE IF EXISTS favorites")
        self.cursor.execute("DROP TABLE IF EXISTS view_history")
        self.cursor.execute("DROP TABLE IF EXISTS search_history")
        
        # إنشاء الجداول الجديدة
        self.create_tables_if_not_exist()
        
    def check_database_status(self):
        """فحص حالة قاعدة البيانات"""
        try:
            # التحقق من وجود الجداول
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = self.cursor.fetchall()
            print("📊 Database tables:", [table[0] for table in tables])
            
            # التحقق من عدد الوصفات المفضلة
            self.cursor.execute("SELECT COUNT(*) FROM favorites")
            count = self.cursor.fetchone()[0]
            print(f"⭐ Total favorites count: {count}")
            
            # عرض أمثلة
            if count > 0:
                self.cursor.execute("SELECT user_id, recipe_title FROM favorites LIMIT 5")
                favorites = self.cursor.fetchall()
                print(f"Sample favorites: {[f[1] for f in favorites]}")
                
        except Exception as e:
            print(f"Database check error: {e}")
            
    def hash_password(self, password):
        """تجزئة كلمة المرور"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def create_user(self, username, password, api_key):
        """إنشاء مستخدم جديد"""
        hashed_password = self.hash_password(password)
        
        try:
            query = '''
            INSERT INTO users (user_name, psw, api_key) 
            VALUES (?, ?, ?)
            '''
            self.cursor.execute(query, (username, hashed_password, api_key))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
            
    def authenticate_user(self, username, password):
        """مصادقة المستخدم"""
        hashed_password = self.hash_password(password)
        
        query = '''
        SELECT id, api_key FROM users 
        WHERE user_name = ? AND psw = ?
        '''
        self.cursor.execute(query, (username, hashed_password))
        result = self.cursor.fetchone()
        
        if result:
            return {"user_id": result[0], "api_key": result[1]}
        return None
        
    def add_search_history(self, user_id, ingredients, results_count):
        """إضافة بحث إلى التاريخ"""
        query = '''
        INSERT INTO search_history (user_id, ingredients, results_count)
        VALUES (?, ?, ?)
        '''
        self.cursor.execute(query, (user_id, ingredients, results_count))
        self.connection.commit()
        return self.cursor.lastrowid
        
    def get_search_history(self, user_id, limit=10):
        """الحصول على تاريخ البحث"""
        query = '''
        SELECT ingredients, results_count, search_date
        FROM search_history
        WHERE user_id = ?
        ORDER BY search_date DESC
        LIMIT ?
        '''
        self.cursor.execute(query, (user_id, limit))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
        
    def clear_search_history(self, user_id):
        """مسح تاريخ البحث"""
        query = "DELETE FROM search_history WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        self.connection.commit()
        return self.cursor.rowcount
        
    def add_to_view_history(self, user_id, recipe_id, recipe_title, recipe_data):
        """إضافة وصفة إلى تاريخ المشاهدة"""
        try:
            # تحويل recipe_data إلى JSON إذا كان dict
            if isinstance(recipe_data, dict):
                recipe_data_json = json.dumps(recipe_data, ensure_ascii=False)
            else:
                recipe_data_json = str(recipe_data)
            
            query = '''
            INSERT INTO view_history (user_id, recipe_id, recipe_title, recipe_data)
            VALUES (?, ?, ?, ?)
            '''
            self.cursor.execute(query, (user_id, recipe_id, recipe_title, recipe_data_json))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error adding to view history: {e}")
            return None
        
    def get_view_history(self, user_id, limit=20):
        """الحصول على تاريخ المشاهدة"""
        query = '''
        SELECT recipe_id, recipe_title, recipe_data, viewed_at
        FROM view_history
        WHERE user_id = ?
        ORDER BY viewed_at DESC
        LIMIT ?
        '''
        self.cursor.execute(query, (user_id, limit))
        rows = self.cursor.fetchall()
        
        history = []
        for row in rows:
            try:
                recipe_data = json.loads(row['recipe_data'])
                history.append({
                    'recipe_id': row['recipe_id'],
                    'recipe_title': row['recipe_title'],
                    'recipe_data': recipe_data,
                    'viewed_at': row['viewed_at']
                })
            except Exception as e:
                print(f"Error parsing recipe data: {e}")
                history.append({
                    'recipe_id': row['recipe_id'],
                    'recipe_title': row['recipe_title'],
                    'recipe_data': {},
                    'viewed_at': row['viewed_at']
                })
        
        return history
        
    def clear_view_history(self, user_id):
        """مسح تاريخ المشاهدة"""
        query = "DELETE FROM view_history WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        self.connection.commit()
        return self.cursor.rowcount
        
    def add_to_favorites(self, user_id, recipe_id, recipe_title, recipe_data, recipe_image="", ingredients=""):
        """إضافة وصفة إلى المفضلة"""
        try:
            # تحويل recipe_data إلى JSON
            if isinstance(recipe_data, dict):
                recipe_data_json = json.dumps(recipe_data, ensure_ascii=False)
            else:
                recipe_data_json = str(recipe_data)
            
            query = '''
            INSERT INTO favorites (user_id, recipe_id, recipe_title, recipe_data, recipe_image, ingredients)
            VALUES (?, ?, ?, ?, ?, ?)
            '''
            self.cursor.execute(query, (user_id, recipe_id, recipe_title, recipe_data_json, recipe_image, ingredients))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            # موجودة بالفعل
            return False
        except Exception as e:
            print(f"Error adding to favorites: {e}")
            return False
            
    def get_favorites(self, user_id):
        """الحصول على الوصفات المفضلة"""
        query = '''
        SELECT recipe_id, recipe_title, recipe_data, recipe_image, ingredients, saved_date
        FROM favorites
        WHERE user_id = ?
        ORDER BY saved_date DESC
        '''
        self.cursor.execute(query, (user_id,))
        rows = self.cursor.fetchall()
        
        favorites = []
        for row in rows:
            try:
                recipe_data = json.loads(row['recipe_data'])
                favorites.append({
                    'recipe_id': row['recipe_id'],
                    'recipe_title': row['recipe_title'],
                    'recipe_data': recipe_data,
                    'recipe_image': row['recipe_image'],
                    'ingredients': row['ingredients'],
                    'saved_date': row['saved_date']
                })
            except Exception as e:
                print(f"Error parsing favorite data: {e}")
                favorites.append({
                    'recipe_id': row['recipe_id'],
                    'recipe_title': row['recipe_title'],
                    'recipe_data': {},
                    'recipe_image': row['recipe_image'],
                    'ingredients': row['ingredients'],
                    'saved_date': row['saved_date']
                })
        
        return favorites
        
    def remove_from_favorites(self, user_id, recipe_id):
        """إزالة وصفة من المفضلة"""
        query = "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?"
        self.cursor.execute(query, (user_id, recipe_id))
        self.connection.commit()
        return self.cursor.rowcount > 0
        
    def is_favorite(self, user_id, recipe_id):
        """التحقق إذا كانت الوصفة مفضلة"""
        query = "SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?"
        self.cursor.execute(query, (user_id, recipe_id))
        return self.cursor.fetchone() is not None
        
    def get_favorites_count(self, user_id):
        """الحصول على عدد الوصفات المفضلة للمستخدم"""
        query = "SELECT COUNT(*) FROM favorites WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
