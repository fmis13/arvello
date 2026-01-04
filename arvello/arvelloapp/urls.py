from django.urls import path
from . import views

urlpatterns = [
    path('subjects/', views.SubjectListView.as_view(), name='subjects'),
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject-create'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject-update'),
    path('subjects/switch/', views.switch_subject, name='subject-switch'),
]
