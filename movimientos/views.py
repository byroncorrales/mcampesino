# -*- coding: utf-8 -*-
# Create your views here.
from django.utils import simplejson as json
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from mercados.models import *
from lugar.models import *
from productos.models import *
from .models import Movimiento, MovimientoProductosFresco, MovimientoProductosProcesados
from .forms import *
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
import thread
from correos.models import Correos

#salidas

def reqdata(request):
	mensaje = ''
	if request.is_ajax() and request.method == 'POST':
		productosfrescos = ActividadMercado.objects.filter(fkmercado__id=request.POST['mercado']).order_by('-id')[0]
		productosprocedados = ActividadMercado.objects.filter(fkmercado__id=request.POST['mercado']).order_by('-id')[0]

		prod1 = {x.id:x.nombre for x in productosfrescos.productos_frescos.all()}
		prod2 = {x.id:x.nombre for x in productosprocedados.productos_procesados.all()}
		uni1 = {x.id:x.unidad for x in productosfrescos.productos_frescos.all()}
		uni2 = {x.id:x.unidad for x in productosprocedados.productos_procesados.all()}
		
		mensaje = json.dumps(dict(productos=prod1,procesado=prod2,unidadf=uni1,unidadp=uni2))
	return HttpResponse(mensaje)

def multipleform(request):
	MovimientoForm.base_fields['nombre_mercado'] = forms.ModelChoiceField(widget=forms.Select, queryset=RegistroMercado.objects.filter(usuario=request.user))
	if request.method == 'POST':
		formMer = MovimientoForm(request.POST)
		if formMer.is_valid():
			form_uncommited = formMer.save(commit=False)
			form_uncommited.usuario = request.user
			form_uncommited.save()
			for prod in ProductosFrescos.objects.all():
				producto = request.POST.get('product-'+str(prod.id), None)
				volumen = request.POST.get('volumen-'+str(prod.id), None)
				promedio = request.POST.get('promedio-'+str(prod.id), None)
				municipal = request.POST.get('municipal-'+str(prod.id), None)
				calidad = request.POST.get('calidad-'+str(prod.id), None)
				if producto and volumen and promedio and municipal and calidad: 
					mov = MovimientoProductosFresco.objects.create(
	                    fkmovimiento=form_uncommited,
	                    producto_fresco = ProductosFrescos.objects.get(pk=prod.id),
	                    volumen_venta_global = volumen,
	                    precio_promedio = promedio,
	                    precio_municipal = municipal,
	                    calidad = calidad
	                )
					mov.save()
			for prod in ProductosProcesados.objects.all():
				productop = request.POST.get('productp-'+str(prod.id), None)
				volumenp = request.POST.get('volumenp-'+str(prod.id), None)
				promediop = request.POST.get('promediop-'+str(prod.id), None)
				municipalp = request.POST.get('municipalp-'+str(prod.id), None)
				calidadp = request.POST.get('calidadp-'+str(prod.id), None)
				if productop and volumenp and promediop and municipalp and calidadp: 
					movp = MovimientoProductosProcesados.objects.create(
	                    fkmovimiento=form_uncommited,
	                    fkproducto_fresco = ProductosProcesados.objects.get(pk=prod.id),
	                    volumen_venta_global = volumenp,
	                    precio_promedio = promediop,
	                    precio_municipal = municipalp,
	                    calidad = calidadp
	                )
					movp.save()
	else:
		formMer = MovimientoForm()
	
		
	return render_to_response('test.html', {'formMer':formMer},
							  context_instance=RequestContext(request))


def index(request):
	mercados = RegistroMercado.objects.all()
	return render_to_response('index.html', {'mercados':mercados},
		                       context_instance=RequestContext(request))

def ver_mercado(request,id):
	mercado = get_object_or_404(RegistroMercado, id=id)

	lista1 = {}
	for mer in mercado.actividadmercado_set.all():
		lista1 = [(x.id,x.nombre,x.picture) for x in mer.productos_frescos.all()]

	lista2 = {}
	for mer in mercado.actividadmercado_set.all():
		lista2 = [(x.id,x.nombre,x.picture) for x in mer.productos_procesados.all()]

	return render_to_response('mercado.html', {'mercado':mercado,
							  'lista1':lista1,'lista2':lista2},
		                      context_instance=RequestContext(request))

def _queryset_filtrado(request):
	params = {}
	if 'tipo_organizacion_mercado' in request.session:
		params['tipo_organizacion_mercado'] = request.session['tipo_organizacion_mercado']
	if 'periodicidad' in request.session:
		params['periodicidad'] = request.session['periodicidad']
	if 'productos_procesados' in request.session:
		params['productos_procesados'] = request.session['productos_procesados']
	if 'productos_frescos' in request.session:
		params['productos_frescos'] = request.session['productos_frescos']

	unvalid_keys = []
	for key in params:
		if not params[key]:
			unvalid_keys.append(key)
    
	for key in unvalid_keys:
		del params[key]
    
	return ActividadMercado.objects.filter(**params)

def explorar(request):
	if request.method == 'POST':
		form = ActividadForm(request.POST)
		if form.is_valid():
			request.session['tipo_organizacion_mercado'] = form.cleaned_data['tipo_organizacion_mercado']            
			request.session['periodicidad'] = form.cleaned_data['periodicidad']
			request.session['productos_procesados'] = form.cleaned_data['productos_procesados']
			request.session['productos_frescos'] = form.cleaned_data['productos_frescos']
			request.session['bandera'] = 1
	else:
		form = ActividadForm()
		request.session['bandera'] = 0
	lista = []
	if request.session['bandera'] == 1:
		con = _queryset_filtrado(request)
	else:
		request.session['tipo_organizacion_mercado'] = None          
		request.session['periodicidad'] = None 
		request.session['productos_procesados'] = None
		request.session['productos_frescos'] = None  
		con = ActividadMercado.objects.all()
	for obj in con:
		lista.append([obj.tipo_organizacion_mercado,
			          obj.periodicidad,
			          obj.productos_procesados,
			          obj.productos_frescos,
			          obj.id
			        ]) 
	return render_to_response('explora.html', {'form':form,'lista':lista},
		                      context_instance=RequestContext(request))

def mapa_mercado(request):
	if request.method == 'POST':
		form = ActividadForm(request.POST)
		if form.is_valid():
			request.session['tipo_organizacion_mercado'] = form.cleaned_data['tipo_organizacion_mercado']            
			request.session['periodicidad'] = form.cleaned_data['periodicidad']
			request.session['productos_procesados'] = form.cleaned_data['productos_procesados']
			request.session['productos_frescos'] = form.cleaned_data['productos_frescos']
			request.session['bandera'] = 1
	else:
		form = ActividadForm()
		request.session['bandera'] = 0
	lista = []
	if request.session['bandera'] == 1:
		con = _queryset_filtrado(request)
	else:
		request.session['tipo_organizacion_mercado'] = None          
		request.session['periodicidad'] = None 
		request.session['productos_procesados'] = None
		request.session['productos_frescos'] = None  
		con = ActividadMercado.objects.all()
	for obj in con:
		lista.append([obj.tipo_organizacion_mercado,
			          obj.periodicidad,
			          obj.productos_procesados,
			          obj.productos_frescos,
			          obj.id
			        ])
	dpto = RegistroMercado.objects.all()
	
	return render_to_response('explorare.html', locals(), 
		                       context_instance=RequestContext(request))

def mapa_completo(request):
    if request.is_ajax():
        lista = []
        params = []
        if request.session['bandera'] == 1:
        	params = _queryset_filtrado(request)
        else:
        	params = ActividadMercado.objects.all()

        for objeto in params:
            dicc = dict(nombre=objeto.fkmercado.nombre_mercado, 
                	    id=objeto.id,
                	    idm = float(objeto.fkmercado.id),
                        lon=float(objeto.fkmercado.municipio.longitud) , 
                        lat=float(objeto.fkmercado.municipio.latitud),
                        periodicidad=objeto.periodicidad.nombre,
                        modalidad=objeto.get_modalidad_display(),
                        )
            lista.append(dicc)

        serializado = json.dumps(lista)
    	return HttpResponse(serializado, mimetype='application/json')


def obtener_mapa(request):
    if request.is_ajax():
        lista = []
        consulta = _queryset_filtrado(request)
        params = []
        if request.session['bandera'] == 1:
        	params = consulta.filter(fkmercado__departamento__id=request.POST['depart'])
        else:
        	params = ActividadMercado.objects.filter(fkmercado__departamento__id=request.POST['depart'])
        for objeto in params:
            dicc = dict(nombre=objeto.fkmercado.nombre_mercado, 
                	    id=objeto.id,
                	    idm = float(objeto.fkmercado.id),
                        lon=float(objeto.fkmercado.municipio.longitud) , 
                        lat=float(objeto.fkmercado.municipio.latitud),
                        periodicidad=objeto.periodicidad.nombre,
                        modalidad=objeto.get_modalidad_display(),
                        )
            lista.append(dicc)

        serializado = json.dumps(lista)
    	return HttpResponse(serializado, mimetype='application/json')

def test_mapa(request):

    muni = Municipio.objects.all()[0:55]
    context = {
               'muni': muni,
              }
    template = get_template('mapa.json')
    response = template.render(Context(context))
    return HttpResponse(response, mimetype="application/json")

def mandar_info_producto(request):
	mensaje = ''

	if request.is_ajax() and request.method == 'POST':
		datos = MovimientoProductosFresco.objects.filter(producto_fresco__id=request.POST['nombre'],
			                                             fkmovimiento__nombre_mercado__id=request.POST['mercado']).order_by('fkmovimiento__fecha')
	lista1 = []
	lista2 = []
	listafecha = []
	nombre = []
	medida = []
	listaVolumen = []
	for x in datos:
		lista1.append(x.precio_promedio)
		lista2.append(x.precio_municipal)
		nombre.append(x.fkmovimiento.nombre_mercado.nombre_mercado)
		medida.append(x.producto_fresco.unidad)
		listaVolumen.append(x.volumen_venta_global)
		if x.fkmovimiento.fecha.month == 1:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Ene-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 2:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Feb-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 3:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Mar-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 4:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Abr-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 5:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-May-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 6:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Jun-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 7:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Jul-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 8:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Agos-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 9:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Sep-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 10:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Oct-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 11:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Nov-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 12:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Dic-"+str(x.fkmovimiento.fecha.year))

	mensaje = json.dumps(dict(fresco=lista1,fresco2=lista2,
		                      listaf=listafecha,nombre=list(set(nombre)),
		                      medida=list(set(medida)), volum=listaVolumen))
	return HttpResponse(mensaje, mimetype='application/json')

def mandar_info_procesado(request):
	mensaje = ''

	if request.is_ajax() and request.method == 'POST':
		datos = MovimientoProductosProcesados.objects.filter(fkproducto_fresco__id=request.POST['nombre'],
			                                                 fkmovimiento__nombre_mercado__id=request.POST['mercado']).order_by('fkmovimiento__fecha')
	lista1 = []
	lista2 = []
	listafecha = []
	nombre = []
	medida = []
	listaVolumen = []
	for x in datos:
		lista1.append(x.precio_promedio)
		lista2.append(x.precio_municipal)
		nombre.append(x.fkmovimiento.nombre_mercado.nombre_mercado)
		medida.append(x.fkproducto_fresco.unidad)
		listaVolumen.append(x.volumen_venta_global)
		if x.fkmovimiento.fecha.month == 1:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Ene-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 2:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Feb-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 3:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Mar-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 4:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Abr-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 5:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-May-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 6:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Jun-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 7:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Jul-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 8:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Agos-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 9:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Sep-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 10:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Oct-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 11:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Nov-"+str(x.fkmovimiento.fecha.year))
		elif x.fkmovimiento.fecha.month == 12:
			listafecha.append(str(x.fkmovimiento.fecha.day)+"-Dic-"+str(x.fkmovimiento.fecha.year))

	mensaje = json.dumps(dict(fresco=lista1,fresco2=lista2,
		                      listaf=listafecha,nombre=list(set(nombre)),
		                      medida=list(set(medida)), volum=listaVolumen))
	return HttpResponse(mensaje, mimetype='application/json')

def posicion_mapa(request):
	lista = [] 
	for objeto in ActividadMercado.objects.filter(fkmercado__departamento__id=request.POST['depart']):	
		dicc = dict( 
			lon=float(objeto.fkmercado.municipio.longitud) , 
			lat=float(objeto.fkmercado.municipio.latitud),
		)
		lista.append(dicc)
	serializado = json.dumps(lista)
	return HttpResponse(serializado, mimetype='application/json')	

def lista_mercados(request):
	mercados = RegistroMercado.objects.all().order_by('departamento')
	departamentos = Departamento.objects.all()
	return render_to_response('lista_mercados.html', locals(), 
		                       context_instance=RequestContext(request))

def enviar_correo(algo):
	'''
		funcion para mandar correos notificando que hay usuario nuevo registrado
	'''
	users = [obj.correo for obj in Correos.objects.all()]
	contenido = render_to_string('mercado/notificar.html', 
		                         {'algo': algo})
	msg = EmailMultiAlternatives('Registro nuevo Mercado Campesino', contenido, 'simas.nicaragua@gmail.com', users)
	msg.attach_alternative(contenido, "text/html")
	msg.send()
	

def registrar(request):
	if request.method == 'POST':
		form = UserCreateForm(request.POST)
		if form.is_valid():
			uncommit = form.save(commit=False)
			uncommit.save()
			thread.start_new_thread(enviar_correo, (uncommit,))
			return HttpResponseRedirect('/')
	else:
		form = UserCreateForm()

	return render_to_response('registration/register.html',{'form':form},
		                       context_instance=RequestContext(request))

