# -*- coding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name' : 'Product Kit',
    'version' : '2.3.0',
    'author' : 'NaN·tic',
    'email': 'info@nan-tic.com',
    'website': 'http://www.nan-tic.com/',
    'description': 'Adds a new tab to Product form to define product kits. '
            'That is a list of products that are added automatically when the '
            'creates a new sale, picking, etc.',
    'depends' : [
        'product',
    ],
    'xml' : [
        'product.xml',
    ],
    'translation': [
    ]
}

