# -*- encoding: utf-8 -*-
{
    'name': 'T4 Clinical LDH Configuration',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """    """,
    'author': 'Tactix4',
    'website': 'http://www.tactix4.com/',
    'depends': ['t4clinical_ui'],
    'data': ['security/ir.model.access.csv',
             'ldh_master_data.xml',
             't4clinical_ldh_view.xml'],
    'qweb': ['static/src/xml/t4clinical_ldh.xml'],
    'application': True,
    'installable': True,
    'active': False,
}