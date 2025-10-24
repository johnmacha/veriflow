import pyotp
from datetime import datetime, timedelta
from django.core.mail import send_mail

def send_otp(user, request):
    #totp - Time based One Time Passwords

    #Generate a new secret once per login
    otp_secret_key = request.session.get('otp_secret_key')
    if not otp_secret_key:
        otp_secret_key = pyotp.random_base32()
        request.session['otp_secret_key'] = otp_secret_key

    #Save expiry time (5mins)
    otp_valid_date = datetime.now() + timedelta(seconds=30)
    request.session['otp_valid_date'] = otp_valid_date.isoformat()

    #Generate OTP
    totp = pyotp.TOTP(otp_secret_key, interval=30)
    otp = totp.now()
   
    #Send OTP via EMAIL
    send_mail(
        'Your One Time Password (OTP)',
        f'Hello {user.username}, your OTP is: {otp}',
        'johmac002@gmail.com', #From
        [user.email], #To (user's email)
        fail_silently=False,
    )

    print(f"Your one time password is {otp}")


