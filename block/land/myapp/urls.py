from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.customer_register, name='customer_register'),
    path('login/', views.customer_login, name='customer_login'),
    path('dashboard/', views.resident_dashboard, name='dashboard'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('properties/', views.view_properties, name='view_properties'),
    path('transaction/start/', views.start_transaction, name='start_transaction'),
    path('documents/', views.document_center, name='document_center'),
    path('certificates/', views.certificate_wallet, name='certificate_wallet'),
    path('verify/', views.qr_verification, name='qr_verification'),
    path('valuation/', views.property_valuation, name='property_valuation'),
    path('timeline/', views.transaction_timeline, name='transaction_timeline'),
    path('help/', views.help_center, name='help_center'),
    path("adminlogin/", views.admin_login, name="admin_login"),
    path("admindashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("prediction/", views.predict, name="prediction"),
    path('properties/', views.view_properties, name='view_properties'),
    path("register/", views.register_land_ownership_change, name="register_land_ownership_change"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("my-requests/<uuid:request_id>/", views.request_detail, name="request_detail"),
    



]