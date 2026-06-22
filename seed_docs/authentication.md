# ShopFlow — Authentication

## Login

Customers authenticate with their email and password. A successful login returns
a bearer token that must be sent in the `Authorization` header on subsequent
requests.

## Token lifetime

Access tokens are valid for 24 hours. After expiry the client must log in again
to obtain a new token. ShopFlow does not currently issue refresh tokens.

## Password reset

A customer can request a password reset link by email. The link is valid for one
hour and can be used only once.
