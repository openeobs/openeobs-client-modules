from openerp.osv import orm, fields
from openerp.addons.t4activity.activity import except_if
from openerp import SUPERUSER_ID, tools


class t4_clinical_ldh_patient_review(orm.Model):
    _name = 't4.clinical.ldh.patient.review'
    _inherit = ['t4.clinical.notification']

class t4_clinical_ldh_patient_clerking(orm.Model):
    _name = 't4.clinical.ldh.patient.clerking'
    _inherit = ['t4.clinical.notification']

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['t4.activity']
        review_pool = self.pool['t4.clinical.ldh.patient.review']
        res = super(t4_clinical_ldh_patient_clerking, self).complete(cr, uid, activity_id, context=context)
        clerking_activity = activity_pool.browse(cr, uid, activity_id, context=context)
        review_pool.create_activity(cr,  SUPERUSER_ID, {
            'summary': clerking_activity.data_ref.patient_id.name+' Review',
            'parent_id': clerking_activity.parent_id.id,
            'creator_id': activity_id
        }, {'patient_id': clerking_activity.data_ref.patient_id.id})
        return res

class t4_clinical_patient_placement(orm.Model):
    _name = 't4.clinical.patient.placement'
    _inherit = 't4.clinical.patient.placement'

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['t4.activity']
        api_pool = self.pool['t4.clinical.api']
        move_pool = self.pool['t4.clinical.patient.move']
        clerking_pool = self.pool['t4.clinical.ldh.patient.clerking']
        placement_activity = activity_pool.browse(cr, uid, activity_id, context=context)
        except_if(not placement_activity.data_ref.location_id,
                  msg="Location is not set for the placement thus the placement can't be completed!")
        res = super(t4_clinical_patient_placement, self).complete(cr, uid, activity_id, context=context)

        placement_activity = activity_pool.browse(cr, uid, activity_id, context=context)
        # set spell location
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, uid, placement_activity.data_ref.patient_id.id, context=context)
        except_if(not spell_activity_id,
                  cap="Spell in state 'started' is not found for patient_id=%s" % placement_activity.data_ref.patient_id.id,
                  msg="Placement can not be completed")
        # move to location
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
                                                    {'parent_id': spell_activity_id,
                                                     'creator_id': activity_id},
                                                    {'patient_id': placement_activity.data_ref.patient_id.id,
                                                     'location_id': placement_activity.data_ref.location_id.id})
        activity_pool.complete(cr, uid, move_activity_id)
        activity_pool.submit(cr, SUPERUSER_ID, spell_activity_id, {'location_id': placement_activity.data_ref.location_id.id})
        clerking_activity_id = clerking_pool.create_activity(cr,  SUPERUSER_ID, {
            'summary': placement_activity.data_ref.patient_id.name+' Clerking',
            'parent_id': spell_activity_id,
            'creator_id': activity_id,
        }, {
            'patient_id': placement_activity.data_ref.patient_id.id
        })
        activity_pool.start(cr, uid, clerking_activity_id)
        return res


class t4_clinical_workload(orm.Model):
    _name = "t4.ldh.activity.workload"
    _inherits = {'t4.activity': 'activity_id'}
    _description = "LDH Activity Workload"
    _auto = False
    _table = "t4_ldh_activity_workload"
    _data_models = [(10, 'Placement'),
                    (20, 'Clerking'),
                    (30, 'Review')]
    _columns = {
        'activity_id': fields.many2one('t4.activity', 'Activity', required=True, ondelete='cascade'),
        'activity_type': fields.selection(_data_models, 'Activity Type', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'wardboard')
        cr.execute("""
                drop view if exists %s;
                create or replace view %s as (
                    select
                        act.id,
                        act.id as activity_id,
                        case
                            when act.data_model = 't4.clinical.patient.placement' then 10
                            when act.data_model = 't4.clinical.ldh.patient.clerking' then 20
                            when act.data_model = 't4.clinical.ldh.patient.review' then 30
                        else null end as activity_type
                    from t4_activity act
                )
        """ % (self._table, self._table))

    def _get_groups(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        at_copy = [(at[0], at[1]) for at in self._data_models]
        groups = at_copy
        fold = {at[0]: False for at in at_copy}
        return groups, fold

    _group_by_full = {'activity_type': _get_groups}