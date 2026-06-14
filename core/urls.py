from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("verify/", views.place_order, name="place_order"),
    path("order/<str:reference>/", views.order_result, name="order_result"),
]
