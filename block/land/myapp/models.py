from django.db import models
from django.contrib.auth.models import User, Group
import uuid
from django.utils import timezone


def assign_group(user, group_name):
    """Assign a user to a Django group (Resident or Office)"""
    group, created = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    adhar_no = models.CharField(max_length=12, unique=True)
    phone_no = models.CharField(max_length=15, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def group(self):
        return "Resident"


class SubRegistrarOffice(models.Model):
    """Office where land transactions are registered"""
    office_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    office_name = models.CharField(max_length=200)
    district = models.CharField(max_length=50)
    taluk = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.office_name} - {self.district}"

class SubRegistrar(models.Model):
    """Represents a sub-registrar linked to a user and office"""
    registrar_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office_location = models.CharField(max_length=255) 
    
    def __str__(self):
        return f"{self.user.username} - {self.office_location}"


class LandOwnershipChangeRequest(models.Model):
    """Main request for land ownership change"""

    class DeedType(models.TextChoices):
        SALE = 'sale', 'Sale Deed'
        GIFT = 'gift', 'Gift Deed'
        PARTITION = 'partition', 'Partition Deed'
        LEASE = 'lease', 'Lease Deed'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='land_requests')

    # Property details
    survey_number = models.CharField(max_length=50)
    village = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    property_area_sqft = models.DecimalField(max_digits=10, decimal_places=2)
    property_value = models.DecimalField(max_digits=15, decimal_places=2)

    # Transaction details
    deed_type = models.CharField(max_length=20, choices=DeedType.choices)
    previous_owner_name = models.CharField(max_length=200)
    new_owner_name = models.CharField(max_length=200)

    # Processing
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    assigned_sub_registrar = models.ForeignKey(
        SubRegistrar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.status == self.Status.SUBMITTED and not self.submitted_at:
            self.submitted_at = timezone.now()
        elif self.status == self.Status.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Request {str(self.request_id)[:8]} - {self.deed_type} - {self.village}"


class RequestStatusHistory(models.Model):
    """Audit trail for request status changes"""
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        LandOwnershipChangeRequest,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=25)
    new_status = models.CharField(max_length=25)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"History {self.request} {self.old_status} → {self.new_status}"
