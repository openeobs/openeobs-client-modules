from openerp.osv import orm, fields
from openerp.addons.nh_activity.activity import except_if
from openerp import SUPERUSER_ID, tools


class nh_clinical_ldh_diagnosis(orm.Model):
    _name = 'nh.clinical.ldh.diagnosis'
    _columns = {
        'name': fields.char('Name', size=256, required=True)
    }

class nh_clinical_ldh_patient_review(orm.Model):
    _name = 'nh.clinical.ldh.patient.review'
    _inherit = ['nh.clinical.notification']


class nh_clinical_ldh_patient_clerking(orm.Model):
    _name = 'nh.clinical.ldh.patient.clerking'
    _inherit = ['nh.clinical.notification']

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        review_pool = self.pool['nh.clinical.ldh.patient.review']
        res = super(nh_clinical_ldh_patient_clerking, self).complete(cr, uid, activity_id, context=context)
        clerking_activity = activity_pool.browse(cr, uid, activity_id, context=context)
        review_pool.create_activity(cr,  SUPERUSER_ID, {
            'summary': clerking_activity.data_ref.patient_id.name+' Review',
            'parent_id': clerking_activity.parent_id.id,
            'creator_id': activity_id
        }, {'patient_id': clerking_activity.data_ref.patient_id.id})
        return res

class nh_clinical_patient_placement(orm.Model):
    _name = 'nh.clinical.patient.placement'
    _inherit = 'nh.clinical.patient.placement'

    _POLICY = {'activities': [{'model': 'nh.clinical.ldh.patient.clerking', 'type': 'start'}]}


class nh_clinical_workload(orm.Model):
    _name = "nh.ldh.activity.workload"
    _inherits = {'nh.activity': 'activity_id'}
    _description = "LDH Activity Workload"
    _auto = False
    _table = "nh_ldh_activity_workload"
    _data_models = [(10, 'Referral'),
                    (20, 'Clerking'),
                    (30, 'Review')]
    _columns = {
        'activity_id': fields.many2one('nh.activity', 'Activity', required=True, ondelete='cascade'),
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
                            when act.data_model = 'nh.clinical.patient.placement' then 10
                            when act.data_model = 'nh.clinical.ldh.patient.clerking' then 20
                            when act.data_model = 'nh.clinical.ldh.patient.review' then 30
                        else null end as activity_type
                    from nh_activity act
                )
        """ % (self._table, self._table))

    def _get_groups(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        at_copy = [(at[0], at[1]) for at in self._data_models]
        groups = at_copy
        fold = {at[0]: False for at in at_copy}
        return groups, fold

    _group_by_full = {'activity_type': _get_groups}

class nh_clinical_clerking(orm.Model):
    _name = "nh.clinical.clerking"
    _inherits = {'nh.activity': 'activity_id'}
    _description = "Clerking View"
    _auto = False
    _table = "nh_clinical_clerking"
    _columns = {
        'activity_id': fields.many2one('nh.activity', 'Activity'),
        'location_id': fields.many2one('nh.clinical.location', 'Ward'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
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
                    from nh_activity activity
                    inner join nh_clinical_patient patient on activity.patient_id = patient.id
                    where activity.data_model = 'nh.clinical.ldh.patient.clerking' and activity.state not in ('completed','cancelled')
                )
        """ % (self._table, self._table))

    def complete(self, cr, uid, ids, context=None):
        activity_pool = self.pool['nh.activity']
        clerking = self.browse(cr, uid, ids[0], context=context)
        activity_pool.complete(cr, uid, clerking.activity_id.id, context=context)
        return True


class nh_clinical_review(orm.Model):
    _name = "nh.clinical.review"
    _inherits = {'nh.activity': 'activity_id'}
    _description = "Review View"
    _auto = False
    _table = "nh_clinical_review"
    _columns = {
        'activity_id': fields.many2one('nh.activity', 'Activity'),
        'location_id': fields.many2one('nh.clinical.location', 'Ward'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
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
                    from nh_activity activity
                    inner join nh_clinical_patient patient on activity.patient_id = patient.id
                    where activity.data_model = 'nh.clinical.ldh.patient.review' and activity.state not in ('completed','cancelled')
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
            'res_model': 'nh.clinical.ldh.patient.review',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': review.activity_id.data_ref.id,
            'target': 'new',
            'view_id': int(view_id),
            'context': context
        }


class nh_clinical_spell_ldh(orm.Model):

    _name = 'nh.clinical.spell'
    _inherit = 'nh.clinical.spell'

    _columns = {
        'diagnosis': fields.text('Diagnosis'),
        'plan': fields.text('Plan'),
        'outstanding_jobs': fields.text('Outstanding Jobs')
    }


class nh_clinical_ldh_spell_update(orm.Model):
    _name = 'nh.clinical.ldh.spell.update'
    _inherit = ['nh.activity.data']
    _columns = {
        'spell_activity_id': fields.many2one('nh.activity', 'Spell Activity', required=True),
        'diagnosis': fields.text('Diagnosis'),
        'plan': fields.text('Plan'),
        'outstanding_jobs': fields.text('Outstanding Jobs')
    }

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        spell_update = activity_pool.browse(cr, uid, activity_id, context=context)
        data = {}
        data.update({'diagnosis': spell_update.data_ref.diagnosis}) if spell_update.data_ref.diagnosis else 0
        data.update({'plan': spell_update.data_ref.plan}) if spell_update.data_ref.plan else 0
        data.update({'outstanding_jobs': spell_update.data_ref.outstanding_jobs}) if spell_update.data_ref.outstanding_jobs else 0
        activity_pool.submit(cr, uid, spell_update.data_ref.spell_activity_id.id, data, context=context)
        return super(nh_clinical_ldh_spell_update, self).complete(cr, uid, activity_id, context=context)


class nh_clinical_ldh_patientlist(orm.Model):
    _name = "nh.clinical.ldh.patientlist"
    _inherits = {
                 'nh.clinical.patient': 'patient_id',
    }
    _description = "Task List Wardboard"
    _auto = False
    _table = "nh_clinical_ldh_patientlist"
    _rec_name = 'full_name'

    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
        # 'referral': fields.text('Referral'),
        'diagnosis': fields.text('Diagnosis'),
        'plan': fields.text('Plan'),
        'outstanding_jobs': fields.text('Outstanding Jobs'),
        'clerked_by': fields.many2one('res.users', 'Clerked by'),
        'senior_review': fields.many2one('res.users', 'Senior Review'),
        'spell_activity_id': fields.many2one('nh.activity', 'Spell Activity'),
        'spell_date_started': fields.datetime('Spell Start Date'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'spell_code': fields.text('Spell Code'),
        'full_name': fields.text("Family Name"),
        'hospital_id': fields.text('Hospital ID'),
        'location': fields.text("Current Location"),
        'location_id': fields.many2one('nh.clinical.location',"Current Location"),
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
            activity.terminate_uid,
            rank() over (partition by spell.patient_id order by activity.date_terminated desc, activity.id desc)
        from nh_clinical_spell spell
        left join nh_clinical_ldh_patient_clerking clerking on clerking.patient_id = spell.patient_id
        inner join nh_activity activity on clerking.activity_id = activity.id
        where activity.state = 'completed'
),
completed_reviews as(
        select
            review.id,
            spell.patient_id,
            activity.terminate_uid,
            rank() over (partition by spell.patient_id order by activity.date_terminated desc, activity.id desc)
        from nh_clinical_spell spell
        left join nh_clinical_ldh_patient_review review on review.patient_id = spell.patient_id
        inner join nh_activity activity on review.activity_id = activity.id
        where activity.state = 'completed'
)
select
    spell.patient_id as id,
    spell.patient_id as patient_id,
    spell.diagnosis as diagnosis,
    spell.plan as plan,
    spell.outstanding_jobs as outstanding_jobs,
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
    clerking.terminate_uid as clerked_by,
    review.terminate_uid as senior_review,
    users.user_id as responsible_user
from nh_clinical_spell spell
inner join nh_activity spell_activity on spell_activity.id = spell.activity_id
inner join nh_clinical_patient patient on spell.patient_id = patient.id
left join nh_clinical_location location on location.id = spell.location_id
left join (select id, patient_id, rank, terminate_uid from completed_clerkings where rank = 1) clerking on spell.patient_id = clerking.patient_id
left join (select id, patient_id, rank, terminate_uid from completed_reviews where rank = 1) review on spell.patient_id = review.patient_id
inner join activity_user_rel users on users.activity_id = spell.activity_id
where spell_activity.state = 'started'
)
        """ % (self._table, self._table))

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('diagnosis') or vals.get('plan') or vals.get('outstanding_jobs'):
            update_pool = self.pool['nh.clinical.ldh.spell.update']
            activity_pool = self.pool['nh.activity']
            for patientlist in self.browse(cr, uid, ids, context=context):
                activity = {
                    'parent_id': patientlist.spell_activity_id.id
                }
                data = {
                    'spell_activity_id': patientlist.spell_activity_id.id,
                    'diagnosis': vals.get('diagnosis'),
                    'plan': vals.get('plan'),
                    'outstanding_jobs': vals.get('outstanding_jobs')
                }
                spell_update_id = update_pool.create_activity(cr, SUPERUSER_ID, activity, data, context=context)
                activity_pool.complete(cr, uid, spell_update_id, context=context)
        return True


class nh_clinical_placement_ldh(orm.Model):
    _name = "nh.clinical.placement"
    _inherit = "nh.clinical.placement"

    def complete(self, cr, uid, ids, context=None):
        placement = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_patient_placement_complete')], context=context)
        if not model_data_ids:
            pass # view doesnt exist
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context)[0]['res_id']

        return {
            'name': 'Patient On Site',
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.patient.placement',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': placement.activity_id.data_ref.id,
            'target': 'new',
            'view_id': int(view_id),
            'context': context
        }

