from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=100)
    document_number = models.CharField(max_length=100, unique=True)
    account_number = models.CharField(max_length=100, unique=True)

class Balance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class Transaction(models.Model):
    user_receptor = models.ForeignKey(User, on_delete=models.CASCADE)
    user_emisor = models.CharField(max_length=100)
    is_add = models.BooleanField()
    transaction_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20)