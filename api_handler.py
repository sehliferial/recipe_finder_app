import requests
from typing import List, Dict, Optional, Any
from PIL import Image, ImageTk
import io
import urllib.request
import urllib.error
import json
import re

class RecipeAPIHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.spoonacular.com"
        
    def validate_api_key(self) -> bool:
        """التحقق من صحة مفتاح API"""
        url = f"{self.base_url}/recipes/complexSearch"
        params = {"apiKey": self.api_key, "number": 1}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
            
    def fetch_recipes_by_ingredients(self, ingredients: str, number: int = 10) -> List[Dict]:
        """جلب وصفات بناءً على المكونات"""
        url = f"{self.base_url}/recipes/findByIngredients"
        params = {
            "ingredients": ingredients,
            "number": number,
            "apiKey": self.api_key,
            "ranking": 2,
            "ignorePantry": False
        }
    
          # جلب تفاصيل كاملة لكل وصفة
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            recipes = response.json()
            
            detailed_recipes = []
            for recipe in recipes[:5]:  # نحدد 5 وصفات فقط لتجنب طلبات كثيرة
                recipe_id = recipe.get('id')
                if recipe_id:
                    full_details = self.get_recipe_details(recipe_id)
                    if full_details:
                        recipe.update(full_details)  # دمج التفاصيل الكاملة
                detailed_recipes.append(recipe)
            
            return detailed_recipes
        except Exception as e:
            print(f"API Error: {e}")
            return []
            
            """الحصول على تفاصيل كاملة للوصفة""" 
    def get_recipe_details(self, recipe_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/recipes/{recipe_id}/information"
        params = {
            "apiKey": self.api_key,
            "includeNutrition": True
        }
        #   تنسيق بيانات الوصفة     
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # تنسيق البيانات للاستخدام في التطبيق
            formatted_data = {
                'id': data.get('id'),
                'title': data.get('title', 'No Title'),
                'image': data.get('image', ''),
                'summary': self._clean_html(data.get('summary', '')),
                'instructions': self._clean_html(data.get('instructions', '')),
                'readyInMinutes': data.get('readyInMinutes', 0),
                'servings': data.get('servings', 0),
                'sourceUrl': data.get('sourceUrl', ''),
                'spoonacularSourceUrl': data.get('spoonacularSourceUrl', ''),
                'healthScore': data.get('healthScore', 0),
                'pricePerServing': data.get('pricePerServing', 0),
                'diets': data.get('diets', []),
                'dishTypes': data.get('dishTypes', []),
                'cuisines': data.get('cuisines', []),
                'extendedIngredients': self._format_ingredients(data.get('extendedIngredients', [])),
                'analyzedInstructions': self._format_instructions(data.get('analyzedInstructions', [])),
                'full_details': json.dumps(data)  # حفظ التفاصيل الكاملة كـ JSON
            }
            
            return formatted_data
            
        except Exception as e:
            print(f"Error fetching recipe details {recipe_id}: {e}")
            return {}
        
        """تنظيف النص من HTML tags"""    
    def _clean_html(self, html_text: str) -> str:
        if not html_text:
            return ""
        
        # إزالة tags HTML
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_text)
        
        # استبدال HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        return text.strip()
    
    def _format_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        """تنسيق المكونات"""
        formatted = []
        for ing in ingredients:
            formatted.append({
                'id': ing.get('id'),
                'name': ing.get('name', ''),
                'original': ing.get('original', ''),
                'amount': ing.get('amount', 0),
                'unit': ing.get('unit', ''),
                'measures': ing.get('measures', {})
            })
        return formatted
    
    def _format_instructions(self, instructions: List[Dict]) -> List[Dict]:
        """تنسيق الخطوات"""
        formatted = []
        for section in instructions:
            steps = []
            for step in section.get('steps', []):
                steps.append({
                    'number': step.get('number', 0),
                    'step': step.get('step', ''),
                    'ingredients': step.get('ingredients', []),
                    'equipment': step.get('equipment', [])
                })
            formatted.append({
                'name': section.get('name', 'Instructions'),
                'steps': steps
            })
        return formatted
        
    def format_recipe_display(self, recipe: Dict) -> str:
        """تنسيق عرض الوصفة"""
        title = recipe.get('title', 'No Title')
        used_count = recipe.get('usedIngredientCount', 0)
        missed_count = recipe.get('missedIngredientCount', 0)
        
        return f"• {title} (✓ {used_count} | ✗ {missed_count})"
        
    def load_image_from_url(self, url: str, size: tuple = (100, 100)):
        """تحميل صورة من رابط"""
        try:
            # تحقق إذا كان الرابط موجوداً
            if not url or "spoonacular" not in url:
                return self.create_default_image(size)
                
            # إضافة headers لتجنب بعض الأخطاء
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                image_data = response.read()
            
            image = Image.open(io.BytesIO(image_data))
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
            
        except urllib.error.HTTPError as e:
            # خطأ HTTP (مثل 404)
            if e.code == 404:
                print(f"Image not found (404): {url}")
            else:
                print(f"HTTP Error {e.code} for image: {url}")
            return self.create_default_image(size)
            
        except urllib.error.URLError as e:
            # خطأ في URL
            print(f"URL Error for image {url}: {e.reason}")
            return self.create_default_image(size)
            
        except Exception as e:
            # أي خطأ آخر
            print(f"Error loading image from {url}: {str(e)}")
            return self.create_default_image(size)
            
    def create_default_image(self, size: tuple = (100, 100)):
        """إنشاء صورة افتراضية"""
        # إنشاء صورة جديدة باللون الرمادي
        image = Image.new('RGB', size, color='#F0F0F0')
        
        # لرسم نص على الصورة
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(image)
        
        # كتابة نص على الصورة
        try:
            # محاولة استخدام خط أكبر
            font_size = min(size) // 8
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # إذا فشل، استخدم الخط الافتراضي
            font = ImageFont.load_default()
        
        text = "No Image"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # حساب الموقع المركزي
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill='#666666', font=font)
        return ImageTk.PhotoImage(image)
        
    def get_recipe_image_url(self, recipe: Dict) -> str:
        """الحصول على رابط صورة الوصفة"""
        # محاولة الحصول على الصورة من مصادر مختلفة
        image = recipe.get('image')
        if image:
            # بعض الصور تأتي كاملة، بعضها جزئية
            if image.startswith('http'):
                return image
            else:
                return f"https://spoonacular.com/recipeImages/{image}"
        
        return ""

# دالة اختبارية
def test_image_loading():
    """اختبار تحميل الصور"""
    print("Testing image loading...")
    
    # إنشاء كائن اختبار
    handler = RecipeAPIHandler("test_key")
    
    # اختبار إنشاء صورة افتراضية
    default_img = handler.create_default_image((100, 100))
    print("✅ Default image created")
    
    # اختبار تحميل صورة غير موجودة
    fake_url = "https://spoonacular.com/recipeImages/nonexistent.jpg"
    result = handler.load_image_from_url(fake_url, (100, 100))
    print("✅ Handled non-existent image gracefully")
    
    return True

if __name__ == "__main__":
    test_image_loading()
    print("\n✅ API Handler module loaded successfully")
