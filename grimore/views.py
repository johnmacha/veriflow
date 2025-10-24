from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from grimore.utils import send_otp
from django.utils import timezone
from django.core.mail import send_mail
from datetime import datetime, timedelta
import pyotp
from django.contrib.auth.models import User

# Create your views here.

def home(request):
    return render(request,'home.html',{'name':'John'})

def add(request):

    val1 = int(request.POST['num1'])
    val2 = int(request.POST['num2'])
    res = val1 + val2

    return render(request,'result.html',{'result':res})

def login_view(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
        # Store username in session
            request.session['username'] = username
        
        # Generate & send OTP to email
            send_otp(user, request)
 
        # generate OTP (to send via SMS/ email)
            otp_secret_key= request.session.get('otp_secret_key')
            totp = pyotp.TOTP(otp_secret_key, interval=30)
            print("DEBUG:OTP generated at login:", totp.now())

            return redirect('otp_view')
        else:
            error_message = 'Invalid username or password'
    return render(request, 'login.html', {'error_message': error_message})
        
def otp_view(request):
    error_message = None

    if request.method == 'POST':
        otp = request.POST['otp']
        print("User entered OTP:", otp)

        username = request.session.get('username') 
        otp_secret_key = request.session.get('otp_secret_key')
        otp_valid_date = request.session.get('otp_valid_date')

        print("Session values:", username, otp_secret_key, otp_valid_date)

        if not (otp_secret_key and otp_valid_date): 
            error_message = "OTP expired. Please request a new one."
        else:
            valid_date = datetime.fromisoformat(otp_valid_date)

            if datetime.now() > valid_date:
                error_message = "OTP expired. Please request a new one."
                #Optionally, generate a new OTP here and update session
            
            else:
                totp = pyotp.TOTP(otp_secret_key, interval=30)
                print("DEBUG: Expected OTP:", totp.now())

                if totp.verify(otp, valid_window=1):
                    user = get_object_or_404(User, username=username)
                    login(request, user)

                    request.session.pop('otp_secret_key', None)
                    request.session.pop('otp_valid_date', None)

                    return redirect('main_view')
                else:
                    error_message = 'Incorrect OTP. Try again'
   
    return render(request, 'otp.html', {'error_message':error_message,
     'otp_valid_date':request.session.get('otp_valid_date')
     })

def request_new_otp(request):
    username = request.session.get('username')
    if not username:
        messages.error(request, "Session expired. Please login again.")
        return redirect('login')
    
    user = get_object_or_404(User, username=username)

    #1. Check OTP request limit
    last_request = request.session.get('last_otp_request')
    request_count = request.session.get('otp_request_count', 0)
    now = timezone.now()

    print("last_request:", last_request)
    print("request_count before:", request_count)
    print("now:", now)

   

    if last_request:
        last_request_time = datetime.fromisoformat(last_request)

        # If last request was within 1 minute
        if now - last_request_time < timedelta(minutes=1):
            if request_count >= 3: # max 3 requests per minute
                messages.error(request, "Too many OTP requests. Please try again after 1 minute.")
                return redirect('otp_view')
            else:
                request_count += 1
        else:
            # Reset counter after 1 minute
            request_count = 1
    else:    
         # First request
        request_count = 1
    
    # Save back to session
    request.session['otp_request_count'] = request_count
    request.session['last_otp_request'] = now.isoformat()
    request.session.modified = True # Force save/ session update
        
    #2. Generate new OTP secret key and store in session
    otp_secret_key = pyotp.random_base32()
    otp_valid_date = datetime.now() + timedelta(seconds=30) #OTP valid for 5 minutes

    request.session['otp_secret_key'] = otp_secret_key
    request.session['otp_valid_date'] = otp_valid_date.isoformat()

    #Here you should send the OTP to user (email, SMS, etc.)
    totp = pyotp.TOTP(otp_secret_key, interval=30)
    otp = totp.now()

    #3. Send mail
    send_mail(
        subject="Your new OTP code",
        message=f"Your new OTP is {otp}. It expires in 30 seconds.",
        from_email=None, #uses DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent to your email!")
    return redirect('otp_view')

@login_required
def main_view(request):
    return render(request, 'main.html', {})

def logout_view(request):
    auth_logout(request)
    return redirect('login')