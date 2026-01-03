from tkinter import Tk
from login_window import LoginWindow

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    root = Tk()
    
    try:
        app = LoginWindow(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # تنظيف الموارد عند الخروج
        if hasattr(app, 'db_manager'):
            app.db_manager.close()

if __name__ == "__main__":
    main()