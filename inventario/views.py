from django.shortcuts import render, redirect, get_object_or_404
from .models import Manifiesto, ProductoInventario, ProductoCatalogo, Categoria
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from .models import Salida, Requisicion, ItemRequisicion
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum, Count
from django.utils import timezone
from .models import ProductoCatalogo, Requisicion, Salida
from django.contrib import messages


@csrf_protect
def recibir_manifiesto(request):
    folio = request.GET.get('folio')
    manifiesto = None
    entradas = []
    catalogo = ProductoCatalogo.objects.all()
    total_manifiesto = 0

    if folio:
        # Buscamos o creamos el manifiesto
        manifiesto, created = Manifiesto.objects.get_or_create(folio=folio)
        if request.method == 'POST' and not manifiesto.cerrado:
        # Si el usuario envió el formulario para agregar un producto
         if request.method == 'POST':
            prod_id = request.POST.get('producto_id')
            cantidad = request.POST.get('cantidad')
            precio = request.POST.get('precio')
            caducidad = request.POST.get('caducidad')
            
            if prod_id and cantidad and precio:
                ProductoInventario.objects.create(
                    catalogo_id=prod_id,
                    manifiesto=manifiesto,
                    unidades=cantidad,
                    precio_compra=precio,
                    fecha_caducidad=caducidad
                )
                # Recargamos la página con el mismo folio para ver el cambio
                return redirect(f'/recibir/?folio={folio}')

        # Obtenemos las entradas y calculamos el total
        entradas = ProductoInventario.objects.filter(manifiesto=manifiesto)
        total_manifiesto = sum(item.unidades * item.precio_compra for item in entradas)

    # --- ESTE RETURN ES EL MÁS IMPORTANTE ---
    # Debe estar fuera de todos los IF para que siempre devuelva la página
    return render(request, 'inventario/recibir.html', {
        'manifiesto': manifiesto,
        'entradas': entradas,
        'catalogo': catalogo,
        'folio': folio,
        'total_manifiesto': total_manifiesto
    })
def eliminar_entrada(request, entrada_id):
    # Buscamos la entrada que se quiere borrar
    entrada = get_object_or_404(ProductoInventario, id=entrada_id)
    folio = entrada.manifiesto.folio # Guardamos el folio para regresar a la misma página
    entrada.delete() # Borramos el registro
    return redirect(f'/recibir/?folio={folio}')
def cerrar_manifiesto(request, manifiesto_id):
    manifiesto = get_object_or_404(Manifiesto, id=manifiesto_id)
    manifiesto.cerrado = True
    manifiesto.save()
    # Redirige a la función que genera el PDF que creamos antes
    return redirect('pdf_manifiesto', manifiesto_id=manifiesto.id)
    
def generar_pdf_manifiesto(request, manifiesto_id):
    manifiesto = get_object_or_404(Manifiesto, id=manifiesto_id)
    entradas = ProductoInventario.objects.filter(manifiesto=manifiesto)
    
    # Crear la respuesta del navegador
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Manifiesto_{manifiesto.folio}.pdf"'

    # Crear el PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título y Folio
    elements.append(Paragraph(f"Reporte de Recepción - Folio: {manifiesto.folio}", styles['Title']))
    elements.append(Paragraph(f"Fecha de llegada: {manifiesto.fecha_llegada.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Tabla de productos
    data = [['Producto', 'Cantidad', 'Precio U.', 'Subtotal', 'Caducidad']]
    total_general = 0
    for e in entradas:
        data.append([
            e.catalogo.nombre, 
            str(e.unidades), 
            f"${e.precio_compra}", 
            f"${e.subtotal()}", 
            e.fecha_caducidad.strftime('%d/%m/%Y')
        ])
        total_general += e.subtotal()

    data.append(['', '', 'TOTAL:', f"${total_general}", ''])

    # Estilo de la tabla
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(t)

    doc.build(elements)
    return response
    # inventario/views.py


def registrar_salida(request):
    salidas = Salida.objects.all().order_by('-fecha_salida')[:10]
    catalogo = ProductoCatalogo.objects.all()

    if request.method == 'POST':
        prod_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad'))
        motivo = request.POST.get('motivo')

        producto = get_object_or_404(ProductoCatalogo, id=prod_id)
        
        # VALIDACIÓN DE STOCK
        if cantidad > producto.stock_real():
            messages.error(request, f"Error: Solo hay {producto.stock_real()} unidades de {producto.nombre} disponibles.")
        else:
            Salida.objects.create(
                catalogo=producto,
                cantidad=cantidad,
                motivo=motivo
            )
            messages.success(request, "Salida registrada correctamente.")
            return redirect('registrar_salida')

    return render(request, 'inventario/salidas.html', {'salidas': salidas, 'catalogo': catalogo})

def modulo_requisicion(request):
    folio = request.GET.get('folio')
    requisicion = None
    items = []
    catalogo = ProductoCatalogo.objects.all()

    if folio:
        # Buscamos o creamos la requisición por folio
        requisicion, _ = Requisicion.objects.get_or_create(folio=folio)
        
        if request.method == 'POST' and not requisicion.cerrada:
            prod_id = request.POST.get('producto_id')
            cant = request.POST.get('cantidad')
            solicitante = request.POST.get('solicitante')
            
            # Guardamos el nombre del solicitante si se envía
            if solicitante:
                requisicion.solicitante = solicitante
                requisicion.save()

            if prod_id and cant:
                producto = get_object_or_404(ProductoCatalogo, id=prod_id)
            try:
             cant = int(request.POST.get('cantidad'))
            except (ValueError, TypeError):
             cant = 0  # En caso de que el campo llegue vacío o con letras
    # VALIDACIÓN DE STOCK
            if cant > producto.stock_real():
             messages.error(request, f"No puedes agregar {cant} unidades. Stock actual: {producto.stock_real()}")
            else:
             ItemRequisicion.objects.create(
             requisicion=requisicion,
             catalogo=producto,
             cantidad=cant
        )
             messages.success(request, "Producto añadido.")
    
            return redirect(f'/requisicion/?folio={folio}')
        items = requisicion.items.all()

    return render(request, 'inventario/requisicion.html', {
        'requisicion': requisicion,
        'items': items,
        'catalogo': catalogo,
        'folio': folio
    })

def cerrar_requisicion(request, req_id):
    requisicion = get_object_or_404(Requisicion, id=req_id)
    
    if not requisicion.cerrada:
        requisicion.cerrada = True
        requisicion.save()
        
        # ESTE ES EL BLOQUE QUE DESCUENTA:
        # Por cada item en la nota, creamos un registro de Salida
        for item in requisicion.items.all():
            Salida.objects.create(
                catalogo=item.catalogo,
                cantidad=item.cantidad,
                motivo='VENTA' # O el motivo que prefieras
            )
    
    return redirect('pdf_requisicion', req_id=requisicion.id)
def pdf_requisicion(request, req_id):
    req = get_object_or_404(Requisicion, id=req_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Requisicion_{req.folio}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"NOTA DE REQUISICIÓN: {req.folio}", styles['Title']))
    elements.append(Paragraph(f"Solicitante: {req.solicitante}", styles['Normal']))
    elements.append(Paragraph(f"Fecha: {req.fecha_creacion.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    data = [['Producto', 'Cantidad']]
    for item in req.items.all():
        data.append([item.catalogo.nombre, str(item.cantidad)])

    t = Table(data, colWidths=[300, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ]))
    elements.append(t)
    doc.build(elements)
    return response
    
def inventario_maestro(request):
    productos = ProductoCatalogo.objects.all()
    # Calculamos el valor total de la bodega (opcional)
    valor_bodega = sum(p.stock_real() * 10 for p in productos) # Ajustar según tu lógica de costo
    
    return render(request, 'inventario/maestro.html', {
        'productos': productos,
        'valor_bodega': valor_bodega
    })
def dashboard(request):
    # 1. Estadísticas Generales
    total_productos = ProductoCatalogo.objects.count()
    total_stock_bajo = 0
    productos = ProductoCatalogo.objects.all()
    
    # 2. Identificar productos con stock bajo (menos de 10 unidades)
    lista_critica = []
    for p in productos:
        stock = p.stock_real()
        if stock < 10:
            total_stock_bajo += 1
            lista_critica.append({'nombre': p.nombre, 'stock': stock})

    # 3. Actividad de hoy
    hoy = timezone.now().date()
    req_hoy = Requisicion.objects.filter(fecha_creacion__date=hoy).count()
    salidas_hoy = Salida.objects.filter(fecha_salida__date=hoy).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

    return render(request, 'inventario/dashboard.html', {
        'total_productos': total_productos,
        'total_stock_bajo': total_stock_bajo,
        'req_hoy': req_hoy,
        'salidas_hoy': salidas_hoy,
        'lista_critica': lista_critica[:5], # Solo los primeros 5 para no saturar
    })


