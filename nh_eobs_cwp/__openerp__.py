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
        'nh_eobs_slam_policy'
    ],
    'data': [
        'data/locations/hospitals.xml',
        'data/locations/wards.xml',
        'data/locations/beds.xml',
        'data/users/doctors.xml',
        'data/users/senior_managers.xml',
        'data/users/shift_coordinators.xml',
        'data/users/nurses.xml',
        'data/users/hcas.xml'
    ],
    'demo': [],
    'qweb': [],
    'css': [],
    'application': True,
    'installable': True,
    'active': False,
}