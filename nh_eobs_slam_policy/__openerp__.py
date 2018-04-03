# -*- coding: utf-8 -*-
# pylint: disable=manifest-required-author, manifest-deprecated-key
{
    'name': 'Open e-Obs SLAM Policy',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """
    A configuration module for South London & Maudsley NHS Foundation Trust
    """,
    'author': 'Neova Health',
    'website': 'http://www.neovahealth.co.uk/',
    'depends': [
        'shift_allocation',
        'user_management',
        'nh_eobs_mobile',
        'nh_eobs_mental_health',
        'acute',
        'nh_neurological',
        # 'nh_food_and_fluid',
        'nh_weight'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mobile_template.xml',
        'views/wardboard.xml'
    ],
    'demo': [],
    'qweb': ['static/src/xml/slam.xml'],
    'css': [],
    'application': True,
    'installable': True,
    'active': False,
}
