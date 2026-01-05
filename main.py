from tkinter import Tk
from login_window import LoginWindow
import os
import shutil
from datetime import datetime

def backup_database():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        if os.path.exists('recipes.db'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f'recipes_backup_{timestamp}.db'
            shutil.copy2('recipes.db', backup_name)
            print(f"✅ Database backed up as: {backup_name}")
            
            # حذف النسخ القديمة (احتفظ بـ5 نسخ فقط)
            backup_files = [f for f in os.listdir('.') if f.startswith('recipes_backup_') and f.endswith('.db')]
            backup_files.sort(reverse=True)
            
            for old_backup in backup_files[5:]:  # احتفظ بـ5 نسخ فقط
                os.remove(old_backup)
                print(f"🗑️ Deleted old backup: {old_backup}")
            
            return backup_name
        else:
            print("⚠️ No database found to backup")
            return None
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def check_database_exists():
    """التحقق من وجود قاعدة البيانات"""
    if not os.path.exists('recipes.db'):
        print("ℹ️ No database found. A new one will be created.")
        return False
    
    # التحقق من حجم قاعدة البيانات
    size = os.path.getsize('recipes.db')
    print(f"📁 Database size: {size:,} bytes")
    
    if size == 0:
        print("⚠️ Database file is empty!")
        return False
    
    return True

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    print("=" * 50)
    print("🍳 Starting Recipe Finder Pro")
    print("=" * 50)
    
    # نسخة احتياطية
    backup_database()
    
    # التحقق من قاعدة البيانات
    check_database_exists()
    
    root = Tk()
    
    try:
        app = LoginWindow(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # تنظيف الموارد عند الخروج
        if hasattr(app, 'db_manager'):
            app.db_manager.close()
        print("\n👋 Application closed")

if __name__ == "__main__":
    main()
