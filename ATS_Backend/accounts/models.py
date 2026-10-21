from django.db import models
from django.contrib.auth.models import User

class ResumeUpload(models.Model):
    
    user=models.ForeignKey(User,on_delete=models.CASCADE) 
    resume_file=models.FileField(upload_to='resumes/') 
    upload_at=models.DateTimeField(auto_now_add=True)   
    parse=models.BooleanField(default=False)  

    def __str__(self):
        return f"{self.user.username}-{self.resume_file.name}" 
    
    
class JDupload(models.Model):
    
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    Jd_file=models.FileField(upload_to='Jd/')
    upload_at=models.DateTimeField(auto_now_add=True)
    compare=models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}-{self.Jd_file}"

class History(models.Model):
    
    ACTION_CHOICES = [
        ("resume", "Resume Check"),
        ("job", "Job Match"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES) 

    score = models.DecimalField(max_digits=5, decimal_places=2)

    title = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    resume = models.ForeignKey(ResumeUpload, on_delete=models.SET_NULL, null=True, blank=True)
    jd = models.ForeignKey(JDupload, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} | {self.action} | {self.score}%"