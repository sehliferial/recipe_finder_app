from tkinter import *
from tkinter import messagebox
from database import DatabaseManager
from api_handler import RecipeAPIHandler

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.db_manager = DatabaseManager()
        self.current_user = None  # تخزين معلومات المستخدم الحالي
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """إعداد نافذة التطبيق"""
        self.root.title("🍳 Recipe Finder Pro")
        self.root.geometry('550x600')
        self.root.configure(bg='#F8FAFF')
        
        # مركز النافذة
        self.center_window()
        
    def center_window(self):
        """توسيط النافذة على الشاشة"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """إنشاء واجهة المستخدم"""
        # إطار العنوان
        header_frame = Frame(self.root, bg='#5D7B9D', height=100)
        header_frame.pack(fill=X)
        
        Label(header_frame, 
              text="🍳 Recipe Finder Pro", 
              bg='#5D7B9D', 
              fg='white', 
              font=('Arial', 26, 'bold')).pack(pady=25)
        
        # إطار النموذج
        form_frame = Frame(self.root, bg='#F8FAFF', padx=50, pady=30)
        form_frame.pack(fill=BOTH, expand=True)
        
        # حقل اسم المستخدم
        Label(form_frame, 
              text='Username:', 
              font=('Arial', 12, 'bold'), 
              bg='#F8FAFF',
              fg='#2C3E50').grid(row=0, column=0, sticky='w', pady=(20, 5))
        
        self.username_entry = Entry(form_frame, 
                                    font=('Arial', 12), 
                                    width=35,
                                    bg='white',
                                    relief=SOLID,
                                    borderwidth=1)
        self.username_entry.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        
        # حقل كلمة المرور
        Label(form_frame, 
              text='Password:', 
              font=('Arial', 12, 'bold'), 
              bg='#F8FAFF',
              fg='#2C3E50').grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        self.password_entry = Entry(form_frame, 
                                    font=('Arial', 12), 
                                    width=35,
                                    show='•',
                                    bg='white',
                                    relief=SOLID,
                                    borderwidth=1)
        self.password_entry.grid(row=3, column=0, sticky='ew', pady=(0, 10))
        self.password_entry.bind('<Return>', lambda e: self.api_key_entry.focus())
        
        # حقل مفتاح API
        Label(form_frame, 
              text='API Key:', 
              font=('Arial', 12, 'bold'), 
              bg='#F8FAFF',
              fg='#2C3E50').grid(row=4, column=0, sticky='w', pady=(0, 5))
        
        self.api_key_entry = Entry(form_frame, 
                                   font=('Arial', 12), 
                                   width=35,
                                   bg='white',
                                   relief=SOLID,
                                   borderwidth=1)
        self.api_key_entry.grid(row=5, column=0, sticky='ew', pady=(0, 30))
        self.api_key_entry.bind('<Return>', lambda e: self.signup() if self.api_key_entry.get() else self.login())
        
        # أزرار التحكم
        button_frame = Frame(form_frame, bg='#F8FAFF')
        button_frame.grid(row=6, column=0, pady=30)
        
        # زر التسجيل
        self.signup_btn = Button(button_frame,
                                text="📝 Sign Up",
                                font=('Arial', 12, 'bold'),
                                width=15,
                                height=2,
                                bg='#3498DB',
                                fg='white',
                                activebackground='#2980B9',
                                command=self.signup)
        self.signup_btn.pack(side=LEFT, padx=10)
        
        # زر الدخول
        self.login_btn = Button(button_frame,
                               text="🔑 Log In",
                               font=('Arial', 12, 'bold'),
                               width=15,
                               height=2,
                               bg='#2ECC71',
                               fg='white',
                               activebackground='#27AE60',
                               command=self.login)
        self.login_btn.pack(side=LEFT, padx=10)
        
        # معلومات API
        info_frame = Frame(form_frame, bg='#F8FAFF', relief=GROOVE, borderwidth=1)
        info_frame.grid(row=7, column=0, pady=(20, 0), sticky='ew')
        
        Label(info_frame,
              text="ℹ️ Get your free API key from:",
              font=('Arial', 10),
              bg='#F8FAFF',
              fg='#34495E').pack(pady=5)
        
        LinkLabel = Label(info_frame,
                         text="🔗 spoonacular.com/food-api",
                         font=('Arial', 10, 'underline'),
                         bg='#F8FAFF',
                         fg='#3498DB',
                         cursor="hand2")
        LinkLabel.pack(pady=(0, 5))
        
        # إضافة حدث النقر
        LinkLabel.bind("<Button-1>", lambda e: self.open_spoonacular_website())
        
    def open_spoonacular_website(self):
        """فتح موقع Spoonacular"""
        import webbrowser
        webbrowser.open("https://spoonacular.com/food-api")
        
    def validate_inputs(self, username, password, api_key=None, require_api_key=False):
        """التحقق من صحة المدخلات"""
        if not username or not password:
            return False, "Please enter username and password"
            
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
            
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
            
        if require_api_key and (not api_key or len(api_key) < 10):
            return False, "Please enter a valid API key"
            
        return True, ""
        
    def signup(self):
        """تسجيل مستخدم جديد"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        api_key = self.api_key_entry.get().strip()
        
        # التحقق من المدخلات
        is_valid, message = self.validate_inputs(username, password, api_key, require_api_key=True)
        if not is_valid:
            messagebox.showwarning("Input Error", message)
            return
            
        try:
            connection, cursor = self.db_manager.connect()
            self.db_manager.initialize_database()
            
            # التحقق من صحة API Key
            api_handler = RecipeAPIHandler(api_key)
            if not api_handler.validate_api_key():
                messagebox.showwarning("API Error", "Invalid API key! Please check your key.")
                return
                
            # إنشاء المستخدم
            user_id = self.db_manager.create_user(username, password, api_key)
            if user_id:
                messagebox.showinfo("Success", "🎉 Account created successfully!")
                self.current_user = {"user_id": user_id, "username": username, "api_key": api_key}
                self.clear_entries()
                self.open_recipe_app()
            else:
                messagebox.showwarning("Error", "Username already exists!")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def login(self):
        """تسجيل الدخول"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # التحقق من المدخلات
        is_valid, message = self.validate_inputs(username, password)
        if not is_valid:
            messagebox.showwarning("Input Error", message)
            return
            
        try:
            connection, cursor = self.db_manager.connect()
            self.db_manager.initialize_database()
            
            # التحقق من بيانات الدخول
            user_data = self.db_manager.authenticate_user(username, password)
            
            if user_data:
                messagebox.showinfo("Success", f"👋 Welcome back, {username}!")
                self.current_user = {"user_id": user_data["user_id"], 
                                   "username": username, 
                                   "api_key": user_data["api_key"]}
                self.clear_entries()
                self.open_recipe_app()
            else:
                messagebox.showwarning("Error", "Invalid username or password!")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def clear_entries(self):
        """مسح حقول الإدخال"""
        self.username_entry.delete(0, END)
        self.password_entry.delete(0, END)
        self.api_key_entry.delete(0, END)
        
    def open_recipe_app(self):
        """فتح تطبيق الوصفات"""
        if not self.current_user:
            return
            
        from recipe_app import RecipeApp
        
        self.root.withdraw()
        
        app_window = Toplevel(self.root)
        app_window.protocol("WM_DELETE_WINDOW", lambda: self.on_app_close(app_window))
        
        RecipeApp(app_window, self.root, self.current_user, self.db_manager)
        
    def on_app_close(self, app_window):
        """معالجة إغلاق نافذة التطبيق"""
        app_window.destroy()
        self.root.deiconify()

# دالة اختبارية
def test_login_window():
    """اختبار نافذة تسجيل الدخول"""
    print("Testing Login Window...")
    
    # اختبار الوظائف الأساسية
    root = Tk()
    app = LoginWindow(root)
    
    # اختبار التحقق من المدخلات
    test_cases = [
        ("", "pass123", "apikey123", False, "empty username"),
        ("user", "pass", "apikey123", False, "short password"),
        ("user123", "pass123", "short", False, "short api key"),
        ("validuser", "validpass123", "validapikey12345", True, "valid inputs"),
    ]
    
    for username, password, api_key, expected, description in test_cases:
        is_valid, message = app.validate_inputs(username, password, api_key, require_api_key=True)
        print(f"{description}: {is_valid == expected} (expected {expected}, got {is_valid})")
    
    root.destroy()

if __name__ == "__main__":
    # يمكنك تشغيل هذا لاختبار الملف بمفرده
    test_login_window()