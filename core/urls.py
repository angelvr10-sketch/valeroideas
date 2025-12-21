"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from inventario import views

urlpatterns = [
    path('admin/', admin.site.urls),
     path('recibir/', views.recibir_manifiesto, name='recibir_manifiesto'),
     path('eliminar-entrada/<int:entrada_id>/', views.eliminar_entrada, name='eliminar_entrada'),
     path('pdf-manifiesto/<int:manifiesto_id>/', views.generar_pdf_manifiesto, name='pdf_manifiesto'),
     path('cerrar-manifiesto/<int:manifiesto_id>/', views.cerrar_manifiesto, name='cerrar_manifiesto'),
     path('salidas/', views.registrar_salida, name='registrar_salida'),
path('requisicion/', views.modulo_requisicion, name='modulo_requisicion'),
path('cerrar-requisicion/<int:req_id>/', views.cerrar_requisicion, name='cerrar_requisicion'),
path('pdf-requisicion/<int:req_id>/', views.pdf_requisicion, name='pdf_requisicion'),
path('maestro/', views.inventario_maestro, name='inventario_maestro'),
path('', views.dashboard, name='dashboard'),

]
