# -*- coding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name' : 'Product Kit',
    'name_es': 'Kits de Productos',
    'name_ca': 'Kits de Productes',
    'version' : '2.2.0',
    'author' : 'NaN·tic',
    'email': 'info@nan-tic.com',
    'website': 'http://www.nan-tic.com/',
    'description': '''
         Adds a new tab to Product form to define product kits.
         That is a list of products that are added automatically when the
         creates a new sale, picking, etc.''',
    'description_es_ES':'''
         Añade una nueva pestaña en la ficha de producto para definir los kits,
         esta lista de productos sera añadidad automaticamente cuando se crea
         una nueva venta o albarán.''',
    'description_ca_ES':'''
         Afegeix una nova pestanya en la fitxa de producte per definir els kits,
         aquesta serà afegida autmaticament quan es crea una vento o albarà.''',
    'depends' : [
        'product',
    ],
    'xml' : [
        'product.xml',
    ],
    'translation': [
        'locale/es_ES.po',
        'locale/ca_ES.po',
    ]
}


