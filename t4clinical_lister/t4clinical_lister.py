from openerp.osv import orm
import logging

_logger = logging.getLogger(__name__)


class t4_clinical_patient_observation_lister_ews(orm.Model):
    _name = 't4.clinical.patient.observation.ews'
    _inherit = 't4.clinical.patient.observation.ews'

    _POLICY = {'ranges': [0, 4, 6], 'case': '0123', 'frequencies': [240, 240, 60, 15],
               'notifications': [
                   [],
                   [{'model': 'assessment', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}],
                   [{'model': 'medical_team', 'summary': 'Urgently inform medical team', 'groups': ['nurse', 'hca']},
                    {'model': 'frequency', 'groups': ['nurse', 'hca']},
                    {'model': 'nurse', 'summary': 'Inform CCOT if unresolved after one hour. Bleep L1663 or Q0169', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}],
                   [{'model': 'medical_team', 'summary': 'Immediately inform SPR or above', 'groups': ['nurse', 'hca']},
                    {'model': 'nurse', 'summary': 'Urgent assessment by CCOT', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}]
               ],
               'risk': ['None', 'Low', 'Medium', 'High']}