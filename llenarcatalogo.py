import os
import sys
import django
import random

# Configuración de entorno
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 
django.setup()

from inventario.models import ProductoCatalogo, Categoria

def optimizar_catalogo():
    try:
        # 1. Asegurar Categoría Base
        cat, _ = Categoria.objects.get_or_create(id=1, defaults={'nombre': 'Abarrotes'})

        # 2. Diccionarios para generar nombres realistas
        prefijos = [
            "Aceite", "Arroz", "Frijol", "Azúcar", "Leche", "Papel Higiénico", 
            "Detergente", "Jabón", "Atún", "Café", "Harina", "Pasta", "Sal", 
            "Galletas", "Mayonesa", "Salsa", "Cereal", "Lentejas", "Cloro", "Suavizante"
        ]
        marcas = ["La Gloria", "Premium Gold", "Economax", "Sierra Madre", "Del Campo", "Sol y Mar"]
        presentaciones = ["1kg", "500g", "900ml", "1.5L", "4 piezas", "250g", "12 pack"]

        print("Generando catálogo de 200 productos...")
        
        creados = 0
        nombres_usados = set()

        while creados < 200:
            # Construir nombre único
            nom = f"{random.choice(prefijos)} {random.choice(marcas)} {random.choice(presentaciones)}"
            
            if nom not in nombres_usados:
                # Generar código de barras aleatorio de 13 dígitos
                barras = "".join([str(random.randint(0, 9)) for _ in range(13)])
                
                # update_or_create evita errores si el script se interrumpe
                ProductoCatalogo.objects.update_or_create(
                    nombre=nom,
                    defaults={
                        'codigo_barras': barras,
                        'descripcion': f"Producto de abarrotes - {nom}",
                        'categoria': cat
                    }
                )
                nombres_usados.add(nom)
                creados += 1

        print(f"--- ÉXITO ---")
        print(f"Se han optimizado y cargado {creados} productos únicos al catálogo.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    optimizar_catalogo()
