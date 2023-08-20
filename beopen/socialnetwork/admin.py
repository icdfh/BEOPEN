from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_display_links = ('title',)  # Добавьте это, чтобы сделать заголовок ссылкой

    # Добавьте это, чтобы отобразить поле изображения в админ-панели
    list_display += ('image_thumbnail',)
    readonly_fields = ('image_thumbnail',)

    def image_thumbnail(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" height="50">'
        return 'No Image'

    image_thumbnail.short_description = 'Thumbnail'
    image_thumbnail.allow_tags = True