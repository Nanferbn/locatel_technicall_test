from django.db import transaction
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Customer, Balance, Transaction
from decimal import Decimal
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


class RegisterSerializer(serializers.ModelSerializer):
    document_type = serializers.CharField(write_only=True)
    document_number = serializers.CharField(write_only=True)
    account_number = serializers.CharField(write_only=True)
    initial_balance = serializers.DecimalField(write_only=True, max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'password',
            'document_type', 
            'document_number', 
            'account_number', 
            'initial_balance'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("El usuario ya existe.")
        return value    

    def create(self, validated_data):
        with transaction.atomic():
            email = validated_data.pop('email')
            password = validated_data.pop('password')
            user_data = {
                'username': email,
                'email': email,
                'password': password,
                'first_name': validated_data.pop('first_name', None),
                'last_name': validated_data.pop('last_name', None),
            }
            user = User.objects.create_user(**user_data)
            user.set_password(password)
            user.save()

            initial_balance_amount = validated_data.pop('initial_balance', Decimal('0.00'))

            customer_data = {
                'account_number': validated_data.pop('account_number'),
                'document_type': validated_data.pop('document_type'),
                'document_number': validated_data.pop('document_number')
            }

            customer = Customer.objects.create(user=user, **customer_data)

            transaction_data = {
                'user_receptor': user,
                'user_emisor': customer_data['document_number'],
                'is_add': True,
                'type': 'consignation',
                'amount': initial_balance_amount
            }
            transaction_ = Transaction.objects.create(**transaction_data)

            balance_data = {
                'user': user,
                'balance': initial_balance_amount
            }
            balance = Balance.objects.create(**balance_data)

            return user

    

# This serializer is used to validate user data
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return {'user': user}
        raise serializers.ValidationError("Credenciales incorrectas")

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class BalanceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Balance
        fields = ['user', 'balance']

class ConsignationSerializer(serializers.Serializer):
    account_number = serializers.CharField(write_only=True)
    user_emisor = serializers.CharField(write_only=True)
    amount = serializers.DecimalField(write_only=True, max_digits=10, decimal_places=2)

    def validate_account_number(self, value):
        # Check if the account number exists in the database
        if not Customer.objects.filter(account_number=value).exists():
            raise serializers.ValidationError("Número de cuenta no encontrado.")
        return value

    def save(self):
        # Extract validated data
        account_number = self.validated_data['account_number']
        user_emisor = self.validated_data['user_emisor']
        amount = self.validated_data['amount']

        # Get the receiving customer from the account number
        customer = Customer.objects.get(account_number=account_number)
        user_receptor = customer.user

        # Create the transaction and update the balance within an atomic block
        # to ensure that all actions are executed
        with transaction.atomic():
            # Create transacción
            transaction_ = Transaction.objects.create(
                user_receptor = user_receptor,
                user_emisor = user_emisor,
                is_add = True,
                type = 'withdrawal',
                amount = amount
            )

            # Get or create the balance for the receiving user
            balance, _ = Balance.objects.get_or_create(user=user_receptor, defaults={'balance': Decimal('0.00')})
            balance.balance += amount
            balance.save()

        user_receptor_data = UserSerializer(user_receptor).data
        # Return transaction data
        return {
            'type': 'consignation',
            'id': transaction_.id,
            'user_receptor': user_receptor_data,
            'user_emisor': user_emisor,
            'amount': amount,
            'transaction_date': transaction_.transaction_date,
            'is_add': transaction_.is_add
        }

class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        user = self.context['request'].user
        balance = Balance.objects.filter(user=user).first()
        if not balance or balance.balance < data['amount']:
            raise serializers.ValidationError("Saldo insuficiente para el retiro.")
        return data

    def save(self):
        user = self.context['request'].user
        amount = self.validated_data['amount']
        with transaction.atomic():
            balance = Balance.objects.get(user=user)
            balance.balance -= amount
            balance.save()

            transaction_ = Transaction.objects.create(
                user_receptor=user,
                user_emisor=user,
                is_add=False,
                type = 'withdrawal',
                amount=amount
            )
            # Returns a tuple with the transaction object and the updated balance
            return transaction_, balance.balance  


class TransferSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        user = self.context['request'].user
        amount = data['amount']
        account_number = data['account_number']
        print(user)
       # Get balance from the issuer directly, without checking if it exists, since it is assumed that you have an account.
        sender_balance = Balance.objects.get(user=user)
        if sender_balance.balance < amount:
            print("if")
            raise serializers.ValidationError("Saldo insuficiente para realizar la transferencia.")

        # Verify existence of the receiving user by account number
        try:
            receiver = Customer.objects.get(account_number=account_number).user
        except Customer.DoesNotExist:
            raise serializers.ValidationError("El número de cuenta receptor no existe.")

        # Save the receiving user to use in the method save
        data['receiver'] = receiver
        return data

    def save(self):
        user_emisor = self.context['request'].user
        amount = self.validated_data['amount']
        user_receptor = self.validated_data['receiver']

        with transaction.atomic():
            # Update issuer balance
            sender_balance = Balance.objects.select_for_update().get(user=user_emisor)
            sender_balance.balance -= amount
            sender_balance.save()

            # Update receiver balance
            receiver_balance, created = Balance.objects.select_for_update().get_or_create(
                user=user_receptor, defaults={'balance': 0}
            )
            receiver_balance.balance += amount
            receiver_balance.save()
            
            # Get the issuer's document number
            customer_emisor = Customer.objects.get(user=user_emisor)

            # Record transaction to recipient
            transaction_receptor = Transaction.objects.create(
                user_receptor = user_receptor,
                user_emisor = customer_emisor.document_number,
                is_add = True,
                type = 'transfer_add',
                amount = amount
            )

            # Record transaction to issuer
            transaction_emisor = Transaction.objects.create(
                user_receptor = user_receptor,
                user_emisor = customer_emisor.document_number,
                is_add = False,
                type = 'transfer_out',
                amount = amount
            )
            return {
                'user_emisor': user_emisor.id,
                'user_receptor': user_receptor.id,
                'amount': amount,
                'balance': sender_balance.balance,
                'date': transaction_emisor.transaction_date
            }


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    transactions_consignation = serializers.SerializerMethodField()
    transactions_transfer = serializers.SerializerMethodField()
    transactions_withdrawal = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'full_name', 'document_type', 'document_number', 'account_number', 
            'balance', 'transactions_consignation', 'transactions_transfer', 
            'transactions_withdrawal'
        ]

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_balance(self, obj):
        balance = Balance.objects.get(user=obj.user)
        return balance.balance

    def get_transactions_consignation(self, obj):
        transactions = Transaction.objects.filter(user_receptor=obj.user, type='consignation')
        return TransactionListSerializer(transactions, many=True).data

    def get_transactions_transfer(self, obj):
        transactions = Transaction.objects.filter(user_receptor=obj.user, type__contains='transfer')
        return TransactionListSerializer(transactions, many=True).data

    def get_transactions_withdrawal(self, obj):
        transactions = Transaction.objects.filter(user_receptor=obj.user, type='withdrawal')
        return TransactionListSerializer(transactions, many=True).data
    

class TransactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['user_emisor', 'amount', 'transaction_date', 'type']

        
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({'username': self.user.username})
        data.update({'email': self.user.email})
        return data