from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from faker import Faker
import logging
from openerp.addons.nh_observations.tests.test_scenario import ActivityTypesTest

_logger = logging.getLogger(__name__)

faker = Faker()


class TestLdhPolicy(ActivityTypesTest):

    def setUp(self):
        global cr, uid, \
               register_pool, patient_pool, admit_pool, activity_pool, transfer_pool, ews_pool, \
               activity_id, api_pool, location_pool, pos_pool, user_pool, imd_pool, discharge_pool, \
               device_connect_pool, device_disconnect_pool, partner_pool, height_pool, blood_sugar_pool, \
               blood_product_pool, weight_pool, stools_pool, gcs_pool, vips_pool, o2target_pool, o2target_activity_pool

        cr, uid = self.cr, self.uid

        register_pool = self.registry('nh.clinical.adt.patient.register')
        patient_pool = self.registry('nh.clinical.patient')
        admit_pool = self.registry('nh.clinical.adt.patient.admit')
        discharge_pool = self.registry('nh.clinical.patient.discharge')
        activity_pool = self.registry('nh.activity')
        transfer_pool = self.registry('nh.clinical.adt.patient.transfer')
        ews_pool = self.registry('nh.clinical.patient.observation.ews')
        height_pool = self.registry('nh.clinical.patient.observation.height')
        weight_pool = self.registry('nh.clinical.patient.observation.weight')
        blood_sugar_pool = self.registry('nh.clinical.patient.observation.blood_sugar')
        blood_product_pool = self.registry('nh.clinical.patient.observation.blood_product')
        stools_pool = self.registry('nh.clinical.patient.observation.stools')
        gcs_pool = self.registry('nh.clinical.patient.observation.gcs')
        vips_pool = self.registry('nh.clinical.patient.observation.vips')
        api_pool = self.registry('nh.clinical.api')
        location_pool = self.registry('nh.clinical.location')
        pos_pool = self.registry('nh.clinical.pos')
        user_pool = self.registry('res.users')
        partner_pool = self.registry('res.partner')
        imd_pool = self.registry('ir.model.data')
        device_connect_pool = self.registry('nh.clinical.device.connect')
        device_disconnect_pool = self.registry('nh.clinical.device.disconnect')
        o2target_pool = self.registry('nh.clinical.o2level')
        o2target_activity_pool = self.registry('nh.clinical.patient.o2target')

        super(TestLdhPolicy, self).setUp()

    def test_ldh_clerking_and_review_policy(self):
        # environment
        pos1_env = self.create_pos_environment()
        # register
        [self.adt_patient_register(env=pos1_env) for i in range(5)]

        # admit
        [self.adt_patient_admit(data_vals={'other_identifier': other_identifier}, env=pos1_env) for other_identifier in pos1_env['other_identifiers']]

        # placements
        [self.patient_placement(data_vals={'patient_id': patient_id}, env=pos1_env) for patient_id in pos1_env['patient_ids']]

        for patient_id in pos1_env['patient_ids']:
            clerking_ids = activity_pool.search(cr, uid, [
                ('patient_id', '=', patient_id),
                ('data_model', '=', 'nh.clinical.ldh.patient.clerking'),
                ('state', 'not in', ['completed', 'cancelled'])])
            self.assertTrue(clerking_ids, msg='Clerking activity not created')
            activity_pool.complete(cr, uid, clerking_ids[0])

        print "TEST - LDH policy tests - " + "Patient clerkings completed."

        for patient_id in pos1_env['patient_ids']:
            review_ids = activity_pool.search(cr, uid, [
                ('patient_id', '=', patient_id),
                ('data_model', '=', 'nh.clinical.ldh.patient.review'),
                ('state', 'not in', ['completed', 'cancelled'])])
            self.assertTrue(review_ids, msg='Review activity not created')
            activity_pool.complete(cr, uid, review_ids[0])

        print "TEST - LDH policy tests - " + "Patient reviews completed."