from django.contrib import admin
# Cambiamos 'Producto' por los nuevos nombres:
from .models import Categoria, Manifiesto, ProductoCatalogo, ProductoInventario
from .models import Requisicion, ItemRequisicion, Salida
from django.db.models import Sum

@admin.register(ProductoCatalogo)
class ProductoCatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'codigo_barras')
    search_fields = ('nombre', 'codigo_barras')

@admin.register(ProductoInventario)
class ProductoInventarioAdmin(admin.ModelAdmin):
    list_display = ('catalogo', 'unidades', 'precio_compra', 'manifiesto')
    list_filter = ('manifiesto', 'catalogo__categoria')

admin.site.register(Categoria)
admin.site.register(Manifiesto)
class ItemRequisicionInline(admin.TabularInline):
    model = ItemRequisicion
    extra = 0

@admin.register(Requisicion)
class RequisicionAdmin(admin.ModelAdmin):
    # Agregamos 'total_piezas' a la lista de visualización
    list_display = ('folio', 'solicitante', 'fecha_creacion', 'total_piezas', 'cerrada')
    list_filter = ('cerrada', 'fecha_creacion')
    search_fields = ('folio', 'solicitante')
    inlines = [ItemRequisicionInline]

    # Función para calcular el total de piezas en la lista
    def total_piezas(self, obj):
        resultado = obj.items.aggregate(Sum('cantidad'))['cantidad__sum']
        return resultado if resultado else 0
    
    # Le ponemos un nombre bonito a la columna
    total_piezas.short_description = 'Total Piezas'

@admin.register(Salida)
class SalidaAdmin(admin.ModelAdmin):
    list_display = ('catalogo', 'cantidad', 'motivo', 'fecha_salida')
    list_filter = ('motivo', 'fecha_salida')
    search_fields = ('catalogo__nombre',)