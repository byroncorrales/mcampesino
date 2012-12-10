# -*- coding: UTF-8 -*-

from django.db import models

class Pais(models.Model):
    nombre = models.CharField(max_length=200)

    class Meta:
        verbose_name=u'Pais'
        verbose_name_plural=u'Paises'

    def __unicode__(self):
        return self.nombre

class Departamento(models.Model):
    id = models.IntegerField("Código", primary_key=True)
    fkpais = models.ForeignKey(Pais)
    nombre = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, null=True, help_text="Usado como url unica(autorellenado)")
    extension = models.DecimalField("Extension Territorials", max_digits=10, decimal_places=2, null=True)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Departamentos"

class Municipio(models.Model):
    id = models.IntegerField("Código", primary_key=True)
    departamento = models.ForeignKey(Departamento)
    nombre = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, null=True, help_text="Usado como url unica(autorellenado)")
    extension = models.DecimalField("Extension Territorial", max_digits=10, decimal_places=2, blank=True, null=True)
    latitud = models.DecimalField('Latitud', max_digits=8, decimal_places=5, blank=True, null=True)
    longitud = models.DecimalField('Longitud', max_digits=8, decimal_places=5, blank=True, null=True)

    def __unicode__(self):
        return '%s - %s' % (self.departamento.nombre, self.nombre)

    class Meta:
        verbose_name_plural = "Municipios"
        ordering = ['departamento__nombre', ]

class Comunidad(models.Model):
    municipio = models.ForeignKey(Municipio)
    nombre = models.CharField(max_length=40)

    class Meta:
        verbose_name_plural="Pueblo o Ciudad"

    def __unicode__(self):
        return self.nombre
