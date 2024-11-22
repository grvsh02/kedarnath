from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    profile_image = models.ImageField(upload_to="profile_images", null=True, blank=True)
    job_title = models.CharField(max_length=50, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_leaving = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    allowed_locations = models.ManyToManyField("Location", blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_profiles")
    hr = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="hr_profiles")

    def to_dict(self):
        return {
            "user": self.user.username,
            "phone": self.phone,
            "address": self.address,
            "job_title": self.job_title,
            "date_of_birth": self.date_of_birth,
            "date_of_joining": self.date_of_joining,
            "date_of_leaving": self.date_of_leaving,
            "salary": self.salary,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "manager": self.manager.username if self.manager else None,
            "hr": self.hr.username if self.hr else None,
        }


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
        }


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)
    check_in_message = models.CharField(max_length=500, null=True, blank=True)
    check_out_message = models.CharField(max_length=500, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    other_location = models.CharField(max_length=500, null=True, blank=True)

    def to_dict(self):
        return {
            "user": self.user.username,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "check_in_message": self.check_in_message,
            "check_out_message": self.check_out_message,
        }


class LeaveRequest(models.Model):
    status_choices = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=500)
    status = models.CharField(choices=status_choices, max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def to_dict(self):
        return {
            "user": self.user.username,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "reason": self.reason,
            "status": self.status,
        }


class Reimbursement(models.Model):
    status_choices = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    )
    type_choices = (
        ("food", "food"),
        ("travel", "travel"),
        ("accommodation", "accommodation"),
        ("medical", "medical"),
        ("telephone", "telephone"),
        ("other", "other"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=500, null=True, blank=True)
    type = models.CharField(choices=type_choices, max_length=50, default="other")
    expense_date = models.DateField()
    status = models.CharField(choices=status_choices, max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    receipt = models.ImageField(upload_to="receipts", null=True, blank=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.username,
            "amount": self.amount,
            "reason": self.reason,
            "status": self.status,
            "type": self.type,
            "expense_date": self.expense_date,
        }

class Payroll(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="payroll", null=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    reimbursement_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    final_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_final_salary(self):
        """
        Compute the final salary after applying breakups, reimbursements, and deductions.
        """
        self.final_salary = (
            self.basic_salary 
            + self.hra 
            + self.special_allowance 
            - self.tax_deduction 
            + self.reimbursement_amount
        )
        self.save()

    def to_dict(self):
        """
        Convert the Payroll object to a dictionary, including Profile details like username.
        """
        return {
            "employee": self.profile.user.username,  
            "basic_salary": self.basic_salary,
            "hra": self.hra,
            "special_allowance": self.special_allowance,
            "tax_deduction": self.tax_deduction,
            "reimbursement_amount": self.reimbursement_amount,
            "final_salary": self.final_salary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
