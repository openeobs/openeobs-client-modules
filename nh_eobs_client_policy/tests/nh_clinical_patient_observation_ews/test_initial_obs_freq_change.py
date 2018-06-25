# coding: utf-8
from datetime import datetime, timedelta

from openerp.addons.nh_eobs_mental_health.tests.common.observation \
    import ObservationCase
from openerp.addons.nh_ews.tests.common import clinical_risk_sample_data
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf


class InitialObsFreqCommon(ObservationCase):

    def setUp(self):
        self.spell_pool = self.registry('nh.clinical.spell')
        self.observation_pool = \
            self.registry('nh.clinical.patient.observation.ews')
        self.frequencies_model = self.env['nh.clinical.frequencies.ews']
        super(InitialObsFreqCommon, self).setUp()

    def complete_obs(self, obs_data):
        super(InitialObsFreqCommon, self).complete_obs(obs_data)
        next_ews = self.activity_pool.browse(self.cr, self.uid,
                                             self.ews_activity_ids[0])

        return next_ews.data_ref.frequency


class TestChangeNoRiskAdmittedLessThanSevenDaysAgo(InitialObsFreqCommon):
    """
    Test after initial obs frequencey change for no risk admitte less than 7
    days ago
    """
    def tearDown(self):
        self.spell_pool._revert_method('read')
        super(TestChangeNoRiskAdmittedLessThanSevenDaysAgo, self).tearDown()

    def test_applies_post_initial_freq(self):
        def mock_spell_read(*args, **kwargs):
            if len(args) >= 5 and args[4] == ['date_started']:
                now = datetime.now()
                td = timedelta(days=3)
                five_days_ago = now - td
                return {'date_started': five_days_ago.strftime(dtf)}
            return mock_spell_read.origin(*args, **kwargs)
        self.spell_pool._patch_method('read', mock_spell_read)

        config_model = self.env['ir.config_parameter']
        expected_frequency = int(config_model.get_param('no_risk'))
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.NO_RISK_DATA)

        self.assertEqual(
            actual_frequency,
            expected_frequency,
            msg='Did not change freq after initial period')


class TestChangeNoRiskAdmittedMoreThanSevenDaysAgo(InitialObsFreqCommon):
    """
    Test Post Initial Obs Freq Change No Risk Admitted More than 7 days ago
    """
    def tearDown(self):
        self.spell_pool._revert_method('read')
        super(TestChangeNoRiskAdmittedMoreThanSevenDaysAgo, self).tearDown()

    def test_applies_post_initial_freq(self):

        def mock_spell_read(*args, **kwargs):
            if len(args) >= 5 and args[4] == ['date_started']:
                now = datetime.now()
                td = timedelta(days=8)
                five_days_ago = now - td
                return {'date_started': five_days_ago.strftime(dtf)}
            return mock_spell_read.origin(*args, **kwargs)

        self.spell_pool._patch_method('read', mock_spell_read)
        self.assertEqual(
            self.complete_obs(clinical_risk_sample_data.NO_RISK_DATA),
            self.observation_pool.POST_INITIAL_EWS_DAYS_NO_RISK_OBS_FREQ,
            msg='Did not change freq after initial period')


class TestInitialObsFreqChangeNo(InitialObsFreqCommon):

    def setUp(self):
        super(TestInitialObsFreqChangeNo, self).setUp()

    def test_uses_initial_period(self):
        expected_frequency = self.frequencies_model.get_risk_frequency('no')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.NO_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency,
                         msg="Did not apply initial period.")


class TestPostInitialObsFreqChangeLow(InitialObsFreqCommon):

    def tearDown(self):
        self.spell_pool._revert_method('read')
        super(TestPostInitialObsFreqChangeLow, self).tearDown()

    def test_applies_post_initial_freq(self):

        def mock_spell_read(*args, **kwargs):
            if len(args) >= 5 and args[4] == ['date_started']:
                now = datetime.now()
                td = timedelta(days=5)
                five_days_ago = now - td
                return {'date_started': five_days_ago.strftime(dtf)}
            return mock_spell_read.origin(*args, **kwargs)

        self.spell_pool._patch_method('read', mock_spell_read)

        expected_frequency = self.frequencies_model.get_risk_frequency('low')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.LOW_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency)


class TestInitialObsFreqChangeLow(InitialObsFreqCommon):

    def setUp(self):
        super(TestInitialObsFreqChangeLow, self).setUp()

    def test_uses_initial_period(self):
        expected_frequency = self.frequencies_model.get_risk_frequency('low')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.LOW_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency)


class TestPostInitialObsFreqChangeMedium(InitialObsFreqCommon):

    def tearDown(self):
        self.spell_pool._revert_method('read')
        super(TestPostInitialObsFreqChangeMedium, self).tearDown()

    def test_applies_post_initial_freq(self):

        def mock_spell_read(*args, **kwargs):
            if len(args) >= 5 and args[4] == ['date_started']:
                now = datetime.now()
                td = timedelta(days=5)
                five_days_ago = now - td
                return {'date_started': five_days_ago.strftime(dtf)}
            return mock_spell_read.origin(*args, **kwargs)

        self.spell_pool._patch_method('read', mock_spell_read)

        expected_frequency = \
            self.frequencies_model.get_risk_frequency('medium')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.MEDIUM_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency)


class TestInitialObsFreqChangeMedium(InitialObsFreqCommon):

    def setUp(self):
        super(TestInitialObsFreqChangeMedium, self).setUp()

    def test_uses_initial_period(self):
        expected_frequency = \
            self.frequencies_model.get_risk_frequency('medium')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.MEDIUM_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency)


class TestPostInitialObsFreqChangeHigh(InitialObsFreqCommon):

    def tearDown(self):
        self.spell_pool._revert_method('read')
        super(TestPostInitialObsFreqChangeHigh, self).tearDown()

    def test_applies_post_initial_freq(self):

        def mock_spell_read(*args, **kwargs):
            if len(args) >= 5 and args[4] == ['date_started']:
                now = datetime.now()
                td = timedelta(days=5)
                five_days_ago = now - td
                return {'date_started': five_days_ago.strftime(dtf)}
            return mock_spell_read.origin(*args, **kwargs)

        self.spell_pool._patch_method('read', mock_spell_read)

        expected_frequency = self.frequencies_model.get_risk_frequency('high')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.HIGH_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency)


class TestInitialObsFreqChangeHigh(InitialObsFreqCommon):

    def setUp(self):
        super(TestInitialObsFreqChangeHigh, self).setUp()

    def test_uses_initial_period(self):
        expected_frequency = self.frequencies_model.get_risk_frequency('high')
        actual_frequency = \
            self.complete_obs(clinical_risk_sample_data.HIGH_RISK_DATA)
        self.assertEqual(expected_frequency, actual_frequency)
