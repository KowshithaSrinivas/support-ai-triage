# Login & Password Issues

## Resetting your password
1. Go to the login page and click "Forgot password".
2. Enter the email associated with your account.
3. Check your inbox (and spam folder) for a reset link, valid for 30 minutes.
4. Choose a new password with at least 8 characters, one number, and one symbol.

## "Invalid credentials" after a reset
This usually happens for one of these reasons:
- The reset link was used more than once (each link is single-use).
- There is a delay of up to 5 minutes for the new password to propagate across our auth servers.
- Caps Lock or a trailing space was accidentally included when typing the new password.

Recommended fix: ask the customer to wait 5 minutes and try again in an incognito/private browser window. If it still fails, manually trigger a password reset from the admin panel and confirm the account is not locked due to repeated failed attempts (5+ fails triggers a 15-minute lockout).

## Forgotten account email
If the customer doesn't remember which email they signed up with, search the customer database by name, partial name, or phone number if on file. Never confirm account existence or details to someone who cannot verify identity through at least two factors (e.g., name + last 4 digits of payment method, or name + billing address).
