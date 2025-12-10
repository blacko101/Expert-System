"""
Custom exception handlers for API
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns standardized error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the error response
        response.data = {
            'success': False,
            'error': response.data.get('detail', 'An error occurred'),
            'code': response.status_code,
        }
    else:
        # Handle uncaught exceptions
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        response = Response({
            'success': False,
            'error': 'Internal server error',
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response