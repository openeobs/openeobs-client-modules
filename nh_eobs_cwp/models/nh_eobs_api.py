from openerp import models, api


class NhEobsApi(models.Model):

    _inherit = 'nh.eobs.api'

    @api.model
    def get_active_observations(self, patient_id):
        if self._patient_on_obs_stop(patient_id):
            return []
        active_observations = self._get_active_observations()
        if not self.user_allocated_to_patient(patient_id):
            active_observations = filter(
                lambda active_observation: active_observation['type'] != 'ews',
                active_observations)
        return active_observations

    def user_allocated_to_patient(self, patient_id):
        patient_model = self.env['nh.clinical.patient']
        patient = patient_model.browse(patient_id)
        return self.env.user in patient.current_location_id.user_ids