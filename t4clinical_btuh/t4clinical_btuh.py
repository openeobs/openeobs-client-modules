from openerp.osv import orm
from openerp.addons.t4activity.activity import except_if
from datetime import datetime as dt, timedelta as td
import bisect
from openerp import SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class t4_clinical_patient_observation_btuh_ews(orm.Model):
    _name = 't4.clinical.patient.observation.ews'
    _inherit = 't4.clinical.patient.observation.ews'

    _RR_RANGES = {'ranges': [8, 11, 20, 24], 'scores': '31023'}
    _O2_RANGES = {'ranges': [91, 93, 95], 'scores': '3210'}
    _BT_RANGES = {'ranges': [35.0, 35.999, 37.999, 38.999], 'scores': '31012'}
    _BP_RANGES = {'ranges': [79, 89, 109, 219], 'scores': '32103'}
    _PR_RANGES = {'ranges': [39, 89, 109, 129], 'scores': '30123'}
    """
    BTUH EWS policy has 4 different scenarios:
        case 0: no clinical risk
        case 1: low clinical risk
        case 2: medium clinical risk
        case 3: high clinical risk
    """
    _POLICY = {'ranges': [0, 4, 6], 'case': '0123', 'frequencies': [720, 240, 60, 30],
               'notifications': [
                   [],
                   ['Assess patient'],
                   ['Urgently inform medical team', 'Consider assessment by CCOT beep 6427'],
                   ['Immediately inform medical team', 'Urgent assessment by CCOT beep 6427']],
               'risk': ['None', 'Low', 'Medium', 'High']}

    def _get_score(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for ews in self.browse(cr, uid, ids, context):
            score = 0
            three_in_one = False

            aux = int(self._RR_RANGES['scores'][bisect.bisect_left(self._RR_RANGES['ranges'], ews.respiration_rate)])
            three_in_one = three_in_one or aux == 3
            score += aux

            aux = int(self._O2_RANGES['scores'][bisect.bisect_left(self._O2_RANGES['ranges'], ews.indirect_oxymetry_spo2)])
            three_in_one = three_in_one or aux == 3
            score += aux

            aux = int(self._BT_RANGES['scores'][bisect.bisect_left(self._BT_RANGES['ranges'], ews.body_temperature)])
            three_in_one = three_in_one or aux == 3
            score += aux

            aux = int(self._BP_RANGES['scores'][bisect.bisect_left(self._BP_RANGES['ranges'], ews.blood_pressure_systolic)])
            three_in_one = three_in_one or aux == 3
            score += aux

            aux = int(self._PR_RANGES['scores'][bisect.bisect_left(self._PR_RANGES['ranges'], ews.pulse_rate)])
            three_in_one = three_in_one or aux == 3
            score += aux

            score += 2 if ews.oxygen_administration_flag else 0

            score += 3 if ews.avpu_text in ['V', 'P', 'U'] else 0
            three_in_one = True if ews.avpu_text in ['V', 'P', 'U'] else three_in_one

            case = int(self._POLICY['case'][bisect.bisect_left(self._POLICY['ranges'], score)])
            case = 2 if three_in_one and case < 3 else case
            clinical_risk = self._POLICY['risk'][case]

            res[ews.id] = {'score': score, 'three_in_one': three_in_one, 'clinical_risk': clinical_risk}
            _logger.debug("Observation EWS activity_id=%s ews_id=%s score: %s" % (ews.activity_id.id, ews.id, res[ews.id]))
        return res

    def complete(self, cr, uid, activity_id, context=None):
        """
        Implementation of the BTUH EWS policy
        """
        activity_pool = self.pool['t4.activity']
        hca_pool = self.pool['t4.clinical.notification.hca']
        nurse_pool = self.pool['t4.clinical.notification.nurse']
        groups_pool = self.pool['res.groups']
        api_pool = self.pool['t4.clinical.api']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        case = int(self._POLICY['case'][bisect.bisect_left(self._POLICY['ranges'], activity.data_ref.score)])
        case = 2 if activity.data_ref.three_in_one and case < 3 else case
        hcagroup_ids = groups_pool.search(cr, uid, [('users', 'in', [uid]), ('name', '=', 'T4 Clinical HCA Group')])
        nursegroup_ids = groups_pool.search(cr, uid, [('users', 'in', [uid]), ('name', '=', 'T4 Clinical Nurse Group')])
        group = nursegroup_ids and 'nurse' or hcagroup_ids and 'hca' or False
        if group == 'hca':
            hca_pool.create_activity(cr,  SUPERUSER_ID, {'summary': 'Inform registered nurse', 'creator_id': activity_id}, {'patient_id': activity.data_ref.patient_id.id})
            nurse_pool.create_activity(cr, SUPERUSER_ID, {'summary': 'Informed about patient status', 'creator_id': activity_id}, {'patient_id': activity.data_ref.patient_id.id})
        if case:
            for n in self._POLICY['notifications'][case]:
                nurse_pool.create_activity(cr, SUPERUSER_ID, {'summary': n, 'creator_id': activity_id}, {'patient_id': activity.data_ref.patient_id.id})
        # create next EWS
        spell_activity_id = activity.parent_id.id
        next_activity_id = self.create_activity(cr, SUPERUSER_ID,
                             {'creator_id': activity_id, 'parent_id': spell_activity_id},
                             {'patient_id': activity.data_ref.patient_id.id})
        activity_pool.schedule(cr, SUPERUSER_ID, next_activity_id, dt.today()+td(minutes=self._POLICY['frequencies'][case]))
        activity_pool.submit(cr, SUPERUSER_ID, spell_activity_id,
                             {'ews_frequency': self._POLICY['frequencies'][case]},
                             context)
        return super(t4_clinical_patient_observation_btuh_ews, self).complete(cr, SUPERUSER_ID, activity_id, context)