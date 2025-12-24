from django.shortcuts import render, redirect, get_object_or_404
from .models import Manifiesto, ProductoInventario, ProductoCatalogo, Categoria, Salida, Requisicion, ItemRequisicion
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib import messages

@csrf_protect
def recibir_manifiesto(request):
    folio = request.GET.get('folio')
    manifiesto = None
    entradas = []
    total_manifiesto = 0
    catalogo = ProductoCatalogo.objects.all()

    if folio:
        manifiesto, created = Manifiesto.objects.get_or_create(folio=folio)
        if request.method == 'POST' and not manifiesto.cerrado:
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
                messages.success(request, "Producto agregado.")
                return redirect(f'/recibir/?folio={folio}')

        entradas = ProductoInventario.objects.filter(manifiesto=manifiesto).select_related('catalogo')
        total_manifiesto = sum(item.unidades * item.precio_compra for item in entradas)

    return render(request, 'inventario/recibir.html', {
        'manifiesto': manifiesto, 'entradas': entradas,
        'catalogo': catalogo, 'folio': folio, 'total_manifiesto': total_manifiesto
    })

def eliminar_entrada(request, entrada_id):
    entrada = get_object_or_404(ProductoInventario, id=entrada_id)
    folio = entrada.manifiesto.folio
    entrada.delete()
    return redirect(f'/recibir/?folio={folio}')

def cerrar_manifiesto(request, manifiesto_id):
    manifiesto = get_object_or_404(Manifiesto, id=manifiesto_id)
    manifiesto.cerrado = True
    manifiesto.save()
    return redirect(f'/recibir/?folio={manifiesto.folio}&descargar_pdf={manifiesto.id}')

def generar_pdf_manifiesto(request, manifiesto_id):
    manifiesto = get_object_or_404(Manifiesto, id=manifiesto_id)
    entradas = ProductoInventario.objects.filter(manifiesto=manifiesto).select_related('catalogo')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Manifiesto_{manifiesto.folio}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Reporte de Recepción - Folio: {manifiesto.folio}", styles['Title']))
    data = [['Producto', 'Cantidad', 'Precio U.', 'Subtotal', 'Caducidad']]
    total_general = 0
    for e in entradas:
        data.append([e.catalogo.nombre, str(e.unidades), f"${e.precio_compra}", f"${e.subtotal()}", e.fecha_caducidad.strftime('%d/%m/%Y')])
        total_general += e.subtotal()
    data.append(['', '', 'TOTAL:', f"${total_general}", ''])
    t = Table(data)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.black), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 1, colors.grey)]))
    elements.append(t)
    doc.build(elements)
    return response

def registrar_salida(request):
    salidas = Salida.objects.all().order_by('-fecha_salida')[:10].select_related('catalogo')
    catalogo = ProductoCatalogo.objects.all()
    if request.method == 'POST':
        prod_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad'))
        motivo = request.POST.get('motivo')
        producto = get_object_or_404(ProductoCatalogo, id=prod_id)
        if cantidad > producto.stock_real:
            messages.error(request, f"Error: Solo hay {producto.stock_real} disponibles.")
        else:
            Salida.objects.create(catalogo=producto, cantidad=cantidad, motivo=motivo)
            messages.success(request, "Salida registrada.")
            return redirect('registrar_salida')
    return render(request, 'inventario/salidas.html', {'salidas': salidas, 'catalogo': catalogo})

def modulo_requisicion(request):
    folio = request.GET.get('folio')
    descargar_pdf_id = request.GET.get('descargar_pdf')
    requisicion = None
    items = []
    catalogo = ProductoCatalogo.objects.all()
    if folio:
        requisicion, _ = Requisicion.objects.get_or_create(folio=folio)
        if request.method == 'POST' and not requisicion.cerrada:
            prod_id = request.POST.get('producto_id')
            cant_raw = request.POST.get('cantidad')
            solicitante = request.POST.get('solicitante')
            if solicitante:
                requisicion.solicitante = solicitante
                requisicion.save()
            if prod_id and cant_raw:
                producto = get_object_or_404(ProductoCatalogo, id=prod_id)
                cant = int(cant_raw)
                if cant > producto.stock_real:
                    messages.error(request, "Stock insuficiente.")
                else:
                    ItemRequisicion.objects.create(requisicion=requisicion, catalogo=producto, cantidad=cant)
            return redirect(f'/requisicion/?folio={folio}')
        items = requisicion.items.all().select_related('catalogo')
    return render(request, 'inventario/requisicion.html', {'requisicion': requisicion, 'items': items, 'catalogo': catalogo, 'folio': folio, 'descargar_pdf_id': descargar_pdf_id})

def cerrar_requisicion(request, req_id):
    requisicion = get_object_or_404(Requisicion, id=req_id)
    if not requisicion.cerrada:
        requisicion.cerrada = True
        requisicion.save()
        for item in requisicion.items.all():
            Salida.objects.create(catalogo=item.catalogo, cantidad=item.cantidad, motivo='VENTA')
    return redirect(f'/requisicion/?folio={requisicion.folio}&descargar_pdf={requisicion.id}')

def pdf_requisicion(request, req_id):
    req = get_object_or_404(Requisicion, id=req_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Requisicion_{req.folio}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"NOTA DE REQUISICIÓN: {req.folio}", styles['Title']))
    data = [['Producto', 'Cantidad']]
    for item in req.items.all():
        data.append([item.catalogo.nombre, str(item.cantidad)])
    t = Table(data, colWidths=[300, 100])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t)
    doc.build(elements)
    return response

def inventario_maestro(request):
    # OPTIMIZACIÓN: La base de datos calcula todo de una sola vez
    productos = ProductoCatalogo.objects.annotate(
        total_e=Coalesce(Sum('productoinventario__unidades'), 0),
        total_s=Coalesce(Sum('salida__cantidad'), 0)
    ).annotate(stock_calc=F('total_e') - F('total_s')).select_related('categoria')
    
    # Usamos stock_calc para el valor de la bodega
    valor_bodega = sum(p.stock_calc * 10 for p in productos)
    
    return render(request, 'inventario/maestro.html', {
        'productos': productos,
        'valor_bodega': valor_bodega
    })

def dashboard(request):
    hoy = timezone.now().date()
    quince_dias = hoy + timezone.timedelta(days=15)
    
    # OPTIMIZACIÓN: Traer todo el stock calculado de golpe
    productos = ProductoCatalogo.objects.annotate(
        total_e=Coalesce(Sum('productoinventario__unidades'), 0),
        total_s=Coalesce(Sum('salida__cantidad'), 0)
    ).annotate(stock_calc=F('total_e') - F('total_s'))

    total_productos = productos.count()
    valor_total = 0
    productos_criticos = 0
    lista_alertas = []

    for p in productos:
        stock = p.stock_calc # Usamos el valor ya calculado por la DB
        valor_total += (stock * 10) 
        if stock <= 5:
            productos_criticos += 1
            lista_alertas.append({'nombre': p.nombre, 'mensaje': 'Stock crítico', 'tipo': 'stock', 'valor': f'{stock} uds'})

    lotes_por_vencer = ProductoInventario.objects.filter(fecha_caducidad__range=[hoy, quince_dias]).select_related('catalogo')
    proximos_a_vencer = lotes_por_vencer.count()

    for lote in lotes_por_vencer:
        lista_alertas.append({'nombre': lote.catalogo.nombre, 'mensaje': f'Vence {lote.fecha_caducidad.strftime("%d/%m")}', 'tipo': 'vencimiento', 'valor': 'Vence pronto'})

    req_hoy = Requisicion.objects.filter(fecha_creacion__date=hoy).count()
    salidas_hoy = Salida.objects.filter(fecha_salida__date=hoy).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

    return render(request, 'inventario/dashboard.html', {
        'total_productos': total_productos,
        'productos_criticos': productos_criticos,
        'proximos_a_vencer': proximos_a_vencer,
        'valor_total': f'{valor_total:,}',
        'req_hoy': req_hoy,
        'salidas_hoy': salidas_hoy,
        'alertas_lista': lista_alertas[:6],
    })
