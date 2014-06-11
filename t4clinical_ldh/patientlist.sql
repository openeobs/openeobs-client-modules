with
completed_clerkings as(
		select
			clerking.id,
			spell.patient_id,
			activity.complete_uid,
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
			activity.complete_uid,
			rank() over (partition by spell.patient_id order by activity.date_terminated desc, activity.id desc)
		from t4_clinical_spell spell
		left join t4_clinical_ldh_patient_review review on review.patient_id = spell.patient_id
		inner join t4_activity activity on review.activity_id = activity.id
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
	clerking.complete_uid as clerked_by,
	review.complete_uid as senior_review,
    users.user_id as responsible_user
from t4_clinical_spell spell
inner join t4_activity spell_activity on spell_activity.id = spell.activity_id
inner join t4_clinical_patient patient on spell.patient_id = patient.id
left join t4_clinical_location location on location.id = spell.location_id
left join (select id, patient_id, rank, complete_uid from completed_clerkings where rank = 1) clerking on spell.patient_id = clerking.patient_id
left join (select id, patient_id, rank, complete_uid from completed_reviews where rank = 1) review on spell.patient_id = review.patient_id
left join activity_user_rel users on users.activity_id = spell.activity_id
where spell_activity.state = 'started'