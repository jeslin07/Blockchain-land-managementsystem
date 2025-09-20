from django.shortcuts import render
from django.shortcuts import render, redirect

# Create your views here.
def index(request):
    return render(request, "index.html")

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import Customer
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render
from .utils import get_districts, get_price_info_fuzzy  # use fuzzy version
from django.shortcuts import  get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import *

def predict(request):
    result = None
    warning = None
    error = None

    if request.method == "POST":
        district = request.POST.get("district")
        locality = request.POST.get("locality")

        if district and locality:
            # Use fuzzy matching prediction
            per_cent, avg_total, fallback, matched_locality = get_price_info_fuzzy(district, locality)

            if per_cent is None:
                error = "❌ Could not predict price (district/locality not found)."
            else:
                result = {
                    "district": district,
                    "locality": matched_locality or locality,
                    "per_cent": f"₹{per_cent:,.0f}",   # changed name
                    "total_price": f"₹{avg_total:,.0f}",
                }
                if fallback and matched_locality:
                    warning = f"⚠️ Locality not found. Showing closest match: '{matched_locality}'"
                elif fallback:
                    warning = f"⚠️ Locality '{locality}' not found. Showing district average instead."
        else:
            error = "Please select a district and enter a locality."

    context = {
        "districts": get_districts(),
        "result": result,
        "warning": warning,
        "error": error,
    }
    return render(request, "predictor.html", context)

def customer_register(request):
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        adhar_no = request.POST.get('aadhar_number')
        phone_no = request.POST.get('phone')
        date_of_birth = request.POST.get('date_of_birth')
        pan_number = request.POST.get('pan_number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        # Validation
        if not all([full_name, email, password, confirm_password, adhar_no, phone_no, date_of_birth, pan_number, address, city, state, pincode]):
            messages.error(request, "All fields are required.")
        elif len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif len(adhar_no) != 12 or not adhar_no.isdigit():
            messages.error(request, "Aadhar number must be exactly 12 digits.")
        elif len(pan_number) != 10:
            messages.error(request, "PAN number must be exactly 10 characters.")
        elif len(pincode) != 6 or not pincode.isdigit():
            messages.error(request, "PIN code must be exactly 6 digits.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
        elif Customer.objects.filter(adhar_no=adhar_no).exists():
            messages.error(request, "This Aadhar number is already registered.")
        elif Customer.objects.filter(phone_no=phone_no).exists():
            messages.error(request, "This phone number is already registered.")
        else:
            try:
                # Split full name
                name_parts = full_name.strip().split()
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

                # Create User
                user = User.objects.create_user(
                    username=email,  # using email as username
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                # Assign Resident group
                assign_group(user, "Resident")

                # Create Customer linked to User
                Customer.objects.create(
                    user=user,
                    adhar_no=adhar_no,
                    phone_no=phone_no,
                    date_of_birth=date_of_birth,
                    pan_number=pan_number.upper(),
                    address=address,
                    city=city,
                    state=state,
                    pincode=pincode,
                    email=email
                )

                messages.success(request, f"🎉 Welcome {full_name}! Your account has been created successfully.")
                return redirect('customer_login')

            except Exception as e:
                messages.error(request, "An error occurred while creating your account.")
                print(f"Registration error: {e}")

    return render(request, 'customer_register.html')


def customer_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate using email (as username)
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Check if user has a linked Customer object
            try:
                customer = Customer.objects.get(user=user)
                login(request, user)
                request.session['customer_id'] = customer.id
                request.session['customer_name'] = f"{user.first_name} {user.last_name}".strip()
                messages.success(request, f"Welcome {request.session['customer_name']}!")
                return redirect('dashboard')
            except Customer.DoesNotExist:
                messages.error(request, "User exists but no Customer profile found.")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'customer_login.html')


# -----------------------------
# Customer Logout
# -----------------------------
def customer_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('customer_login')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

@login_required
def resident_dashboard(request):
    # Static data for demonstration (no database needed)
    context = {
        'name': request.user.get_full_name() or request.user.username or 'John Doe',
        'owned_properties_count': 3,
        'active_transactions_count': 2,
        'certificates_count': 5,
        'verified_docs_count': 8,
        'recent_activities': [
            {
                'action': 'Certificate Downloaded',
                'description': 'Land Certificate #LC2025001 downloaded successfully',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'action': 'Document Uploaded',
                'description': 'Sale deed documents uploaded for Transaction #TX2025003',
                'timestamp': datetime.now() - timedelta(hours=5)
            },
            {
                'action': 'Transaction Approved',
                'description': 'Land transfer transaction completed and verified on blockchain',
                'timestamp': datetime.now() - timedelta(days=1)
            },
            {
                'action': 'Property Valuation',
                'description': 'AI valuation completed for Parcel #PR2025007',
                'timestamp': datetime.now() - timedelta(days=2)
            }
        ]
    }
    return render(request, 'login_dashboard.html', context)

# Placeholder views for the URLs (return simple pages)
def view_properties(request):
    return render(request, 'coming_soon.html', {'feature': 'Property Management'})

def start_transaction(request):
    return render(request, 'coming_soon.html', {'feature': 'Start Transaction'})

def document_center(request):
    return render(request, 'coming_soon.html', {'feature': 'Document Center'})

def certificate_wallet(request):
    return render(request, 'coming_soon.html', {'feature': 'Certificate Wallet'})

def qr_verification(request):
    return render(request, 'coming_soon.html', {'feature': 'QR Verification'})

def property_valuation(request):
    return render(request, 'coming_soon.html', {'feature': 'Property Valuation'})

def transaction_timeline(request):
    return render(request, 'coming_soon.html', {'feature': 'Transaction Timeline'})

def help_center(request):
    return render(request, 'coming_soon.html', {'feature': 'Help & Chatbot'})

def customer_logout(request):
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    logout(request)
    return redirect('login')  # Adjust to your login URL name

@login_required
def admin_dashboard(request):
    users = User.objects.all().order_by("-date_joined")

    if request.method == "POST":   # Handle new user creation manually
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        office_location = request.POST.get("office_location")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        else:
            
            user=User.objects.create_user(username=username, email=email, password=password)
            try:
                SubRegistrar.objects.create(user=user, office_location=office_location)
                print(f"SubRegistrar {username} created successfully.")
            except Exception as e:
                messages.error(request, f"Error creating SubRegistrar: {e}")
                print(f"SubRegistrar creation error: {e}")
                return redirect("admin_dashboard")
            
            messages.success(request, f"User {username} created successfully!")
            return redirect("admin_dashboard")

    return render(request, "admin_dashboard.html", {"users": users})

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:   # only allow superusers
            login(request, user)
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid credentials or not an admin.")
    return render(request, "admin_login.html")

def view_properties(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "Please log in to view your properties")
        return redirect('customer_login')

    # customer = Customer.objects.get(id=customer_id)
    # properties = customer.properties.all()  # uses related_name="properties"

    return render(request, 'view_properties.html', {
        # 'customer': customer,
        # 'properties': properties
    })


@login_required
def register_land_ownership_change(request):
    if request.method == 'POST':
        survey_number = request.POST.get('survey_number')
        village = request.POST.get('village')
        district = request.POST.get('district')
        property_area_sqft = request.POST.get('property_area_sqft')
        property_value = request.POST.get('property_value')
        deed_type = request.POST.get('deed_type')
        previous_owner_name = request.POST.get('previous_owner_name')
        new_owner_name = request.POST.get('new_owner_name')

        # Create request
        ownership_request = LandOwnershipChangeRequest.objects.create(
            applicant=request.user,
            survey_number=survey_number,
            village=village,
            district=district,
            property_area_sqft=property_area_sqft,
            property_value=property_value,
            deed_type=deed_type,
            previous_owner_name=previous_owner_name,
            new_owner_name=new_owner_name,
            status=LandOwnershipChangeRequest.Status.SUBMITTED
        )

        # Save history
        RequestStatusHistory.objects.create(
            request=ownership_request,
            old_status="draft",
            new_status="submitted",
            changed_by=request.user,
            comments="Request submitted by applicant."
        )

        messages.success(request, "Ownership change request submitted successfully.")
        return redirect('my_requests')

    return render(request, 'register_request.html')


@login_required
def my_requests(request):
    #requests = LandOwnershipChangeRequest.objects.filter(applicant=request.user).order_by('-created_at')
    return render(request, 'my_request.html', {'requests': []})


@login_required
def request_detail(request, request_id):
    ownership_request = get_object_or_404(LandOwnershipChangeRequest, request_id=request_id, applicant=request.user)
    history = ownership_request.status_history.all()
    return render(request, 'request_detail.html', {
        'ownership_request': ownership_request,
        'history': history
    })
def register_subregistrar(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        office_location = request.POST.get("office_location")

        # Create User
        user = User.objects.create_user(username=username, email=email, password=password)

        # Create SubRegistrar linked to that user
        try:
            SubRegistrar.objects.create(user=user, office_location=office_location)
            print(f"SubRegistrar {username} created successfully.")
        except Exception as e:
            messages.error(request, f"Error creating SubRegistrar: {e}")
            print(f"SubRegistrar creation error: {e}")
            return redirect("admin_dashboard")

        messages.success(request, "SubRegistrar registered successfully!")

        return redirect("dashboard")

    return render(request, "admin_dashboard.html")