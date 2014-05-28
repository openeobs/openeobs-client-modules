from openerp.osv import orm
from openerp.addons.t4activity.activity import except_if
from openerp import SUPERUSER_ID


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


class t4_activity(orm.Model):
    _name = 't4.activity'
    _inherit = 't4.activity'

    def _get_groups(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        res = [
            ['t4.clinical.patient.placement', 'Placement'],
            ['t4.clinical.ldh.patient.clerking', 'Clerking'],
            ['t4.clinical.ldh.patient.review', 'Review']]
        fold = {r[0]: False for r in res}
        return res, fold


    # _group_by_full = {
    #     'data_model': _get_groups,
    # }