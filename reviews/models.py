from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Review(models.Model):
    gig = models.ForeignKey('gigs.Gig', on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_reviews')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_reviews')
    rating =models.FloatField(default=0, validators=[
        MinValueValidator(0), MaxValueValidator(5)
    ])
    comment = models.TextField(blank=True, null=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.buyer.name} for {self.gig.title}"

    class Meta:
        ordering = ['-created_at']  
