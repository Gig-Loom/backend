from django.db import models
from django.contrib.auth import get_user_model
from gigs.models import Gig

User = get_user_model()

class ChatRoom(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name="chat_rooms")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_buyer")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_seller")
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom for {self.gig.title} (Buyer: {self.buyer.name}, Seller: {self.seller.name})"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.name} in {self.room.gig.title}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    push_token = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
