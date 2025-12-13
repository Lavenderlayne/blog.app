"""
Custom CKEditor 5 upload handler for Cloudinary
"""
import cloudinary
import cloudinary.uploader
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
import os


@login_required
@csrf_protect
def ckeditor_upload_image(request):
    """
    Кастомний view для завантаження зображень CKEditor у Cloudinary
    """
    if request.method == 'POST' and request.FILES.get('upload'):
        uploaded_file = request.FILES['upload']
        
        # Перевірка типу файлу
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'error': {
                    'message': f'Недозволений тип файлу. Дозволені: {", ".join(allowed_extensions)}'
                }
            }, status=400)
        
        # Перевірка розміру файлу (макс 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'error': {
                    'message': 'Файл занадто великий. Максимальний розмір: 5MB'
                }
            }, status=400)
        
        try:
            # Завантаження у Cloudinary
            result = cloudinary.uploader.upload(
                uploaded_file,
                folder='ckeditor_uploads',  # Папка в Cloudinary
                resource_type='image',
                transformation={
                    'quality': 'auto',
                    'fetch_format': 'auto'
                }
            )
            
            # Повертаємо URL у форматі, який очікує CKEditor 5
            return JsonResponse({
                'url': result['secure_url']
            })
            
        except Exception as e:
            return JsonResponse({
                'error': {
                    'message': f'Помилка завантаження: {str(e)}'
                }
            }, status=500)
    
    return JsonResponse({
        'error': {
            'message': 'Невірний запит'
        }
    }, status=400)
