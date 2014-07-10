from openerp.osv import orm, fields
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
                   [{'model': 'frequency', 'groups': ['nurse', 'hca']}],
                   [{'model': 'assessment', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}],
                   [{'model': 'medical_team', 'summary': 'Urgently inform medical team', 'groups': ['nurse', 'hca']},
                    {'model': 'frequency', 'groups': ['nurse', 'hca']},
                    {'model': 'nurse', 'summary': 'Consider assessment by CCOT beep 6427', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}],
                   [{'model': 'medical_team', 'summary': 'Immediately inform medical team', 'groups': ['nurse', 'hca']},
                    {'model': 'frequency', 'groups': ['nurse', 'hca']},
                    {'model': 'nurse', 'summary': 'Urgent assessment by CCOT beep 6427', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}]
               ],
               'risk': ['None', 'Low', 'Medium', 'High']}

    def _get_score(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for ews in self.browse(cr, uid, ids, context):
            activity_pool = self.pool['t4.activity']
            domain = [('data_model', '=', 't4.clinical.patient.o2target'), ('state', '=', 'completed')]
            o2target_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc', context=context)
            o2target = activity_pool.browse(cr, uid, o2target_ids[0], context=context) if o2target_ids else False

            score = 0
            three_in_one = False

            aux = int(self._RR_RANGES['scores'][bisect.bisect_left(self._RR_RANGES['ranges'], ews.respiration_rate)])
            three_in_one = three_in_one or aux == 3
            score += aux

            if o2target and (o2target.data_ref.level_id.min <= ews.indirect_oxymetry_spo2 <= o2target.data_ref.level_id.max):
                aux = 0
            else:
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

    _columns = {
        'score': fields.function(_get_score, type='integer', multi='score', string='Score', store={
            't4.clinical.patient.observation.ews': (lambda self, cr, uid, ids, ctx: ids, [], 10) # all fields of self
        }),
        'three_in_one': fields.function(_get_score, type='boolean', multi='score', string='3 in 1 flag', store={
            't4.clinical.patient.observation.ews': (lambda self, cr, uid, ids, ctx: ids, [], 10) # all fields of self
        }),
        'clinical_risk': fields.function(_get_score, type='char', multi='score', string='Clinical Risk', store={
            't4.clinical.patient.observation.ews': (lambda self, cr, uid, ids, ctx: ids, [], 10)
        }),
    }

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
        spell_activity_id = activity.parent_id.id
        notifications = list(self._POLICY['notifications'][case])

        # CHECK O2TARGET
        domain = [('data_model', '=', 't4.clinical.patient.o2target'), ('state', '=', 'completed')]
        o2target_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc', context=context)
        o2target = activity_pool.browse(cr, uid, o2target_ids[0], context=context) if o2target_ids else False
        if o2target:
            o2 = activity.data_ref.indirect_oxymetry_spo2
            if o2target.data_ref.level_id.min > o2 or o2 > o2target.data_ref.level_id.max:
                domain = [('parent_id', '=', spell_activity_id),
                          ('summary', '=', 'Review Oxygen Regime'),
                          ('state', 'not in', ['completed', 'cancelled'])]
                oxygen_activity_ids = activity_pool.search(cr, SUPERUSER_ID, domain, context=context)
                [activity_pool.cancel(cr, SUPERUSER_ID, id) for id in oxygen_activity_ids]
                notifications.append({'model': 'nurse', 'summary': 'Review Oxygen Regime', 'groups': ['nurse', 'hca']})

        api_pool.trigger_notifications(cr, uid, {
            'notifications': notifications,
            'parent_id': spell_activity_id,
            'creator_id': activity_id,
            'patient_id': activity.data_ref.patient_id.id,
            'model': self._name,
            'group': group
        }, context=context)

        res = self.pool['t4.clinical.patient.observation'].complete(cr, SUPERUSER_ID, activity_id, context=context)

        # cancel open EWS
        api_pool.cancel_open_activities(cr, uid, spell_activity_id, self._name, context=context)

        # create next EWS
        next_activity_id = self.create_activity(cr, SUPERUSER_ID,
                             {'creator_id': activity_id, 'parent_id': spell_activity_id},
                             {'patient_id': activity.data_ref.patient_id.id})
        api_pool.change_activity_frequency(cr, SUPERUSER_ID,
                                           activity.data_ref.patient_id.id,
                                           self._name,
                                           self._POLICY['frequencies'][case], context=context)
        return res


class t4_clinical_api_btuh(orm.AbstractModel):
    _name = 't4.clinical.api'
    _inherit = 't4.clinical.api'

    def update_bed(self, cr, uid, spell_activity_id, vals, context=None):
        if not vals:
            vals = {}
        activity_pool = self.pool['t4.activity']
        location_pool = self.pool['t4.clinical.location']
        bed_ids = location_pool.search(cr, uid, [
            ('parent_id', '=', vals['ward_id']),
            ('name', '=', vals['bed'])
        ], context=context)
        if len(bed_ids) > 1:
            _logger.warn("There is more than one bed %s in the same Ward" % vals['bed'])
        if not bed_ids:
            bed_ids = [location_pool.create(cr, uid, {
                'name': vals['bed'],
                'parent_id': vals['ward_id'],
                'type': 'poc',
                'usage': 'bed'
            })]
        bed = location_pool.browse(cr, uid, bed_ids[0], context=context)
        except_if(not bed.is_available, 'Error! The bed is already being used:%s' % vals['bed'])
        domain = [
            ('data_model', '=', 't4.clinical.patient.placement'),
            ('state', 'not in', ['completed', 'cancelled']),
            ('parent_id', '=', spell_activity_id)]
        placement_ids = activity_pool.search(cr, uid, domain, context=context)
        if placement_ids:
            activity_pool.submit(cr, uid, placement_ids[0], {'location_id': bed_ids[0]}, context=context)
            activity_pool.complete(cr, uid, placement_ids[0], context=context)
        else:
            self.create_complete(cr, SUPERUSER_ID, 't4.clinical.patient.move', {
                'parent_id': spell_activity_id,
                'creator_id': vals.get('activity_id')
            }, {
                'patient_id': vals.get('patient_id'),
                'location_id': bed_ids[0]
            }, context=context)
            activity_pool.submit(cr, SUPERUSER_ID, spell_activity_id, {'location_id': bed_ids[0]})


class t4_clinical_adt_patient_admit_btuh(orm.Model):
    _name = 't4.clinical.adt.patient.admit'
    _inherit = 't4.clinical.adt.patient.admit'

    _columns = {
        'bed': fields.char('Bed', size=50)
    }

    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        res[self._name] = super(t4_clinical_adt_patient_admit_btuh, self).complete(cr, uid, activity_id, context=context)
        api_pool = self.pool['t4.clinical.api']
        admit_activity = api_pool.get_activity(cr, uid, activity_id)
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, admit_activity.data_ref.patient_id.id, context=context)
        if admit_activity.data_ref.bed:
            api_pool.update_bed(cr, uid, spell_activity_id, {
                'ward_id': admit_activity.suggested_location_id.id,
                'bed': admit_activity.bed,
                'activity_id': admit_activity.id,
                'patient_id': admit_activity.data_ref.patient_id.id,
            }, context=context)
        return res
            

class t4_clinical_adt_spell_update_btuh(orm.Model):
    _name = 't4.clinical.adt.spell.update'
    _inherit = 't4.clinical.adt.spell.update'
    
    _columns = {
        'bed': fields.char('Bed', size=50)
    }
    
    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        res[self._name] = super(t4_clinical_adt_spell_update_btuh, self).complete(cr, uid, activity_id, context=context)
        api_pool = self.pool['t4.clinical.api']
        update_activity = api_pool.get_activity(cr, uid, activity_id)
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, update_activity.data_ref.patient_id.id, context=context)
        if update_activity.data_ref.bed:
            api_pool.update_bed(cr, uid, spell_activity_id, {
                'ward_id': update_activity.suggested_location_id.id,
                'bed': update_activity.bed,
                'activity_id': update_activity.id,
                'patient_id': update_activity.data_ref.patient_id.id,
            }, context=context)
        return res
            

class t4_clinical_adt_patient_transfer_btuh(orm.Model):
    _name = 't4.clinical.adt.patient.transfer'
    _inherit = 't4.clinical.adt.patient.transfer'
    
    _columns = {
        'bed': fields.char('Bed', size=50)
    }
    
    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        res[self._name] = super(t4_clinical_adt_patient_transfer_btuh, self).complete(cr, uid, activity_id, context=context)
        api_pool = self.pool['t4.clinical.api']
        transfer_activity = api_pool.get_activity(cr, uid, activity_id)
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, transfer_activity.data_ref.patient_id.id, context=context)
        if transfer_activity.data_ref.bed:
            api_pool.update_bed(cr, uid, spell_activity_id, {
                'ward_id': transfer_activity.suggested_location_id.id,
                'bed': transfer_activity.bed,
                'activity_id': transfer_activity.id,
                'patient_id': transfer_activity.data_ref.patient_id.id,
            }, context=context)
        return res