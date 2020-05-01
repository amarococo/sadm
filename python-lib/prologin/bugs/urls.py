from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from prologin.djangoconf import set_admin_title

set_admin_title(admin, "Bugs Server")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('helpdesk/', include('helpdesk.urls', namespace='helpdesk')),
]

urlpatterns += staticfiles_urlpatterns()
