from django.core.management.base import BaseCommand
from core.models import Post

class Command(BaseCommand):
    help = 'Regenerate empty slugs for posts'

    def handle(self, *args, **kwargs):
        posts = Post.objects.filter(slug='')
        self.stdout.write(f"Found {posts.count()} posts with empty slugs...")
        
        for post in posts:
            post.save()
            self.stdout.write(self.style.SUCCESS(f"Fixed: {post.slug}"))