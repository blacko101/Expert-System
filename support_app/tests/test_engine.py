from django.test import SimpleTestCase
from support_app.expert_engine import run_diagnosis


class EngineSmokeTests(SimpleTestCase):
    def test_run_diagnosis_returns_structure(self):
        facts = {'ping_latency': 250, 'wifi_connected': True}
        res = run_diagnosis(facts)
        self.assertIsInstance(res, list)
        if res:
            top = res[0]
            self.assertIn('name', top)
            self.assertIn('confidence', top)
            self.assertIn('evidence', top)
            self.assertIn('remedy', top)

    def test_high_latency(self):
        facts = {'ping_latency': 250}
        res = run_diagnosis(facts)
        self.assertTrue(len(res) > 0)
        top = res[0]
        # Expect a rule about latency to be present in the name (case-insensitive)
        self.assertTrue('latency' in (top.get('name') or '').lower() or 'latency' in (top.get('name') or ''))
        self.assertGreaterEqual(top.get('score', 0), 0.0)

    def test_insufficient_data(self):
        facts = {}
        res = run_diagnosis(facts)
        self.assertTrue(len(res) >= 1)
        # fallback should be 'Insufficient Data to Diagnose' somewhere in names
        names = [r.get('name', '') for r in res]
        self.assertTrue(any('insufficient' in n.lower() for n in names))
