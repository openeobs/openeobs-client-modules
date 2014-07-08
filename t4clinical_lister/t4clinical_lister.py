from openerp.osv import orm, fields, osv
import logging
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class t4_clinical_patient_placement_lister(orm.Model):
    _name = 't4.clinical.patient.placement'
    _inherit = 't4.clinical.patient.placement'

    _POLICY = {'activities': [{'model': 't4.clinical.patient.observation.ews', 'type': 'recurring'},
                              {'model': 't4.clinical.patient.observation.weight', 'type': 'schedule'}]}


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


class t4_clinical_patient_observation_lister_weight(orm.Model):
    _name = 't4.clinical.patient.observation.weight'
    _inherit = 't4.clinical.patient.observation.weight'

    _POLICY = {
        'schedule': [[6, 0]]
    }

    def schedule(self, cr, uid, activity_id, date_scheduled=None, context=None):
        hour = td(hours=1)
        schedule_times = []
        for s in self._POLICY['schedule']:
            schedule_times.append(dt.now().replace(hour=s[0], minute=s[1], second=0, microsecond=0))
        date_schedule = date_scheduled if date_scheduled else dt.now().replace(minute=0, second=0, microsecond=0)
        utctimes = [fields.datetime.utc_timestamp(cr, uid, t, context=context) for t in schedule_times]
        while all([date_schedule.hour != date_schedule.strptime(ut, DTF).hour for ut in utctimes]):
            date_schedule += hour
        return super(t4_clinical_patient_observation_lister_weight, self).schedule(cr, uid, activity_id, date_schedule.strftime(DTF), context=context)

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['t4.activity']
        api_pool = self.pool['t4.clinical.api']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)

        res = super(t4_clinical_patient_observation_lister_weight, self).complete(cr, SUPERUSER_ID, activity_id, context)

        api_pool.cancel_open_activities(cr, uid, activity.parent_id.id, self._name, context=context)

        # create next Weight activity (schedule)
        next_activity_id = self.create_activity(cr, SUPERUSER_ID,
                             {'creator_id': activity_id, 'parent_id': activity.parent_id.id},
                             {'patient_id': activity.data_ref.patient_id.id})

        date_schedule = dt.now().replace(minute=0, second=0, microsecond=0) + td(hours=2)

        activity_pool.schedule(cr, uid, next_activity_id, date_schedule, context=context)
        return res


class lister_wardboard(osv.Model):
    _name = "t4.clinical.wardboard"
    _inherit = "t4.clinical.wardboard"

    def _get_pbp_flag(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        pbp_pool = self.pool['t4.clinical.patient.observation.pbp']
        for wb_id in ids:
            pbp_ids = self.read(cr, uid, wb_id, ['pbp_ids'], context=context)['pbp_ids']
            res[wb_id] = any([pbp_pool.read(cr, uid, pbp_id, ['result'], context=context)['result'] == 'yes' for pbp_id in pbp_ids]) if pbp_ids else False
        return res

    _columns = {
        'pbp_flag': fields.function(_get_pbp_flag, type='boolean', string='PBP Flag', readonly=True)
    }

    def wardboard_ews(self, cr, uid, ids, context={}):
        wardboard = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_lister_wardboard_obs_list_form')], context=context)
        if not model_data_ids:
            pass # view doesnt exist
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context)[0]['res_id']

        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 't4.clinical.wardboard',
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'view_id': int(view_id),
            'context': context
        }