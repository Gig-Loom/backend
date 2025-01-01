from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['gig', 'buyer', 'seller', 'rating', 'comment', 'payment_proof']
        read_only_fields = ['buyer', 'seller']  
