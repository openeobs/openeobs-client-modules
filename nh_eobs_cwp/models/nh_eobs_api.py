from openerp import models, api


class NhEobsApi(models.Model):

    _inherit = 'nh.eobs.api'

    @api.model
    def get_active_observations(self, patient_id):
        """
        Override to add Therapeutic observation and filter out the NEWS
        observation if the user is not allocated to the patient's bed.

        :param patient_id:
        :return:
        """
        # Check for obs stop.
        if not super(NhEobsApi, self).get_active_observations(patient_id):
            return []
        active_observations = [
            {
                'type': 'ews',
                'name': 'NEWS'
            },
            {
                'type': 'therapeutic',
                'name': 'Therapeutic'
            },
            {
                'type': 'blood_glucose',
                'name': 'Blood Glucose'
            },
            {
                'type': 'blood_product',
                'name': 'Blood Product'
            },
            {
                'type': 'height',
                'name': 'Height'
            },
            {
                'type': 'neurological',
                'name': 'Neurological'
            },
            {
                'type': 'pbp',
                'name': 'Postural Blood Pressure'
            },
            {
                'type': 'weight',
                'name': 'Weight'
            },
        ]
        if not self.user_allocated_to_patient(patient_id):
            active_observations = filter(
                lambda active_observation: active_observation['type'] != 'ews',
                active_observations)
        return active_observations
