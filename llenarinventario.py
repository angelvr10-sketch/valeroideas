import os
import sys
import django
import random
from datetime import datetime
from django.db import transaction

# Configuración de entorno
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 
django.setup()

from inventario.models import ProductoInventario, ProductoCatalogo, Manifiesto

def llenar_stock_maestro():
    try:
        # 1. Asegurar el Manifiesto MAN-008
        manifiesto, _ = Manifiesto.objects.get_or_create(
            id=8, 
            defaults={'folio': 'MAN-008', 'cerrado': False}
        )

        # 2. Obtener TODOS los productos del catálogo
        productos_catalogo = ProductoCatalogo.objects.all()
        total_productos = productos_catalogo.count()

        if total_productos == 0:
            print("Error: El catálogo está vacío. Corre primero el script de catálogo.")
            return

        fecha_cad = datetime.strptime("31/01/2026", "%d/%m/%Y").date()
        
        print(f"Iniciando carga de stock para {total_productos} productos...")

        # Usamos una transacción para que SQLite vuele en Termux
        with transaction.atomic():
            # Borramos registros previos del manifiesto 8 para empezar limpio (opcional)
            # ProductoInventario.objects.filter(manifiesto=manifiesto).delete()

            for producto in productos_catalogo:
                # Unidades entre 1 y 50
                unidades_val = random.randint(1, 50)
                
                # Precios entre 20.00 y 50.00
                precio_val = round(random.uniform(20.00, 50.00), 2)

                ProductoInventario.objects.create(
                    manifiesto=manifiesto,
                    catalogo=producto,
                    unidades=unidades_val,
                    precio_compra=precio_val,
                    fecha_caducidad=fecha_cad
                )

        print(f"--- ÉXITO TOTAL ---")
        print(f"Se asignó stock a {total_productos} productos distintos.")
        print(f"Manifiesto: {manifiesto.folio}")
        print(f"Rango de Precios: $20.00 - $50.00")
        print(f"Fecha de Caducidad: {fecha_cad}")

    except Exception as e:
        print(f"Error durante la carga: {e}")

if __name__ == '__main__':
    llenar_stock_maestro()
