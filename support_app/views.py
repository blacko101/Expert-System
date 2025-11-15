# support_app/views.py
import json
from django.shortcuts import render
from django.views import View
from .forms import DiagnoseForm
from .expert_engine import run_diagnosis
from .models import Case
from django.http import JsonResponse

def _normalize_form_data(cd: dict):
    facts = {}
    def conv_bool(v):
        if v in ('true', 'True', True): return True
        if v in ('false', 'False', False): return False
        return v
    for k, v in cd.items():
        if v in (None, '', []):
            continue
        if k == 'structured':
            # JSON input
            try:
                j = json.loads(v)
                if isinstance(j, dict):
                    facts.update(j)
            except Exception:
                pass
            continue
        if k in ('wifi_connected','popups','app_crash'):
            facts[k] = conv_bool(v)
        else:
            # attempt numeric conversion if possible
            try:
                if isinstance(v, str) and v.isdigit():
                    facts[k] = int(v)
                else:
                    # try float
                    fv = float(v)
                    facts[k] = fv
            except Exception:
                facts[k] = v
    return facts

class DiagnoseView(View):
    template_name = 'support_app/diagnose.html'

    def get(self, request):
        form = DiagnoseForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        # AJAX POST expected
        form = DiagnoseForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
        facts = _normalize_form_data(form.cleaned_data)
        diagnoses = run_diagnosis(facts)
        # Save case
        case = Case.objects.create(user=request.user if request.user.is_authenticated else None,
                                    symptoms=facts, diagnoses=diagnoses, status='diag')
        return JsonResponse({'ok': True, 'diagnoses': diagnoses, 'case_id': case.id})
