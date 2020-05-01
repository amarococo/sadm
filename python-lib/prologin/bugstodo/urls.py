from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from prologin.djangoconf import set_admin_title

set_admin_title(admin, "Wiki Server")

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('', include('todo.urls', namespace='todo')),
]

urlpatterns += staticfiles_urlpatterns()
