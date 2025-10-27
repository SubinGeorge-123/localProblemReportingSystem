from django.urls import path
from .views import dashboard, create_issue, update_issue, delete_issue

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('issue/create/', create_issue, name='create_issue'),
    path('issue/update/<int:issue_id>/', update_issue, name='update_issue'),
    path('issue/delete/<int:issue_id>/', delete_issue, name='delete_issue'),
]
