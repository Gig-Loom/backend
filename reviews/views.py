import os
from django.core.files.storage import default_storage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from .models import Review
from chats.models import ChatRoom
from .serializers import ReviewSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request):
    try:
        chat_room_id = request.data.get('chatRoomId')
        rating = Decimal(request.data.get('rating'))
        comment = request.data.get('comment')
        payment_proof = request.FILES.get('paymentProof')  

        if rating < 0 or rating > 5:
            return Response({
                'success': False,
                'error': 'Rating must be between 0 and 5.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not chat_room_id or not rating or not payment_proof:
            return Response({
                'success': False,
                'error': 'Room, rating, and payment proof are required fields.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        chat_room = ChatRoom.objects.filter(id=chat_room_id).first()
        
        if not chat_room:
            return Response({
                'success': False,
                'error': 'Chat room not found.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        gig = chat_room.gig
        buyer = chat_room.buyer
        seller = chat_room.seller
        
        if request.user != buyer:
            return Response({
                'success': False,
                'error': 'Only the buyer can submit a review.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        review_count = Review.objects.filter(gig=gig, buyer=request.user).count()
        filename = f"{gig.id}_{request.user.id}_{review_count + 1}{os.path.splitext(payment_proof.name)[1]}"
        file_path = os.path.join('payment_proofs', filename)

        with default_storage.open(file_path, 'wb') as destination:
            for chunk in payment_proof.chunks():
                destination.write(chunk)
            
        review = Review.objects.create(
            gig=gig,
            buyer=request.user,
            seller=seller,
            rating=rating,
            comment=comment,
            payment_proof=file_path,
        )
        
        total_rating = gig.rating * gig.number_of_raters  
        gig.number_of_raters += 1  
        new_rating = (total_rating + rating) / gig.number_of_raters  
        gig.rating = new_rating  
        gig.save()  

        serialized_review = ReviewSerializer(review)

        return Response({
            'success': True,
            'data': serialized_review.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
