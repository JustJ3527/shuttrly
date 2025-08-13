# Password Reset Functionality

## Overview

This document describes the password reset functionality implemented in the Shuttrly Django application. The system allows users to securely reset their passwords through email verification.

## Features

- **Secure Password Reset**: Uses Django's built-in password reset views with custom templates
- **Email Verification**: Sends secure reset links via email
- **Token Expiration**: Reset links expire after 24 hours for security
- **Responsive Design**: Templates match the existing application design
- **User-Friendly**: Clear error messages and step-by-step guidance

## URL Structure

```
/password-reset/                    → Request password reset
/password-reset/done/              → Confirmation email sent
/password-reset/confirm/<uid>/<token>/ → Set new password
/password-reset/complete/          → Password reset successful
```

## Templates

### Main Templates

- `password_reset.html` - Initial password reset request form
- `password_reset_done.html` - Confirmation that email was sent
- `password_reset_confirm.html` - Form to enter new password
- `password_reset_complete.html` - Success confirmation

### Email Templates

- `password_reset_email.html` - HTML email with reset link
- `password_reset_subject.txt` - Email subject line

## Security Features

1. **Unique Tokens**: Each reset request generates a unique, secure token
2. **Time Expiration**: Tokens expire after 24 hours
3. **Single Use**: Each token can only be used once
4. **Email Validation**: Only registered email addresses can request resets
5. **CSRF Protection**: All forms include CSRF tokens

## User Flow

1. **Request Reset**: User clicks "Forgot your password?" on login page
2. **Enter Email**: User enters their registered email address
3. **Email Sent**: System sends reset link with secure token
4. **Click Link**: User clicks link in email (valid for 24 hours)
5. **Set Password**: User enters and confirms new password
6. **Success**: Password is updated and user can log in

## Implementation Details

### Views Used

- `PasswordResetView` - Handles initial reset request
- `PasswordResetDoneView` - Shows confirmation page
- `PasswordResetConfirmView` - Handles password change
- `PasswordResetCompleteView` - Shows success page

### Forms

- Uses Django's built-in `PasswordResetForm`
- Custom validation and error handling
- Responsive design matching existing UI

### Styling

- Consistent with existing application design
- Uses `users.css` for styling
- Responsive layout for all devices
- FontAwesome icons for visual appeal

## Configuration

### Settings Required

- `EMAIL_BACKEND` - Configured for sending emails
- `EMAIL_HOST` - SMTP server configuration
- `EMAIL_PORT` - SMTP port (usually 587 or 465)
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password
- `EMAIL_USE_TLS` - Enable TLS encryption

### URL Configuration

```python
# In users/urls.py
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name="users/password_reset.html",
        email_template_name="users/emails/password_reset_email.html",
        subject_template_name="users/emails/password_reset_subject.txt",
        success_url="/password-reset/done/",
    ), name="password_reset"),
    # ... other URLs
]
```

## Testing

### Manual Testing

1. Navigate to login page
2. Click "Forgot your password?"
3. Enter valid email address
4. Check email for reset link
5. Click link and set new password
6. Verify login works with new password

### Automated Testing

Run the test script:

```bash
python test_password_reset.py
```

## Troubleshooting

### Common Issues

1. **Email Not Sent**

   - Check SMTP configuration
   - Verify email backend settings
   - Check server logs for errors

2. **Reset Link Not Working**

   - Verify token hasn't expired (24 hours)
   - Check URL configuration
   - Ensure templates are in correct location

3. **Template Errors**
   - Verify template paths in URL configuration
   - Check template syntax
   - Ensure all required templates exist

### Debug Mode

Enable Django debug mode to see detailed error messages:

```python
DEBUG = True
```

## Future Enhancements

- **Rate Limiting**: Prevent abuse of reset requests
- **SMS Verification**: Add SMS as alternative to email
- **Security Questions**: Additional verification steps
- **Audit Logging**: Track password reset attempts
- **Custom Expiration**: Configurable token expiration times

## Security Considerations

- Reset links should never be logged
- Tokens should be cryptographically secure
- Email delivery should be reliable
- Failed attempts should be monitored
- Consider implementing CAPTCHA for high-traffic sites

## Support

For issues or questions regarding the password reset functionality:

1. Check Django documentation
2. Review server logs
3. Test with different email providers
4. Verify configuration settings
