from openerp.osv import orm, fields
from openerp.addons.t4activity.activity import except_if
from openerp import SUPERUSER_ID, tools


class t4_clinical_ldh_diagnosis(orm.Model):
    _name = 't4.clinical.ldh.diagnosis'
    _columns = {
        'name': fields.char('Name', size=256, required=True)
    }

class t4_clinical_ldh_patient_review(orm.Model):
    _name = 't4.clinical.ldh.patient.review'
    _inherit = ['t4.clinical.notification']
    _columns = {
        'diagnosis_ids': fields.many2many('t4.clinical.ldh.diagnosis', rel='diagnosis_review_rel', string='Diagnosis')
    }

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

class t4_clinical_clerking(orm.Model):
    _name = "t4.clinical.clerking"
    _inherits = {'t4.activity': 'activity_id'}
    _description = "Clerking View"
    _auto = False
    _table = "t4_clinical_clerking"
    _columns = {
        'activity_id': fields.many2one('t4.activity', 'Activity'),
        'location_id': fields.many2one('t4.clinical.location', 'Ward'),
        'pos_id': fields.many2one('t4.clinical.pos', 'POS'),
        'patient_id': fields.many2one('t4.clinical.patient', 'Patient'),
        'hospital_number': fields.text('Hospital Number')
    }

    def init(self, cr):

        cr.execute("""
                drop view if exists %s;
                create or replace view %s as (
                    select
                        activity.id as id,
                        activity.id as activity_id,
                        activity.location_id as location_id,
                        activity.patient_id as patient_id,
                        activity.pos_id as pos_id,
                        patient.other_identifier as hospital_number
                    from t4_activity activity
                    inner join t4_clinical_patient patient on activity.patient_id = patient.id
                    where activity.data_model = 't4.clinical.ldh.patient.clerking' and activity.state not in ('completed','cancelled')
                )
        """ % (self._table, self._table))

    def complete(self, cr, uid, ids, context=None):
        activity_pool = self.pool['t4.activity']
        clerking = self.browse(cr, uid, ids[0], context=context)
        activity_pool.complete(cr, uid, clerking.activity_id.id, context=context)
        return True


class t4_clinical_review(orm.Model):
    _name = "t4.clinical.review"
    _inherits = {'t4.activity': 'activity_id'}
    _description = "Review View"
    _auto = False
    _table = "t4_clinical_review"
    _columns = {
        'activity_id': fields.many2one('t4.activity', 'Activity'),
        'location_id': fields.many2one('t4.clinical.location', 'Ward'),
        'pos_id': fields.many2one('t4.clinical.pos', 'POS'),
        'patient_id': fields.many2one('t4.clinical.patient', 'Patient'),
        'hospital_number': fields.text('Hospital Number')
    }

    def init(self, cr):

        cr.execute("""
                drop view if exists %s;
                create or replace view %s as (
                    select
                        activity.id as id,
                        activity.id as activity_id,
                        activity.location_id as location_id,
                        activity.patient_id as patient_id,
                        activity.pos_id as pos_id,
                        patient.other_identifier as hospital_number
                    from t4_activity activity
                    inner join t4_clinical_patient patient on activity.patient_id = patient.id
                    where activity.data_model = 't4.clinical.ldh.patient.review' and activity.state not in ('completed','cancelled')
                )
        """ % (self._table, self._table))

    def complete(self, cr, uid, ids, context=None):
        review = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_patient_review_complete')], context=context)
        if not model_data_ids:
            pass # view doesnt exist
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context)[0]['res_id']

        return {
            'name': 'Complete Review',
            'type': 'ir.actions.act_window',
            'res_model': 't4.clinical.ldh.patient.review',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': review.activity_id.data_ref.id,
            'target': 'new',
            'view_id': int(view_id),
            'context': context
        }


class t4_clinical_ldh_patientlist(orm.Model):
    _name = "t4.clinical.ldh.patientlist"
    _inherits = {
                 't4.clinical.patient': 'patient_id',
    }
    _description = "Task List Wardboard"
    _auto = False
    _table = "t4_clinical_ldh_patientlist"
    _rec_name = 'full_name'

    _columns = {
        'patient_id': fields.many2one('t4.clinical.patient', 'Patient'),
        'referral': fields.text('Referral'),
        'diagnosis': fields.many2many('t4.clinical.ldh.diagnosis', string='Diagnosis'),
        'plan': fields.text('Plan'),
        'clerked_by': fields.many2one('res.users', 'Clerked by'),
        'senior_review': fields.many2one('res.users', 'Senior Review'),
        'spell_activity_id': fields.many2one('t4.activity', 'Spell Activity'),
        'spell_date_started': fields.datetime('Spell Start Date'),
        'pos_id': fields.many2one('t4.clinical.pos', 'POS'),
        'spell_code': fields.text('Spell Code'),
        'full_name': fields.text("Family Name"),
        'hospital_id': fields.text('Hospital ID'),
        'location': fields.text("Current Location"),
        'location_id': fields.many2one('t4.clinical.location',"Current Location"),
        'sex': fields.text("Sex"),
        'dob': fields.datetime("DOB"),
        'age': fields.integer("Age"),
        'responsible_user': fields.many2one('res.users', 'Responsible User')
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'wardboard')
        cr.execute("""
drop view if exists %s;
create or replace view %s as (
with
completed_clerkings as(
        select
            clerking.id,
            spell.patient_id,
            clerking.write_uid,
            rank() over (partition by spell.patient_id order by activity.date_terminated desc, activity.id desc)
        from t4_clinical_spell spell
        left join t4_clinical_ldh_patient_clerking clerking on clerking.patient_id = spell.patient_id
        inner join t4_activity activity on clerking.activity_id = activity.id
        where activity.state = 'completed'
),
completed_reviews as(
        select
            review.id,
            spell.patient_id,
            review.write_uid,
            rank() over (partition by spell.patient_id order by activity.date_terminated desc, activity.id desc)
        from t4_clinical_spell spell
        left join t4_clinical_ldh_patient_review review on review.patient_id = spell.patient_id
        inner join t4_activity activity on review.activity_id = activity.id
        where activity.state = 'completed'
)
select
    spell.patient_id as id,
    spell.patient_id as patient_id,
    spell_activity.id as spell_activity_id,
    spell_activity.date_started as spell_date_started,
    spell.pos_id,
    spell.code as spell_code,
    coalesce(patient.family_name, '') || ', ' || coalesce(patient.given_name, '') || ' ' || coalesce(patient.middle_names,'') as full_name,
    location.code as location,
    location.id as location_id,
    patient.sex,
    patient.dob,
    patient.other_identifier as hospital_id,
    extract(year from age(now(), patient.dob)) as age,
    clerking.write_uid as clerked_by,
    review.write_uid as senior_review,
    users.user_id as responsible_user
from t4_clinical_spell spell
inner join t4_activity spell_activity on spell_activity.id = spell.activity_id
inner join t4_clinical_patient patient on spell.patient_id = patient.id
left join t4_clinical_location location on location.id = spell.location_id
left join (select id, patient_id, rank, write_uid from completed_clerkings where rank = 1) clerking on spell.patient_id = clerking.patient_id
left join (select id, patient_id, rank, write_uid from completed_reviews where rank = 1) review on spell.patient_id = review.patient_id
inner join activity_user_rel users on users.activity_id = spell.activity_id
where spell_activity.state = 'started'
)
        """ % (self._table, self._table))