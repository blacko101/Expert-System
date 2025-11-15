# support_app/tests.py
from django.test import TestCase
from .expert_engine import run_diagnosis

class EngineTests(TestCase):
    def test_dns_failure(self):
        facts = {'ping_ip': 'success', 'ping_domain': 'fail'}
        res = run_diagnosis(facts)
        names = [r['name'] for r in res]
        self.assertIn('DNS Resolution Failure', names)

    def test_overheat(self):
        facts = {'cpu_temp': 90}
        res = run_diagnosis(facts)
        names = [r['name'] for r in res]
        self.assertIn('Overheating — Fan/Heatsink Fault', names)
