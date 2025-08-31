# Debugging Swift App Error Handling

## Problem Description

The Swift app is displaying the `networkError` message from `AuthErrorConstants.swift` instead of the actual error messages from the Django API.

## Root Cause Analysis

The issue is likely in one of these areas:

1. **API Response Structure Mismatch**: The Django API might not be returning errors in the expected format
2. **Swift Error Parsing**: The `createAuthError` method might not be parsing the API response correctly
3. **Network Error Handling**: The `NetworkManager` might be catching errors before they reach the Swift error handler

## Debugging Steps

### Step 1: Test Django API Error Responses

Run the debug script to verify Django API error responses:

```bash
cd shuttrly
python manage.py shell < users/api/debug_api_errors.py
```

**Expected Output Structure:**
```json
{
  "success": false,
  "error": {
    "code": "AUTH_301",
    "message": "Please check your input and try again.",
    "type": "authentication_error",
    "details": {
      "validation_errors": {
        "email": ["Enter a valid email address."]
      }
    }
  }
}
```

### Step 2: Check Swift App Logs

Run the Swift app and check the console logs for these debug messages:

```
🔍 createAuthError called with: [response data]
🔍 Response type: [type]
🔍 Response is a dictionary: [dictionary]
🔍 Response keys: [keys]
🔍 Found error dictionary: [error dict]
🔍 Error keys: [error keys]
```

### Step 3: Verify Network Error Flow

Check if the error is reaching the Swift app as `NetworkError.apiError` or if it's being caught earlier.

## Common Issues and Solutions

### Issue 1: Django API Not Using AuthErrorResponse

**Problem**: Django views are returning `Response` objects instead of `AuthErrorResponse`

**Solution**: Ensure all error responses use `AuthErrorResponse` methods:

```python
# ❌ Wrong
return Response({
    'success': False,
    'message': 'Invalid email'
}, status=status.HTTP_400_BAD_REQUEST)

# ✅ Correct
return AuthErrorResponse.validation_error({
    'email': ['Invalid email format']
})
```

### Issue 2: Swift Error Parsing Fails

**Problem**: The `createAuthError` method can't parse the API response

**Solution**: Check the response structure in Swift logs and ensure it matches the expected format.

### Issue 3: Network Manager Catching Errors

**Problem**: `NetworkManager` is throwing generic errors instead of `NetworkError.apiError`

**Solution**: Ensure `NetworkManager` properly handles HTTP 400 responses and throws `NetworkError.apiError`.

## Testing Checklist

- [ ] Django API returns proper error structure
- [ ] Swift app receives `NetworkError.apiError`
- [ ] `createAuthError` method parses response correctly
- [ ] `AuthError` object is created with correct message
- [ ] UI displays the correct error message

## Quick Fix Commands

### Test Django API
```bash
cd shuttrly
python manage.py shell < users/api/debug_api_errors.py
```

### Check Django Server Logs
```bash
# Look for error responses in Django console
```

### Test Swift App
1. Run the app
2. Try to login with invalid credentials
3. Check console logs for debug messages
4. Verify error message displayed

## Expected Error Flow

1. **Django API** → Returns structured error response
2. **NetworkManager** → Catches HTTP 400+ and throws `NetworkError.apiError`
3. **AuthService** → Receives `NetworkError.apiError` and calls `createAuthError`
4. **createAuthError** → Parses response and creates `AuthError`
5. **UI** → Displays `AuthError.message`

## Debug Commands

### Django Shell
```python
from django.test import Client
client = Client()
response = client.post('/api/v1/auth/login/', 
                      data='{"identifier": "test", "password": "wrong"}',
                      content_type='application/json')
print(response.status_code)
print(response.content.decode())
```

### Swift Console
Look for these log patterns:
- `🔍 createAuthError called with:`
- `✅ Parsed structured error`
- `❌ Could not parse error response`

## Next Steps

1. Run the debug script to verify Django API
2. Check Swift app logs for error parsing
3. Identify where the error flow breaks
4. Fix the specific issue (Django API or Swift parsing)
5. Test the complete error flow
