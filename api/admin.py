from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Directors)
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Favorite)
admin.site.register(PageInfo)
# Register your models here.
