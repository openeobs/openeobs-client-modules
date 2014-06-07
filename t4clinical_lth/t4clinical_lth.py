from openerp.osv import orm
import logging

_logger = logging.getLogger(__name__)


class t4_clinical_patient_observation_lth_ews(orm.Model):
    _name = 't4.clinical.patient.observation.ews'
    _inherit = 't4.clinical.patient.observation.ews'

    _POLICY = {'ranges': [0, 4, 6], 'case': '0123', 'frequencies': [720, 240, 120, 60],
               'notifications': [
                   {'nurse': [], 'assessment': False, 'frequency': False},
                   {'nurse': [], 'assessment': True, 'frequency': False},
                   {'nurse': ['Urgently inform medical team'], 'assessment': False, 'frequency': False},
                   {'nurse': ['Immediately inform medical team'], 'assessment': False, 'frequency': False}
               ],
               'risk': ['None', 'Low', 'Medium', 'High']}