from django.db import models
from django.contrib.auth.models import User

class Issue(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    CATEGORY_CHOICES = [
        ('Roads', 'Roads'),
        ('Sanitation', 'Sanitation'),
        ('Electricity', 'Electricity'),
        ('Water Supply', 'Water Supply'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'), 
    ]
  
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_name = models.CharField(max_length=200)
    street_no = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Low')
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Roads')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issue_name} - {self.status}"
