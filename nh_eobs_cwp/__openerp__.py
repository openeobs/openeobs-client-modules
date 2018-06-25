# -*- coding: utf-8 -*-
# pylint: disable=manifest-required-author, manifest-deprecated-key
{
    'name': 'CWP',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """
    CWP-specific functionality and master data.
    """,
    'author': 'BJSS',
    'website': 'http://www.liveobs.com/',
    'depends': [
        'nh_eobs_client_policy',
        'nh_eobs_mental_health',
        'therapeutic',
        'uservoice'
    ],
    'data': [
        'data/cwp_master_data.xml',
        'data/locations/hospitals.xml',
        'data/locations/wards.xml',
        'data/locations/beds.xml'
    ],
    'demo': [],
    'qweb': [],
    'css': [],
    'application': True,
    'installable': True,
    'active': False,
}
