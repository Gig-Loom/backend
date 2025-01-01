from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
   sender_name = serializers.CharField(source='sender.name', read_only=True)
   timestamp = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

   class Meta:
       model = Message
       fields = ['id', 'room', 'sender', 'sender_name', 'content', 'timestamp'] 
       read_only_fields = ['id', 'room', 'sender', 'timestamp']