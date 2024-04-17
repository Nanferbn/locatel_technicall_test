# from rest_framework import routers
# from .apiViews import CustomerViewSet
# router = routers.DefaultRouter()

# router.register('customers', CustomerViewSet, basename='customers')

# urlpatterns = router.urls

# from django.urls import path
# from .apiViews import UserRegistrationViewSet

# urlpatterns = [
#     path('register/', UserRegistrationViewSet, name='user_registration'),
#     # Aquí puedes agregar más rutas para las vistas de tu aplicación 'project' si las tienes
# ]

# from django.urls import path, include
# from rest_framework import routers
# from .apiViews import UserRegistrationViewSet

# # Definimos un router
# router = routers.DefaultRouter()

# # Registramos la vista de registro de usuarios en el router
# router.register(r'register', UserRegistrationViewSet, basename='register')

# # Definimos las URLs de nuestra aplicación
# urlpatterns = [
#     path('', include(router.urls)),
#     # Aquí puedes agregar más URLs si es necesario
# ]

# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apiViews import LoginAPIView, RegisterViewSet, ConsignationAPI, WithdrawalAPI, TransferAPIView, UserProfileAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'register', RegisterViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('consignation/', ConsignationAPI.as_view(), name='consignation'),
    path('withdraw/', WithdrawalAPI.as_view(), name='withdrawal'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
    path('transfer/', TransferAPIView.as_view(), name='transfer'),
    path('profile/', UserProfileAPIView.as_view(), name='user_profile'),
]
