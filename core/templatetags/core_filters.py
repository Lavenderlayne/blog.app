from django import template
from urllib.parse import urlparse, parse_qs

register = template.Library()

@register.filter(name='get_embed_url')
def get_embed_url(video_url):
    """
    Конвертує будь-яке посилання YouTube ('watch?v=', 'youtu.be/', 'shorts/')
    у правильне посилання для вбудовування 'embed/'.
    Якщо посилання вже є 'embed/', воно повертається без змін.
    """
    if not video_url:
        return ""

    try:
        parsed_url = urlparse(video_url)
        video_id = None

        if parsed_url.hostname == 'youtu.be':
            # Обробка: youtu.be/VIDEO_ID
            video_id = parsed_url.path.lstrip('/')
        
        elif parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                # Обробка: /watch?v=VIDEO_ID
                query_params = parse_qs(parsed_url.query)
                video_id = query_params.get('v', [None])[0]
            
            elif parsed_url.path.startswith('/embed/'):
                # Посилання ВЖЕ у правильному форматі
                return video_url
            
            elif parsed_url.path.startswith('/shorts/'):
                # Обробка: /shorts/VIDEO_ID
                video_id = parsed_url.path.split('/shorts/')[1]
        
        if video_id:
            # Очищуємо ID від зайвих параметрів, якщо вони є
            video_id = video_id.split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
            
    except Exception:
        # Якщо парсинг не вдався
        return ""
        
    # Якщо це не розпізнане посилання YouTube
    return ""