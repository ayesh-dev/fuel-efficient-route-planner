from django.urls import path
from .views import CalculateFuelRouteView

urlpatterns = [
    path('find-route/', CalculateFuelRouteView.as_view(), name='find-route'),
]