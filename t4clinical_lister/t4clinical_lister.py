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
                              {'model': 't4.clinical.patient.weight_monitoring', 'type': 'complete',
                               'data': {'weight_monitoring': True}}]}


class t4_clinical_patient_observation_lister_ews(orm.Model):
    _name = 't4.clinical.patient.observation.ews'
    _inherit = 't4.clinical.patient.observation.ews'

    _POLICY = {'ranges': [0, 4, 6], 'case': '0123', 'frequencies': [240, 240, 60, 15],
               'notifications': [
                   [],
                   [{'model': 'assessment', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}],
                   [{'model': 'inform_doctor', 'summary': 'Urgently inform medical team', 'groups': ['nurse', 'hca']},
                    {'model': 'frequency', 'groups': ['nurse', 'hca']},
                    {'model': 'nurse', 'summary': 'Inform CCOT if unresolved after one hour. Bleep L1663 or Q0169', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}],
                   [{'model': 'inform_doctor', 'summary': 'Immediately inform SPR or above', 'groups': ['nurse', 'hca']},
                    {'model': 'nurse', 'summary': 'Urgent assessment by CCOT', 'groups': ['nurse', 'hca']},
                    {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
                    {'model': 'nurse', 'summary': 'Informed about patient status (NEWS)', 'groups': ['hca']}]
               ],
               'risk': ['None', 'Low', 'Medium', 'High']}


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


class t4_clinical_notification_inform_doctor(orm.Model):
    _name = 't4.clinical.notification.inform_doctor'
    _inherit = ['t4.clinical.notification']
    _description = 'Inform Medical Team?'
    _notifications = [{'model': 'doctor_assessment', 'groups': ['nurse']}]

    _columns = {
        'doctor_id': fields.many2one('res.partner', 'Informed Doctor', domain=[('doctor', '=', True)]),
    }
    _form_description = [
        {
            'name': 'doctor_id',
            'type': 'selection',
            'label': 'Informed Doctor'
        }
    ]

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['t4.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        api_pool = self.pool['t4.clinical.api']
        api_pool.trigger_notifications(cr, uid, {
            'notifications': self._notifications,
            'parent_id': activity.parent_id.id,
            'creator_id': activity_id,
            'patient_id': activity.data_ref.patient_id.id,
            'model': activity.creator_id._name,
            'group': 'nurse'
        }, context=context)
        return super(t4_clinical_notification_inform_doctor, self).complete(cr, uid, activity_id, context=context)

    def get_form_description(self, cr, uid, patient_id, context=None):
        partner_pool = self.pool['res.partner']
        fd = list(self._form_description)
        # Find Doctors
        doctor_ids = partner_pool.search(cr, uid, [('doctor', '=', True)], context=context)
        doctor_selection = [[d, partner_pool.read(cr, uid, d, ['name'], context=context)['name']] for d in doctor_ids]
        for field in fd:
            if field['name'] == 'doctor_id':
                field['selection'] = doctor_selection
        return fd


class lister_notification_frequency(orm.Model):
    _name = 't4.clinical.notification.frequency'
    _inherit = 't4.clinical.notification.frequency'
    _description = 'Review Frequency'
    _notifications = [{'model': 'inform_doctor', 'groups': ['nurse']}]
