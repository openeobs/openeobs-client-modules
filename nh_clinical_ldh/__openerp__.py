# -*- encoding: utf-8 -*-
{
    'name': 'NH Clinical LDH Configuration',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """    """,
    'author': 'Neova Health',
    'website': 'http://www.neovahealth.co.uk/',
    'depends': ['nh_clinical_ui'],
    'data': ['security/ir.model.access.csv',
             'ldh_master_data.xml',
             'nh_clinical_ldh_view.xml'],
    'qweb': ['static/src/xml/nh_clinical_ldh.xml'],
    'application': True,
    'installable': True,
    'active': False,
}