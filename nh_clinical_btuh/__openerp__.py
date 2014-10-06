# -*- encoding: utf-8 -*-
{
    'name': 'NH Clinical BTUH Configuration',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """    """,
    'author': 'Neova Health',
    'website': 'http://www.neovahealth.co.uk/',
    'depends': ['nh_clinical_ui'],
    'data': ['btuh_master_data.xml',
             'btuh_view.xml'],
    'qweb': ['static/src/xml/nh_clinical_btuh.xml'],
    'application': True,
    'installable': True,
    'active': False,
}