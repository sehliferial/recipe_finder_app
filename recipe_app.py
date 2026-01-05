from tkinter import *
from tkinter import messagebox, scrolledtext
from tkinter import ttk
from api_handler import RecipeAPIHandler
from database import DatabaseManager
import threading
import json
from datetime import datetime

class RecipeApp:
    def __init__(self, window, login_window, user_data, db_manager):
        self.window = window
        self.login_window = login_window
        self.user_data = user_data
        self.db_manager = db_manager
        self.api_handler = RecipeAPIHandler(user_data["api_key"])
        
        self.setup_window()
        self.create_widgets()
        self.recipes = []
        self.current_images = []
        self.image_cache = {}
        
    def setup_window(self):
        """إعداد نافذة التطبيق"""
        self.window.title(f"🍳 Recipe Finder - {self.user_data['username']}")
        self.window.geometry('900x750')
        self.window.configure(bg='#F8FAFF')
        
        # مركز النافذة
        self.center_window()
        
    def center_window(self):
        """توسيط النافذة على الشاشة"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """إنشاء واجهة المستخدم"""
        # شريط العنوان
        self.create_header()
        
        # إطار البحث
        self.create_search_frame()
        
        # إطار النتائج
        self.create_results_frame()
        
        # شريط الحالة
        self.create_status_bar()
        
    def create_header(self):
        """إنشاء شريط العنوان"""
        header_frame = Frame(self.window, bg='#5D7B9D', height=80)
        header_frame.pack(fill=X)
        
        title_label = Label(header_frame,
                          text=f"🍳 Welcome, {self.user_data['username']}!",
                          bg='#5D7B9D',
                          fg='white',
                          font=('Arial', 16, 'bold'))
        title_label.pack(side=LEFT, padx=20, pady=20)
        
        menu_frame = Frame(header_frame, bg='#5D7B9D')
        menu_frame.pack(side=RIGHT, padx=20, pady=20)
        
        # ✅ أضف زر Debug للفحص
        debug_btn = Button(menu_frame,
                         text="🔧 Debug DB",
                         font=('Arial', 8, 'bold'),
                         bg='#34495E',
                         fg='white',
                         command=self.debug_database)
        debug_btn.pack(side=LEFT, padx=2)
        
        history_btn = Button(menu_frame,
                           text="📜 View History",
                           font=('Arial', 10, 'bold'),
                           bg='#8E44AD',
                           fg='white',
                           command=self.show_view_history)
        history_btn.pack(side=LEFT, padx=5)
        
        favorites_btn = Button(menu_frame,
                             text="⭐ Favorites",
                             font=('Arial', 10, 'bold'),
                             bg='#F39C12',
                             fg='white',
                             command=self.show_favorites)
        favorites_btn.pack(side=LEFT, padx=5)
        
        logout_btn = Button(menu_frame,
                          text="🚪 Logout",
                          font=('Arial', 10, 'bold'),
                          bg='#E74C3C',
                          fg='white',
                          command=self.logout)
        logout_btn.pack(side=LEFT, padx=5)
    
    def debug_database(self):
        """فحص قاعدة البيانات"""
        try:
            # التحقق من الجداول
            self.db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = self.db_manager.cursor.fetchall()
            
            # عرض المعلومات
            info = "📊 Database Debug Info:\n\n"
            info += f"User ID: {self.user_data['user_id']}\n"
            info += f"Username: {self.user_data['username']}\n\n"
            info += "📋 Tables in database:\n"
            
            for table in tables:
                table_name = table[0]
                info += f"\n• {table_name}\n"
                
                # عدّ الصفوف في كل جدول
                if table_name != 'sqlite_sequence':
                    self.db_manager.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = self.db_manager.cursor.fetchone()[0]
                    info += f"  📈 Rows: {count}\n"
                    
                    # عرض بعض البيانات من favorites لهذا المستخدم
                    if table_name == 'favorites':
                        self.db_manager.cursor.execute(
                            f"SELECT recipe_id, recipe_title, saved_date FROM {table_name} WHERE user_id = ? ORDER BY saved_date DESC LIMIT 5", 
                            (self.user_data['user_id'],)
                        )
                        favs = self.db_manager.cursor.fetchall()
                        if favs:
                            info += "  💾 User's favorites:\n"
                            for fav in favs:
                                info += f"    • {fav[1]} (ID: {fav[0]}) - {fav[2]}\n"
                        else:
                            info += "  ❌ No favorites for this user\n"
                    
                    # عرض بيانات search_history لهذا المستخدم
                    elif table_name == 'search_history':
                        self.db_manager.cursor.execute(
                            f"SELECT ingredients, search_date FROM {table_name} WHERE user_id = ? ORDER BY search_date DESC LIMIT 3", 
                            (self.user_data['user_id'],)
                        )
                        searches = self.db_manager.cursor.fetchall()
                        if searches:
                            info += "  🔍 Recent searches:\n"
                            for search in searches:
                                info += f"    • {search[0]} - {search[1]}\n"
                    
                    # عرض بيانات view_history لهذا المستخدم
                    elif table_name == 'view_history':
                        self.db_manager.cursor.execute(
                            f"SELECT recipe_title, viewed_at FROM {table_name} WHERE user_id = ? ORDER BY viewed_at DESC LIMIT 3", 
                            (self.user_data['user_id'],)
                        )
                        views = self.db_manager.cursor.fetchall()
                        if views:
                            info += "  👁️ Recent views:\n"
                            for view in views:
                                info += f"    • {view[0]} - {view[1]}\n"
            
            # التحقق من وجود المستخدم
            self.db_manager.cursor.execute("SELECT id, user_name, created_at FROM users WHERE id = ?", 
                                         (self.user_data['user_id'],))
            user_info = self.db_manager.cursor.fetchone()
            if user_info:
                info += f"\n👤 User info:\n"
                info += f"  • ID: {user_info[0]}\n"
                info += f"  • Username: {user_info[1]}\n"
                info += f"  • Created: {user_info[2]}\n"
            
            messagebox.showinfo("Database Debug", info)
            
        except Exception as e:
            messagebox.showerror("Debug Error", f"Error checking database:\n{str(e)}")
    
    def create_search_frame(self):
        """إنشاء إطار البحث"""
        search_frame = Frame(self.window, bg='#F8FAFF', padx=20, pady=20)
        search_frame.pack(fill=X)
        
        Label(search_frame,
              text="🔍 Search Recipes by Ingredients:",
              font=('Arial', 14, 'bold'),
              bg='#F8FAFF',
              fg='#2C3E50').pack(anchor='w', pady=(0, 10))
        
        input_frame = Frame(search_frame, bg='#F8FAFF')
        input_frame.pack(fill=X)
        
        self.ingredients_entry = Entry(input_frame,
                                      font=('Arial', 12),
                                      width=50,
                                      bg='white',
                                      relief=SOLID,
                                      borderwidth=1)
        self.ingredients_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        self.ingredients_entry.bind('<Return>', lambda e: self.search_recipes())
        self.ingredients_entry.focus_set()
        
        self.search_btn = Button(input_frame,
                                text="🔎 Search",
                                font=('Arial', 12, 'bold'),
                                bg='#3498DB',
                                fg='white',
                                width=12,
                                command=self.search_recipes)
        self.search_btn.pack(side=LEFT)
        
        examples = [
            "chicken, rice, tomato",
            "eggs, milk, flour",
            "beef, potato, carrot",
            "fish, lemon, onion"
        ]
        
        for example in examples:
            Label(search_frame,
                 text=f"Example: {example}",
                 font=('Arial', 10, 'italic'),
                 fg='#7F8C8D',
                 bg='#F8FAFF').pack(anchor='w', pady=(2, 0))
            
    def create_results_frame(self):
        """إنشاء إطار النتائج"""
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        
        # تبويب النتائج
        self.results_tab = Frame(self.notebook, bg='#F8FAFF')
        self.notebook.add(self.results_tab, text="📋 Results")
        
        # Canvas وScrollbar للنتائج
        results_container = Frame(self.results_tab, bg='#F8FAFF')
        results_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = Canvas(results_container, bg='white', highlightthickness=0)
        scrollbar = Scrollbar(results_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg='white')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # تبويب التفاصيل
        self.details_tab = Frame(self.notebook, bg='#F8FAFF')
        self.notebook.add(self.details_tab, text="📄 Full Recipe")
        
        # إطار تفاصيل الوصفة مع scroll
        details_container = Frame(self.details_tab, bg='#F8FAFF')
        details_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Canvas للتفاصيل
        self.details_canvas = Canvas(details_container, bg='white', highlightthickness=0)
        details_scrollbar = Scrollbar(details_container, orient="vertical", command=self.details_canvas.yview)
        self.details_frame = Frame(self.details_canvas, bg='white')
        
        self.details_frame.bind(
            "<Configure>",
            lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        )
        
        self.details_canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        self.details_canvas.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_canvas.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
        
    def search_recipes(self):
        """بحث الوصفات"""
        ingredients = self.ingredients_entry.get().strip()
        
        if not ingredients:
            messagebox.showwarning("Input Error", "Please enter ingredients!")
            return
            
        self.search_btn.config(state=DISABLED)
        self.status_bar.config(text="Searching for recipes...")
        
        # مسح النتائج السابقة
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.current_images.clear()
        self.image_cache.clear()
        
        # البحث في thread منفصل
        def search_thread():
            try:
                self.recipes = self.api_handler.fetch_recipes_by_ingredients(ingredients, number=5)
                
                self.window.after(0, lambda: self.display_search_results(ingredients))
                
            except Exception as e:
                self.window.after(0, lambda: self.handle_search_error(e))
        
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
    
    def display_search_results(self, ingredients):
        """عرض نتائج البحث"""
        if self.recipes:
            self.display_results_basic()
            self.load_images_in_background()
            
            # حفظ في تاريخ البحث
            try:
                self.db_manager.add_search_history(
                    self.user_data["user_id"],
                    ingredients,
                    len(self.recipes)
                )
            except Exception as e:
                print(f"Note: Could not save search history: {e}")
            
            self.status_bar.config(text=f"Found {len(self.recipes)} recipes with full details")
        else:
            no_results = Label(self.scrollable_frame,
                             text="No recipes found. Try different ingredients.",
                             font=('Arial', 12),
                             bg='white',
                             fg='#7F8C8D')
            no_results.pack(pady=50)
            self.status_bar.config(text="No recipes found")
        
        self.search_btn.config(state=NORMAL)
    
    def handle_search_error(self, error):
        """معالجة خطأ البحث"""
        messagebox.showerror("Error", f"Search failed: {str(error)}")
        self.status_bar.config(text="Search error")
        self.search_btn.config(state=NORMAL)
    
    def display_results_basic(self):
        """عرض النتائج الأساسية"""
        for i, recipe in enumerate(self.recipes, 1):
            self.create_recipe_card_basic(i, recipe)
    
    def create_recipe_card_basic(self, index, recipe):
        """إنشاء بطاقة وصفة أساسية"""
        card_frame = Frame(self.scrollable_frame,
                          bg='white',
                          relief=GROOVE,
                          borderwidth=1,
                          padx=10,
                          pady=10)
        card_frame.pack(fill=X, padx=5, pady=5)
        
        card_frame.recipe_id = recipe.get('id')
        card_frame.recipe_data = recipe
        
        content_frame = Frame(card_frame, bg='white')
        content_frame.pack(fill=X)
        
        # إطار الصورة (مؤقت)
        image_frame = Frame(content_frame, bg='#F0F0F0', width=100, height=100)
        image_frame.pack(side=LEFT, padx=(0, 15))
        image_frame.pack_propagate(False)
        
        loading_label = Label(image_frame,
                            text="Loading...",
                            font=('Arial', 8),
                            bg='#F0F0F0',
                            fg='#666666')
        loading_label.place(relx=0.5, rely=0.5, anchor='center')
        
        card_frame.image_frame = image_frame
        
        info_frame = Frame(content_frame, bg='white')
        info_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        title = recipe.get('title', 'No Title')
        title_label = Label(info_frame,
                          text=f"{index}. {title}",
                          font=('Arial', 12, 'bold'),
                          bg='white',
                          fg='#2C3E50',
                          anchor='w')
        title_label.pack(anchor='w')
        
        # معلومات إضافية
        if recipe.get('readyInMinutes'):
            time_label = Label(info_frame,
                             text=f"⏱️ {recipe.get('readyInMinutes')} min | 👥 {recipe.get('servings', 1)} servings",
                             font=('Arial', 9),
                             bg='white',
                             fg='#7F8C8D',
                             anchor='w')
            time_label.pack(anchor='w', pady=(2, 0))
        
        used = recipe.get('usedIngredientCount', 0)
        missed = recipe.get('missedIngredientCount', 0)
        
        if used > 0 or missed > 0:
            stats_frame = Frame(info_frame, bg='white')
            stats_frame.pack(anchor='w', pady=5)
            
            stats_text = f"✅ Used: {used} | ❌ Missing: {missed}"
            Label(stats_frame,
                 text=stats_text,
                 font=('Arial', 10),
                 bg='white',
                 fg='#7F8C8D').pack(side=LEFT)
        
        actions_frame = Frame(card_frame, bg='white')
        actions_frame.pack(anchor='e', pady=(5, 0))
        
        Button(actions_frame,
               text="📖 View Full Recipe",
               font=('Arial', 9, 'bold'),
               bg='#3498DB',
               fg='white',
               command=lambda r=recipe: self.show_full_recipe(r)).pack(side=LEFT, padx=(0, 5))
        
        recipe_id = recipe.get('id')
        is_fav = self.db_manager.is_favorite(self.user_data["user_id"], recipe_id)
        
        fav_text = "⭐ Remove Favorite" if is_fav else "☆ Add to Favorites"
        fav_color = "#F39C12" if is_fav else "#BDC3C7"
        
        Button(actions_frame,
               text=fav_text,
               font=('Arial', 9),
               bg=fav_color,
               fg='white',
               command=lambda r=recipe: self.toggle_favorite(r)).pack(side=LEFT)
    
    def show_full_recipe(self, recipe):
        """عرض الوصفة الكاملة"""
        # حفظ في تاريخ المشاهدة
        try:
            recipe_id = recipe.get('id')
            recipe_title = recipe.get('title', 'No Title')
            recipe_data = json.dumps(recipe)
            
            self.db_manager.add_to_view_history(
                self.user_data["user_id"],
                recipe_id,
                recipe_title,
                recipe_data
            )
        except Exception as e:
            print(f"Note: Could not save to view history: {e}")
        
        # عرض الوصفة
        self.display_full_recipe(recipe)
        self.notebook.select(1)  # التبديل لتبويب التفاصيل
        self.status_bar.config(text=f"Viewing: {recipe.get('title', 'Recipe')}")
    
    def display_full_recipe(self, recipe):
        """عرض الوصفة الكاملة"""
        # مسح الإطار السابق
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        # إطار رئيسي للوصفة
        main_frame = Frame(self.details_frame, bg='white', padx=20, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # عنوان الوصفة
        title = recipe.get('title', 'No Title')
        title_label = Label(main_frame,
                          text=title,
                          font=('Arial', 20, 'bold'),
                          bg='white',
                          fg='#2C3E50',
                          wraplength=700,
                          justify='center')
        title_label.pack(pady=(0, 20))
        
        # معلومات أساسية
        info_frame = Frame(main_frame, bg='#F8FAFF', relief=GROOVE, borderwidth=1, padx=15, pady=10)
        info_frame.pack(fill=X, pady=(0, 20))
        
        # وقت التحضير والمقادير
        ready_time = recipe.get('readyInMinutes', 0)
        servings = recipe.get('servings', 0)
        health_score = recipe.get('healthScore', 0)
        
        info_text = f"⏱️ Ready in: {ready_time} minutes"
        if servings > 0:
            info_text += f" | 👥 Servings: {servings}"
        if health_score > 0:
            info_text += f" | 💚 Health Score: {health_score}/100"
        
        Label(info_frame,
              text=info_text,
              font=('Arial', 12),
              bg='#F8FAFF',
              fg='#2C3E50').pack(anchor='w')
        
        # الأنواع والأطباق
        if recipe.get('diets'):
            diets = ", ".join(recipe.get('diets', []))
            Label(info_frame,
                  text=f"🥗 Diets: {diets}",
                  font=('Arial', 11),
                  bg='#F8FAFF',
                  fg='#27AE60').pack(anchor='w', pady=(5, 0))
        
        if recipe.get('cuisines'):
            cuisines = ", ".join(recipe.get('cuisines', []))
            Label(info_frame,
                  text=f"🌍 Cuisines: {cuisines}",
                  font=('Arial', 11),
                  bg='#F8FAFF',
                  fg='#E67E22').pack(anchor='w', pady=(2, 0))
        
        # المكونات
        ingredients_frame = Frame(main_frame, bg='white')
        ingredients_frame.pack(fill=X, pady=(0, 20))
        
        Label(ingredients_frame,
              text="📝 Ingredients:",
              font=('Arial', 16, 'bold'),
              bg='white',
              fg='#2C3E50').pack(anchor='w', pady=(0, 10))
        
        # المكونات الأساسية
        ingredients_listbox = Listbox(ingredients_frame,
                                     font=('Arial', 11),
                                     bg='white',
                                     relief=FLAT,
                                     height=8)
        ingredients_listbox.pack(fill=X, pady=(0, 10))
        
        # إضافة المكونات
        extended_ingredients = recipe.get('extendedIngredients', [])
        if extended_ingredients:
            for ing in extended_ingredients:
                name = ing.get('name', '')
                amount = ing.get('amount', 0)
                unit = ing.get('unit', '')
                original = ing.get('original', f"{amount} {unit} {name}".strip())
                ingredients_listbox.insert(END, f"• {original}")
        else:
            # استخدام المكونات البسيطة إذا لم تكن هناك تفاصيل
            used_ingredients = recipe.get('usedIngredients', [])
            missed_ingredients = recipe.get('missedIngredients', [])
            
            if used_ingredients:
                ingredients_listbox.insert(END, "✅ Used Ingredients:")
                for ing in used_ingredients[:10]:
                    name = ing.get('name', 'Unknown')
                    ingredients_listbox.insert(END, f"  • {name}")
            
            if missed_ingredients:
                ingredients_listbox.insert(END, "\n❌ Missing Ingredients:")
                for ing in missed_ingredients[:5]:
                    name = ing.get('name', 'Unknown')
                    ingredients_listbox.insert(END, f"  • {name}")
        
        # الخطوات
        instructions_frame = Frame(main_frame, bg='white')
        instructions_frame.pack(fill=BOTH, expand=True)
        
        Label(instructions_frame,
              text="👩‍🍳 Instructions:",
              font=('Arial', 16, 'bold'),
              bg='white',
              fg='#2C3E50').pack(anchor='w', pady=(0, 10))
        
        # عرض الخطوات
        instructions_text = scrolledtext.ScrolledText(instructions_frame,
                                                     font=('Arial', 11),
                                                     wrap=WORD,
                                                     height=15,
                                                     bg='white',
                                                     relief=SOLID,
                                                     borderwidth=1)
        instructions_text.pack(fill=BOTH, expand=True)
        
        # تحليل التعليمات
        analyzed_instructions = recipe.get('analyzedInstructions', [])
        if analyzed_instructions:
            for section in analyzed_instructions:
                section_name = section.get('name', 'Instructions')
                if section_name and section_name != 'Instructions':
                    instructions_text.insert(END, f"\n{section_name}:\n")
                
                steps = section.get('steps', [])
                for step in steps:
                    step_num = step.get('number', 0)
                    step_text = step.get('step', '')
                    if step_text:
                        instructions_text.insert(END, f"\n{step_num}. {step_text}\n")
        else:
            # استخدام التعليمات النصية البسيطة
            instructions = recipe.get('instructions', '')
            if instructions:
                instructions_text.insert(END, instructions)
            else:
                instructions_text.insert(END, "No detailed instructions available.")
        
        instructions_text.config(state=DISABLED)
        
        # أزرار التحكم
        control_frame = Frame(main_frame, bg='white')
        control_frame.pack(fill=X, pady=(20, 0))
        
        # زر المفضلة
        recipe_id = recipe.get('id')
        is_fav = self.db_manager.is_favorite(self.user_data["user_id"], recipe_id)
        
        fav_text = "⭐ Remove from Favorites" if is_fav else "☆ Add to Favorites"
        fav_color = "#F39C12" if is_fav else "#BDC3C7"
        
        Button(control_frame,
               text=fav_text,
               font=('Arial', 11, 'bold'),
               bg=fav_color,
               fg='white',
               padx=20,
               command=lambda r=recipe: self.toggle_favorite(r)).pack(side=LEFT, padx=5)
        
        Button(control_frame,
               text="📋 Back to Results",
               font=('Arial', 11),
               bg='#3498DB',
               fg='white',
               padx=20,
               command=lambda: self.notebook.select(0)).pack(side=LEFT, padx=5)
    
    def toggle_favorite(self, recipe):
        """إضافة/إزالة من المفضلة"""
        recipe_id = recipe.get('id')
        title = recipe.get('title', 'No Title')
        image_url = self.api_handler.get_recipe_image_url(recipe)
        ingredients = self.ingredients_entry.get()
        
        is_fav = self.db_manager.is_favorite(self.user_data["user_id"], recipe_id)
        
        if is_fav:
            success = self.db_manager.remove_from_favorites(self.user_data["user_id"], recipe_id)
            if success:
                messagebox.showinfo("Success", "Removed from favorites!")
                # تحديث الواجهة
                self.update_favorite_buttons(recipe_id, False)
        else:
            success = self.db_manager.add_to_favorites(
                self.user_data["user_id"],
                recipe_id,
                title,
                recipe,  # حفظ البيانات الكاملة
                image_url,
                ingredients
            )
            
            if success:
                messagebox.showinfo("Success", "Added to favorites!")
                # تحديث الواجهة
                self.update_favorite_buttons(recipe_id, True)
            else:
                messagebox.showwarning("Warning", "Already in favorites!")
    
    def update_favorite_buttons(self, recipe_id, is_favorite):
        """تحديث أزرار المفضلة"""
        # تحديث أزرار في نتائج البحث
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'recipe_id') and widget.recipe_id == recipe_id:
                for child in widget.winfo_children():
                    if isinstance(child, Frame):  # إطار الإجراءات
                        for btn in child.winfo_children():
                            if "Favorite" in btn.cget('text'):
                                new_text = "⭐ Remove Favorite" if is_favorite else "☆ Add to Favorites"
                                new_color = "#F39C12" if is_favorite else "#BDC3C7"
                                btn.config(text=new_text, bg=new_color)
    
    def show_view_history(self):
        """عرض تاريخ المشاهدة"""
        # إنشاء نافذة جديدة
        history_window = Toplevel(self.window)
        history_window.title("View History")
        history_window.geometry("800x600")
        history_window.configure(bg='#F8FAFF')
        
        Label(history_window,
              text="📜 Recently Viewed Recipes",
              font=('Arial', 16, 'bold'),
              bg='#F8FAFF',
              fg='#2C3E50').pack(pady=20)
        
        container = Frame(history_window, bg='#F8FAFF')
        container.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        
        # الحصول على التاريخ
        history = self.db_manager.get_view_history(self.user_data["user_id"], limit=20)
        
        if not history:
            Label(container,
                  text="No recently viewed recipes.",
                  font=('Arial', 12),
                  bg='#F8FAFF',
                  fg='#7F8C8D').pack(pady=50)
        else:
            # Canvas للتاريخ
            history_canvas = Canvas(container, bg='#F8FAFF', highlightthickness=0)
            scrollbar = Scrollbar(container, orient="vertical", command=history_canvas.yview)
            history_frame = Frame(history_canvas, bg='#F8FAFF')
            
            history_frame.bind(
                "<Configure>",
                lambda e: history_canvas.configure(scrollregion=history_canvas.bbox("all"))
            )
            
            history_canvas.create_window((0, 0), window=history_frame, anchor="nw")
            history_canvas.configure(yscrollcommand=scrollbar.set)
            
            history_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # عرض كل وصفة في التاريخ
            for item in history:
                self.create_history_item(history_frame, item, history_window)
        
        # إطار للأزرار
        button_frame = Frame(history_window, bg='#F8FAFF')
        button_frame.pack(fill=X, padx=20, pady=10)
        
        Button(button_frame,
               text="🗑️ Clear History",
               font=('Arial', 10),
               bg='#E74C3C',
               fg='white',
               command=lambda: self.clear_view_history(history_window)).pack(side=LEFT, padx=5)
        
        Button(button_frame,
               text="✕ Close",
               font=('Arial', 10),
               bg='#7F8C8D',
               fg='white',
               command=history_window.destroy).pack(side=RIGHT, padx=5)
    
    def create_history_item(self, parent_frame, history_item, history_window):
        """إنشاء عنصر في التاريخ"""
        frame = Frame(parent_frame,
                     bg='white',
                     relief=GROOVE,
                     borderwidth=1,
                     padx=15,
                     pady=10)
        frame.pack(fill=X, padx=5, pady=5)
        
        title = history_item.get('recipe_title', 'Unknown Recipe')
        viewed_at = history_item.get('viewed_at', '')
        recipe_data = history_item.get('recipe_data', {})
        
        Label(frame,
              text=title,
              font=('Arial', 12, 'bold'),
              bg='white',
              fg='#2C3E50',
              anchor='w').pack(anchor='w')
        
        if viewed_at:
            Label(frame,
                  text=f"📅 Viewed: {viewed_at}",
                  font=('Arial', 9),
                  bg='white',
                  fg='#7F8C8D',
                  anchor='w').pack(anchor='w', pady=(2, 0))
        
        # تمرير history_window كمعلمة
        Button(frame,
               text="👁️ View Recipe",
               font=('Arial', 9),
               bg='#3498DB',
               fg='white',
               command=lambda r=recipe_data, hw=history_window: self.view_history_recipe(r, hw)).pack(anchor='e', pady=(5, 0))
    
    def view_history_recipe(self, recipe_data, history_window):
        """عرض وصفة من التاريخ"""
        history_window.destroy()
        self.display_full_recipe(recipe_data)
        self.notebook.select(1)
        self.status_bar.config(text=f"Viewing from history: {recipe_data.get('title', 'Recipe')}")
    
    def clear_view_history(self, history_window):
        """مسح تاريخ المشاهدة"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all view history?"):
            try:
                self.db_manager.clear_view_history(self.user_data["user_id"])
                messagebox.showinfo("Success", "View history cleared!")
                history_window.destroy()
                self.show_view_history()  # إعادة فتح النافذة
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear history: {e}")
    
    def show_favorites(self):
        """عرض الوصفات المفضلة"""
        # إنشاء نافذة جديدة
        favorites_window = Toplevel(self.window)
        favorites_window.title("Favorite Recipes")
        favorites_window.geometry("800x600")
        favorites_window.configure(bg='#F8FAFF')
        
        Label(favorites_window,
              text="⭐ Favorite Recipes",
              font=('Arial', 16, 'bold'),
              bg='#F8FAFF',
              fg='#2C3E50').pack(pady=20)
        
        container = Frame(favorites_window, bg='#F8FAFF')
        container.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        
        # الحصول على المفضلة
        favorites = self.db_manager.get_favorites(self.user_data["user_id"])
        
        if not favorites:
            Label(container,
                  text="No favorite recipes yet.",
                  font=('Arial', 12),
                  bg='#F8FAFF',
                  fg='#7F8C8D').pack(pady=50)
        else:
            # Canvas للمفضلة
            fav_canvas = Canvas(container, bg='#F8FAFF', highlightthickness=0)
            scrollbar = Scrollbar(container, orient="vertical", command=fav_canvas.yview)
            fav_frame = Frame(fav_canvas, bg='#F8FAFF')
            
            fav_frame.bind(
                "<Configure>",
                lambda e: fav_canvas.configure(scrollregion=fav_canvas.bbox("all"))
            )
            
            fav_canvas.create_window((0, 0), window=fav_frame, anchor="nw")
            fav_canvas.configure(yscrollcommand=scrollbar.set)
            
            fav_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # عرض كل وصفة مفضلة
            for fav in favorites:
                self.create_favorite_item(fav_frame, fav, favorites_window)
        
        Button(favorites_window,
               text="✕ Close",
               font=('Arial', 10),
               bg='#7F8C8D',
               fg='white',
               command=favorites_window.destroy).pack(pady=10)
    
    def create_favorite_item(self, parent_frame, favorite, favorites_window):
        """إنشاء عنصر في المفضلة"""
        frame = Frame(parent_frame,
                     bg='white',
                     relief=GROOVE,
                     borderwidth=1,
                     padx=15,
                     pady=10)
        frame.pack(fill=X, padx=5, pady=5)
        
        title = favorite.get('recipe_title', 'Unknown Recipe')
        saved_date = favorite.get('saved_date', '')
        recipe_data = favorite.get('recipe_data', {})
        
        Label(frame,
              text=title,
              font=('Arial', 12, 'bold'),
              bg='white',
              fg='#2C3E50',
              anchor='w').pack(anchor='w')
        
        if saved_date:
            Label(frame,
                  text=f"⭐ Saved: {saved_date}",
                  font=('Arial', 9),
                  bg='white',
                  fg='#F39C12',
                  anchor='w').pack(anchor='w', pady=(2, 0))
        
        if favorite.get('ingredients'):
            ingredients_text = favorite.get('ingredients')
            if len(ingredients_text) > 50:
                ingredients_text = ingredients_text[:47] + "..."
            Label(frame,
                  text=f"🔍 Search: {ingredients_text}",
                  font=('Arial', 9),
                  bg='white',
                  fg='#7F8C8D',
                  anchor='w').pack(anchor='w', pady=(2, 0))
        
        # أزرار التحكم
        btn_frame = Frame(frame, bg='white')
        btn_frame.pack(anchor='e', pady=(5, 0))
        
        Button(btn_frame,
               text="👁️ View Recipe",
               font=('Arial', 9),
               bg='#3498DB',
               fg='white',
               command=lambda r=recipe_data, fw=favorites_window: self.view_favorite_recipe(r, fw)).pack(side=LEFT, padx=2)
        
        Button(btn_frame,
               text="🗑️ Remove",
               font=('Arial', 9),
               bg='#E74C3C',
               fg='white',
               command=lambda r=recipe_data, f=frame, fw=favorites_window: self.remove_from_favorites_gui(r, f, fw)).pack(side=LEFT, padx=2)
    
    def view_favorite_recipe(self, recipe_data, favorites_window):
        """عرض وصفة من المفضلة"""
        favorites_window.destroy()
        self.display_full_recipe(recipe_data)
        self.notebook.select(1)
        self.status_bar.config(text=f"Viewing favorite: {recipe_data.get('title', 'Recipe')}")
    
    def remove_from_favorites_gui(self, recipe_data, item_frame, favorites_window):
        """إزالة وصفة من المفضلة من واجهة GUI"""
        recipe_id = recipe_data.get('id')
        if recipe_id:
            success = self.db_manager.remove_from_favorites(self.user_data["user_id"], recipe_id)
            if success:
                item_frame.destroy()
                messagebox.showinfo("Success", "Removed from favorites!")
                
                # إذا لم يعد هناك وصفات، أعد تحميل النافذة
                if not self.db_manager.get_favorites(self.user_data["user_id"]):
                    favorites_window.destroy()
                    self.show_favorites()
            else:
                messagebox.showerror("Error", "Could not remove from favorites")
    
    def load_images_in_background(self):
        """تحميل الصور في الخلفية"""
        for card_frame in self.scrollable_frame.winfo_children():
            if hasattr(card_frame, 'recipe_data'):
                recipe = card_frame.recipe_data
                recipe_id = recipe.get('id')
                
                if recipe_id not in self.image_cache:
                    thread = threading.Thread(
                        target=self.load_single_image,
                        args=(recipe, card_frame)
                    )
                    thread.daemon = True
                    thread.start()
    
    def load_single_image(self, recipe, card_frame):
        """تحميل صورة واحدة"""
        try:
            image_url = self.api_handler.get_recipe_image_url(recipe)
            if image_url:
                photo = self.api_handler.load_image_from_url(image_url, size=(100, 100))
                recipe_id = recipe.get('id')
                self.image_cache[recipe_id] = photo
                self.window.after(0, self.update_image_display, card_frame, photo)
        except Exception as e:
            print(f"Error loading image: {e}")
    
    def update_image_display(self, card_frame, photo):
        """تحديث عرض الصورة"""
        if card_frame.winfo_exists():
            for widget in card_frame.image_frame.winfo_children():
                widget.destroy()
            
            image_label = Label(card_frame.image_frame, image=photo, bg='white')
            image_label.pack(fill=BOTH, expand=True)
            self.current_images.append(photo)
    
    def create_status_bar(self):
        """إنشاء شريط الحالة"""
        self.status_bar = Label(self.window,
                               text="Ready to search recipes...",
                               bg='#5D7B9D',
                               fg='white',
                               font=('Arial', 10),
                               anchor='w',
                               padx=10)
        self.status_bar.pack(side=BOTTOM, fill=X)
    
    def logout(self):
        """تسجيل الخروج"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.window.destroy()
            self.login_window.deiconify()

if __name__ == "__main__":
    print("✅ Recipe App Module Loaded Successfully")
