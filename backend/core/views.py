"""
API Views for GoldVenture Platform
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Placeholder views - will be implemented when we build Claude integration

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claude_chat(request):
    """
    Handle Claude chat requests with MCP tool access.

    POST /api/claude/chat/
    {
        "message": "What are our total gold resources?",
        "conversation_history": [...],  # optional
        "system_prompt": "..."  # optional
    }
    """
    # TODO: Implement Claude integration
    return Response({
        'error': 'Claude integration not yet implemented. Coming in next step!'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_tools(request):
    """
    Get list of all available MCP tools for the user's company.

    GET /api/claude/tools/
    """
    # TODO: Implement tool listing
    return Response({
        'error': 'Tool listing not yet implemented. Coming in next step!'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)
