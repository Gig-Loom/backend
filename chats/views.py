from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ChatRoom, Message, UserProfile
from gigs.models import Gig
from .serializers import MessageSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chat_room(request):
    try:
        gig_id = request.data.get("gig")
        buyer_id = request.user.id

        gig = Gig.objects.filter(id=gig_id).first()
        if not gig:
            return Response({"success": False, "error": "Gig not found."}, status=status.HTTP_404_NOT_FOUND)

        if gig.creator.id == buyer_id:
            return Response({"success": False, "error": "You cannot chat with yourself."}, status=status.HTTP_403_FORBIDDEN)

        chat_room = ChatRoom.objects.filter(gig=gig, buyer_id=buyer_id, seller_id=gig.creator.id).first()

        if chat_room:
            if chat_room.is_closed:
                chat_room.is_closed = False
                chat_room.save()
                return Response({"success": True, "message": "Chat room reopened successfully.", "data": {"chat_room_id": chat_room.id}}, status=status.HTTP_200_OK)
            else:
                return Response({"success": True, "message": "Chat room already open.", "data": {"chat_room_id": chat_room.id}}, status=status.HTTP_200_OK)
        else:
            chat_room = ChatRoom.objects.create(gig=gig, buyer_id=buyer_id, seller_id=gig.creator.id)
            return Response({"success": True, "data": {"chat_room_id": chat_room.id}}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_list(request):
    try:
        chat_rooms = ChatRoom.objects.filter(
            models.Q(buyer=request.user) | models.Q(seller=request.user), is_closed=False
        ).select_related("gig", "buyer", "seller")

        data = []
        for room in chat_rooms:
            last_message = Message.objects.filter(room=room).order_by('-timestamp').first()

            if last_message:
                if last_message.sender == request.user:
                    other_person_name = room.seller.name if room.buyer == request.user else room.buyer.name
                else:
                    other_person_name = last_message.sender.name

                last_message_time = last_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                last_message_content = last_message.content
            else:
                other_person_name = room.seller.name if room.buyer == request.user else room.buyer.name
                last_message_time = room.created_at
                last_message_content = "No messages yet"

            data.append({
                "chat_room_id": room.id,
                "last_message": last_message_content,
                "last_message_time": last_message_time,
                "other_person_name": other_person_name,
            })
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_chat_room(request, chatroom_id):
    try:
        chat_room = ChatRoom.objects.filter(id=chatroom_id, is_closed=False).first()

        if not chat_room:
            return Response({"success": False, "error": "Chat room not found or already closed."}, status=status.HTTP_404_NOT_FOUND)

        if chat_room.buyer != request.user and chat_room.seller != request.user:
            return Response({"success": False, "error": "You are not authorized to close this chat room."}, status=status.HTTP_403_FORBIDDEN)

        chat_room.is_closed = True
        chat_room.save()

        return Response({"success": True, "message": "Chat room closed successfully."}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, chatroom_id):
    try:
        chatroom = ChatRoom.objects.filter(id=chatroom_id, is_closed=False).first()

        if not chatroom:
            return Response({
                'success': False,
                'error': 'Chat room not found or closed.'
            }, status=status.HTTP_404_NOT_FOUND)

        if request.user.id != chatroom.buyer.id and request.user.id != chatroom.seller.id:
            return Response({
                'success': False,
                'error': 'You do not have permission to access this chat room.'
            }, status=status.HTTP_403_FORBIDDEN)

        page_size = 20 
        last_message_id = request.query_params.get('last_message_id')  
        
        if last_message_id:
            messages = Message.objects.filter(
                room=chatroom,
                id__lt=last_message_id
            ).order_by('-id')[:page_size]
        else:
            messages = Message.objects.filter(
                room=chatroom
            ).order_by('-id')[:page_size]

        serialized_messages = MessageSerializer(messages, many=True)

        return Response({
            'success': True,
            'data': serialized_messages.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_push_token(request):
    user = request.user
    push_token = request.data.get('push_token')
    
    if not push_token:
        return Response({'error': 'Push token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.push_token = push_token
    profile.save()
    
    return Response({'message': 'Push token updated successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_notification_settings(request):
    chat_room_id = request.data.get('chat_room_id')
    notifications_enabled = request.data.get('notifications_enabled')
    
    if chat_room_id is None or notifications_enabled is None:
        return Response({'error': 'Both chat_room_id and notifications_enabled are required'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'message': 'Notification settings updated successfully'})
