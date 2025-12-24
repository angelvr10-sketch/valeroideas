from django.db import models
from datetime import date
from django.db.models import Sum

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nombre

# ESTE ES TU NUEVO CATÁLOGO MAESTRO
class ProductoCatalogo(models.Model):
    codigo_barras = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    def total_entradas(self):
        # Suma todas las unidades recibidas en manifiestos
        resultado = self.productoinventario_set.aggregate(Sum('unidades'))['unidades__sum']
        return resultado if resultado else 0

    def total_salidas(self):
        # Suma todas las unidades registradas como salidas o requisiciones
        resultado = self.salida_set.aggregate(Sum('cantidad'))['cantidad__sum']
        return resultado if resultado else 0

   # Ejemplo de cómo debería quedar para evitar el error
@property
def stock_real(self):
    from django.db.models import Sum
    # Sumamos entradas y salidas, usando 0 si no hay registros aún
    entradas = self.movimientos.filter(tipo='entrada').aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    salidas = self.movimientos.filter(tipo='salida').aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    return entradas - salidas

    def __str__(self):
        return self.nombre

class Manifiesto(models.Model):
    folio = models.CharField(max_length=50, unique=True)
    fecha_llegada = models.DateTimeField(auto_now_add=True)
    # Nuevo campo:
    cerrado = models.BooleanField(default=False)

    def __str__(self): 
        return f"{self.folio} ({'Cerrado' if self.cerrado else 'Abierto'})"

class ProductoInventario(models.Model):
    # Ahora el producto se elige del catálogo
    catalogo = models.ForeignKey(ProductoCatalogo, on_delete=models.CASCADE)
    manifiesto = models.ForeignKey(Manifiesto, on_delete=models.CASCADE, related_name='entradas')
    
    unidades = models.PositiveIntegerField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_caducidad = models.DateField()
    def subtotal(self):
        return self.unidades * self.precio_compra
    def dias_para_caducar(self):
        if self.fecha_caducidad:
            delta = self.fecha_caducidad - date.today()
            return delta.days
        return 999 # Si no tiene fecha, lo marcamos como lejos
    def __str__(self):
        return f"{self.catalogo.nombre} - Folio: {self.manifiesto.folio}"
       

class Salida(models.Model):
    # Relacionamos con el catálogo maestro
    catalogo = models.ForeignKey(ProductoCatalogo, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha_salida = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=100, choices=[
        ('VENTA', 'Venta'),
        ('MERMA', 'Merma/Dañado'),
        ('TRANSFERENCIA', 'Transferencia'),
    ], default='VENTA')

    def __str__(self):
        return f"{self.catalogo.nombre} - {self.cantidad} unidades"
# inventario/models.py

class Requisicion(models.Model):
    folio = models.CharField(max_length=50, unique=True)
    solicitante = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    cerrada = models.BooleanField(default=False)

    def __str__(self):
        return f"Req: {self.folio} - {self.solicitante}"

class ItemRequisicion(models.Model):
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name='items')
    catalogo = models.ForeignKey(ProductoCatalogo, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.catalogo.nombre} ({self.cantidad})"

