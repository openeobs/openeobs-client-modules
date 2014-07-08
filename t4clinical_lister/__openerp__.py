# -*- encoding: utf-8 -*-
{
    'name': 'T4 Clinical Lister Configuration',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """    """,
    'author': 'Tactix4',
    'website': 'http://www.tactix4.com/',
    'depends': ['t4clinical_ui'],
    'data': ['lister_master_data.xml',
             't4clinical_lister_view.xml'],
    'qweb': ['static/src/xml/t4clinical_lister.xml'],
    'css': ['static/src/css/t4clinical_lister.css'],
    'application': True,
    'installable': True,
    'active': False,
}