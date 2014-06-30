# -*- encoding: utf-8 -*-
{
    'name': 'T4 Clinical BTUH Configuration',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """    """,
    'author': 'Tactix4',
    'website': 'http://www.tactix4.com/',
    'depends': ['t4clinical_ui'],
    'data': ['btuh_master_data.xml',
             'btuh_view.xml'],
    'qweb': ['static/src/xml/t4clinical_btuh.xml'],
    'css': ['static/src/css/t4clinical_btuh.css'],
    'application': True,
    'installable': True,
    'active': False,
}