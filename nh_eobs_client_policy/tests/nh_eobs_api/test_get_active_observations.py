from openerp.tests.common import TransactionCase


class TestGetActiveObservations(TransactionCase):
    """
    Test that get_active_observations returns the list of active observations
    installed into the system plus neurological observations and removes GCS
    from the list as per EOBS-1014
    """

    def setUp(self):
        super(TestGetActiveObservations, self).setUp()
        self.test_utils_model = self.env['nh.clinical.test_utils']
        self.test_utils_model.admit_and_place_patient()
        self.test_utils_model.copy_instance_variables(self)

        self.api_model = self.env['nh.eobs.api']

    def call_test(self):
        self.obs_list = self.api_model.get_active_observations(self.patient.id)

    def test_adds_neurological_observations(self):
        """
        Test that the neurological observation dict is added to the returned
        list
        """
        self.call_test()
        neuro = \
            [ob for ob in self.obs_list if ob.get('type') == 'neurological']
        self.assertEqual(
            neuro,
            [
                {
                    'type': 'neurological',
                    'name': 'Neurological'
                }
            ]
        )

    def test_removes_gcs(self):
        """
        Test that the gcs dict is removed from the returned list
        """
        self.call_test()
        gcs = [ob for ob in self.obs_list if 'type' == 'gcs']
        self.assertEqual(gcs, [])

    def test_empty_list_on_obs_stop(self):
        """
        Test that no observations are displayed when obs_stop flag is set to
        True
        """
        self.test_utils_model.start_pme()
        self.call_test()
        self.assertEqual(self.obs_list, [])
