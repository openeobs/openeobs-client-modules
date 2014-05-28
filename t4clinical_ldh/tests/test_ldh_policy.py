from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from faker import Faker
import logging

_logger = logging.getLogger(__name__)

faker = Faker()


class TestLdhPolicy(common.SingleTransactionCase):

    def setUp(self):
        global cr, uid
        global patient_pool, activity_pool, register_pool, admit_pool, placement_pool, location_pool
        global api_pool

        cr, uid = self.cr, self.uid

        patient_pool = self.registry('t4.clinical.patient')
        activity_pool = self.registry('t4.activity')
        register_pool = self.registry('t4.clinical.adt.patient.register')
        admit_pool = self.registry('t4.clinical.adt.patient.admit')
        activity_pool = self.registry('t4.activity')
        placement_pool = self.registry('t4.clinical.patient.placement')
        location_pool = self.registry('t4.clinical.location')
        api_pool = self.registry('t4.clinical.api')

        super(TestLdhPolicy, self).setUp()

    def xml2db_id(self, xmlid):
        imd_pool = self.registry('ir.model.data')
        imd_id = imd_pool.search(self.cr, self.uid, [('name', '=', xmlid)])
        db_id = imd_id and imd_pool.browse(self.cr, self.uid, imd_id[0]).res_id or False
        return db_id

    def test_ldh_policy(self):
        global cr, uid
        global patient_pool, activity_pool, ews_pool, register_pool, admit_pool, placement_pool, location_pool
        global faker, api_pool

        adt_uid = self.xml2db_id("t4c_ldh_adt_user")

        gender = faker.random_element(array=('M', 'F'))
        patient_data = {
            'family_name': faker.last_name(),
            'other_identifier': str(faker.random_int(min=1001, max=9999)),
            'dob': faker.date_time_between(start_date="-80y", end_date="-10y").strftime(DTF),
            'gender': gender,
            'sex': gender,
            'given_name': faker.first_name()
        }
        reg_activity_id = register_pool.create_activity(cr, adt_uid, {}, patient_data)
        self.assertTrue(reg_activity_id, msg='Error trying to register patient')
        print "TEST - setting up LDH policy tests - " + "Patient registered."

        patient_domain = [(k, '=', v) for k, v in patient_data.iteritems()]
        patient_id = patient_pool.search(cr, adt_uid, patient_domain)
        self.assertTrue(patient_id, msg='Patient not created')
        patient_id = patient_id[0]
        admit_data = {
            'code': str(faker.random_int(min=10001, max=99999)),
            'other_identifier': patient_data['other_identifier'],
            'location': faker.random_element(array=('EAU', 'AE')),
            'start_date': faker.date_time_between(start_date="-1w", end_date="-1h").strftime(DTF)
        }
        admit_activity_id = admit_pool.create_activity(cr, adt_uid, {}, admit_data)
        self.assertTrue(admit_activity_id, msg='Error trying to admit patient')
        activity_pool.complete(cr, adt_uid, admit_activity_id)
        print "TEST - setting up LDH policy tests - " + "Patient admitted."
        available_bed_location_ids = location_pool.get_available_location_ids(cr, uid, ['bed'])
        if admit_data['location'] == 'EAU':
            wm_uid = self.xml2db_id("t4c_ldh_ward_manager_winifred_user")
            hca_uid = self.xml2db_id("t4c_ldh_hca_harold_user")
            nur_uid = self.xml2db_id("t4c_ldh_nurse_norah_user")
            doc_uid = self.xml2db_id("t4c_ldh_doctor_dave_user")
        else:
            wm_uid = self.xml2db_id("t4c_ldh_ward_manager_whitney_user")
            hca_uid = self.xml2db_id("t4c_ldh_hca_hannah_user")
            nur_uid = self.xml2db_id("t4c_ldh_nurse_nathan_user")
            doc_uid = self.xml2db_id("t4c_ldh_doctor_davina_user")
        location_ids = location_pool.search(cr, uid, [
                ('parent_id.code', '=', admit_data['location']),
                ('id', 'in', available_bed_location_ids)])
        if not location_ids:
            _logger.warning("No available locations found for parent location %s" % admit_data['location'])
            return
        location_id = location_ids[0]
        placement_activity_ids = placement_pool.search(cr, uid, [('patient_id', '=', patient_id)])
        self.assertTrue(placement_activity_ids, msg='Placement activity not created')
        placement_id = placement_pool.read(cr, uid, placement_activity_ids[0], ['activity_id'])
        placement_activity_id = placement_id['activity_id'][0]

        activity_pool.submit(cr, wm_uid, placement_activity_id, {'location_id': location_id})

        activity_pool.complete(cr, wm_uid, placement_activity_id)
        print "TEST - LDH policy tests - " + "Patient placement completed."

        clerking_ids = activity_pool.search(cr, hca_uid, [
            ('patient_id', '=', patient_id),
            ('data_model', '=', 't4.clinical.ldh.patient.clerking'),
            ('state', 'not in', ['completed', 'cancelled'])])
        self.assertTrue(clerking_ids, msg='Clerking activity not created')
        activity_pool.complete(cr, hca_uid, clerking_ids[0])
        print "TEST - LDH policy tests - " + "Patient clerking completed."

        review_ids = activity_pool.search(cr, doc_uid, [
            ('patient_id', '=', patient_id),
            ('data_model', '=', 't4.clinical.ldh.patient.review'),
            ('state', 'not in', ['completed', 'cancelled'])])
        self.assertTrue(review_ids, msg='Review activity not created')
        activity_pool.complete(cr, doc_uid, review_ids[0])
        print "TEST - LDH policy tests - " + "Patient review completed."