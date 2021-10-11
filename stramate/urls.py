from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='social')),

    path('account/', include('apps.account.urls')),
    path('activity/', include('apps.activity.urls')),
    path('', include('apps.page.urls')),
]
