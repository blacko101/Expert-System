"""
API Views for Expert System
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from typing import Dict, Any

from ..expert_engine import run_diagnosis
from ..nlp_processor import NLPProcessor

logger = logging.getLogger(__name__)

# Initialize NLP processor
nlp_processor = NLPProcessor()

@csrf_exempt
@require_http_methods(["GET"])
def get_system_variables(request):
    """
    GET /api/system/variables
    Returns current system variables state
    """
    try:
        # In a real system, this would fetch from database
        variables = [
            {
                "name": "system_status",
                "value": "operational",
                "units": None,
                "lastUpdated": "2024-01-15T10:30:00Z",
                "description": "Overall system status",
                "category": "system"
            }
        ]
        
        return JsonResponse({
            "success": True,
            "variables": variables,
            "timestamp": "2024-01-15T10:30:00Z"
        })
    except Exception as e:
        logger.error(f"Error getting system variables: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Failed to fetch system variables",
            "details": str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_input(request):
    """
    POST /api/chatbot/input
    Process user input and return diagnosis
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        context = data.get('context', {})
        
        if not text:
            return JsonResponse({
                "success": False,
                "error": "No text provided"
            }, status=400)
        
        # Extract facts using NLP
        extracted_facts = nlp_processor.extract_facts(text, context)
        
        # Merge with existing facts
        existing_facts = context.get('facts', {})
        all_facts = {**existing_facts, **extracted_facts}
        
        # Run diagnosis
        diagnoses = run_diagnosis(all_facts)
        
        if not diagnoses:
            return JsonResponse({
                "success": True,
                "message": "Insufficient information for diagnosis",
                "diagnosis": None,
                "extractedFacts": extracted_facts,
                "needsMoreInfo": True,
                "suggestedQuestions": nlp_processor.suggest_questions(all_facts, context.get('domain'))
            })
        
        # Get top diagnosis
        top_diagnosis = diagnoses[0]
        
        response = {
            "success": True,
            "diagnosis": {
                "name": top_diagnosis.get('name', 'Unknown'),
                "confidence": top_diagnosis.get('confidence', 0.5),
                "remedy": top_diagnosis.get('remedy', ''),
                "evidence": top_diagnosis.get('evidence', ''),
                "severity": _determine_severity(top_diagnosis.get('confidence', 0.5)),
                "matchRatio": top_diagnosis.get('match_ratio', 0),
                "matchedConditions": top_diagnosis.get('matched_conditions', []),
                "unmatchedConditions": top_diagnosis.get('unmatched_conditions', [])
            },
            "extractedFacts": extracted_facts,
            "isComplete": nlp_processor.is_complete_for_diagnosis(all_facts, context.get('domain')),
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        return JsonResponse(response)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON payload"
        }, status=400)
    except Exception as e:
        logger.error(f"Error processing chatbot input: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Failed to process input",
            "details": str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def run_diagnosis_endpoint(request):
    """
    POST /api/diagnosis/run
    Run diagnosis on provided context
    """
    try:
        data = json.loads(request.body)
        context = data.get('context', {})
        
        if not context:
            return JsonResponse({
                "success": False,
                "error": "No context provided"
            }, status=400)
        
        facts = context.get('facts', {})
        domain = context.get('domain')
        
        # Validate domain
        if domain not in ['Network', 'Computer']:
            return JsonResponse({
                "success": False,
                "error": "Invalid domain. Must be 'Network' or 'Computer'"
            }, status=400)
        
        # Run diagnosis
        diagnoses = run_diagnosis(facts)
        
        if not diagnoses:
            return JsonResponse({
                "success": True,
                "diagnoses": [],
                "message": "No matching diagnoses found",
                "needsMoreInfo": True
            })
        
        # Format response
        formatted_diagnoses = []
        for diag in diagnoses[:5]:  # Return top 5
            formatted_diagnoses.append({
                "id": diag.get('id'),
                "name": diag.get('name'),
                "confidence": diag.get('confidence', 0.5),
                "remedy": diag.get('remedy', ''),
                "evidence": diag.get('evidence', ''),
                "matchRatio": diag.get('match_ratio', 0),
                "severity": _determine_severity(diag.get('confidence', 0.5))
            })
        
        response = {
            "success": True,
            "diagnoses": formatted_diagnoses,
            "topDiagnosis": formatted_diagnoses[0] if formatted_diagnoses else None,
            "totalMatches": len(diagnoses),
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        return JsonResponse(response)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON payload"
        }, status=400)
    except Exception as e:
        logger.error(f"Error running diagnosis: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Failed to run diagnosis",
            "details": str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_rules(request):
    """
    GET /api/rules
    Returns available rules
    """
    try:
        from ..expert_engine import RULES
        
        formatted_rules = []
        for rule in RULES[:50]:  # Return first 50 for brevity
            formatted_rules.append({
                "id": rule.get('id'),
                "name": rule.get('name'),
                "evidence": rule.get('evidence', ''),
                "confidence": rule.get('confidence', 0.5),
                "conditions": rule.get('conditions', []),
                "category": "Network" if rule.get('id', 0) <= 55 else "Computer"
            })
        
        return JsonResponse({
            "success": True,
            "rules": formatted_rules,
            "totalRules": len(RULES),
            "timestamp": "2024-01-15T10:30:00Z"
        })
    except Exception as e:
        logger.error(f"Error getting rules: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Failed to fetch rules",
            "details": str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    GET /api/health
    Health check endpoint
    """
    return JsonResponse({
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "services": {
            "expert_engine": "operational",
            "nlp_processor": "operational",
            "api": "operational"
        }
    })

def _determine_severity(confidence: float) -> str:
    """Determine severity based on confidence score"""
    if confidence >= 0.8:
        return "Critical"
    elif confidence >= 0.6:
        return "High"
    elif confidence >= 0.4:
        return "Medium"
    else:
        return "Low"