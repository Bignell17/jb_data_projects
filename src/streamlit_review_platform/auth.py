import msal

from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORITY,
    REDIRECT_URI,
    SCOPES,
)


def build_msal_app():

    return msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )


def get_auth_url():

    app = build_msal_app()

    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )


def acquire_token(code):

    app = build_msal_app()

    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    return result
