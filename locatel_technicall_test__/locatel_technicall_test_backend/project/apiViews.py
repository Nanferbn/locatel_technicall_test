from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Customer, Balance
from .serializers import *

class RegisterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new user instance.
        
        Args:
            request (Request): The request object containing user data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            Response: HTTP response object. Returns user data and success message on success,
                      or error message on failure.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': 'success',
                'code': status.HTTP_201_CREATED,
                'message': 'User successfully created',
                'data': serializer.data 
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    API endpoint that handles user login.
    """

    def post(self, request):
        """
        Handle user login.

        Args:
            request (Request): The request object containing user credentials.

        Returns:
            Response: HTTP response object. Returns success message and tokens on successful login,
                      or error message on failed login.
        """
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.get_tokens_for_user(user)
            return Response({
                "message": "Login successful",
                "tokens": tokens,
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Login failed",
                "errors": serializer.errors,
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        

class ConsignationAPI(APIView):
    """
    API endpoint for managing consignations.
    """

    def get(self, request):
        """
        Retrieve all balance records.

        Args:
            request (Request): The request object.

        Returns:
            Response: The list of all balance records with status code 200.
        """
        balances = Balance.objects.all()
        serializer = BalanceSerializer(balances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new consignation transaction.

        Args:
            request (Request): The request object containing consignation data.

        Returns:
            Response: HTTP response object. Returns success message and transaction data on successful consignation,
                      or error message on failed consignation.
        """
        serializer = ConsignationSerializer(data=request.data)
        if serializer.is_valid():
            transaction_data = serializer.save()
            return Response({
                'message': 'Consignation successful',
                'transaction': transaction_data.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WithdrawalAPI(APIView):
    """
    API endpoint that manages withdrawals for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle the withdrawal process for a user.

        Args:
            request (Request): The request object containing withdrawal data.

        Returns:
            Response: HTTP response object with status code 200 on successful withdrawal,
                      including transaction details, or with status code 400 on failure.
        """
        serializer = WithdrawalSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            transaction_, balance_amount = serializer.save()
            return Response({
                'message': 'Withdrawal successful.',
                'transaction_id': transaction_.id,
                'amount': transaction_.amount,
                'date': transaction_.transaction_date,
                'balance': balance_amount
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TransferAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = TransferSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            response_data = {
                "message": "Transferencia realizada con éxito",
                "user_emisor": result['user_emisor'],
                "user_receptor": result['user_receptor'],
                "amount_transferred": result['amount'],
                "emisor_balance": result['balance'],
                "transaction_date": result['date']
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TransferAPIView(APIView):
    """
    API endpoint that manages money transfers between users.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handle a request to transfer money from one user to another.

        Args:
            request (Request): The request object containing transfer details.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: HTTP response object with a status code 200 if the transfer is successful,
                      including detailed transaction information, or with status code 400 on failure.
        """
        serializer = TransferSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            response_data = {
                "message": "Transfer successful",
                "user_emisor": result['user_emisor'],
                "user_receptor": result['user_receptor'],
                "amount_transferred": result['amount'],
                "emisor_balance": result['balance'],
                "transaction_date": result['date']
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserProfileAPIView(APIView):
    """
    API endpoint for retrieving a user's profile.
    """
    permission_classes = [IsAuthenticated]  # Uncomment this to ensure the endpoint is secured

    def get(self, request):
        """
        Retrieve a specific customer's profile by their ID.

        Args:
            request (Request): The request object containing the user's credentials and the desired customer ID.

        Returns:
            Response: HTTP response object with a status code 200 if the profile is found,
                      or 404 if not found. The response includes the customer's profile data or an error message.
        """
        # Assuming the customer ID should be passed in the request; here we use a static ID for demonstration
        customer_id = request.query_params.get('id', 12)  # Get ID from query params or default to 12
        customer = Customer.objects.filter(id=customer_id).first()

        if not customer:
            return Response({"message": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(customer)
        return Response({"message": "User profile found.", "data": serializer.data}, status=status.HTTP_200_OK)
    
class MyTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT access and refresh tokens.

    This endpoint is used to obtain a new JWT access token pair (access and refresh)
    by providing valid user credentials.
    """
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to authenticate a user and return JWT access and refresh tokens.

        Args:
            request (Request): The request object containing user credentials.

        Returns:
            Response: A JSON object containing the JWT access and refresh tokens or error messages
                      if the authentication fails.
        """
        return super().post(request, *args, **kwargs)
