"""Interactive FYERS login; keep credentials in the operating system keyring."""

from __future__ import annotations

import getpass
import webbrowser

import keyring
from fyers_apiv3 import fyersModel

from .fyers_data import SERVICE


def setup() -> None:
    client_id = input("FYERS App ID: ").strip()
    secret = getpass.getpass("FYERS App Secret (hidden): ").strip()
    redirect_uri = input(
        "Redirect URL [https://trade.fyers.in/api-login/redirect-uri/index.html]: "
    ).strip()
    if not redirect_uri:
        redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
    if not client_id or not secret:
        raise SystemExit("App ID and App Secret are required.")
    keyring.set_password(SERVICE, "client_id", client_id)
    keyring.set_password(SERVICE, "client_secret", secret)
    keyring.set_password(SERVICE, "redirect_uri", redirect_uri)
    print("App credentials saved in the operating system credential store.")


def login() -> None:
    client_id = keyring.get_password(SERVICE, "client_id")
    secret = keyring.get_password(SERVICE, "client_secret")
    redirect_uri = keyring.get_password(SERVICE, "redirect_uri")
    if not client_id or not secret or not redirect_uri:
        raise SystemExit("Run setup first.")

    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code",
    )
    auth_url = session.generate_authcode()
    if not isinstance(auth_url, str) or not auth_url.startswith("http"):
        raise SystemExit("FYERS did not return a login URL; check the SDK response.")
    print("Opening FYERS login. Sign in, then copy only auth_code from the redirect URL.")
    webbrowser.open(auth_url)
    auth_code = getpass.getpass("Paste auth_code (input hidden): ").strip()
    if not auth_code:
        raise SystemExit("No auth_code provided.")
    session.set_token(auth_code)
    result = session.generate_token()
    if not isinstance(result, dict) or result.get("s") != "ok" or not result.get("access_token"):
        raise SystemExit("FYERS authentication failed. Check the code and try a fresh login.")
    keyring.set_password(SERVICE, "access_token", result["access_token"])
    print("FYERS login succeeded. Today's access token is stored in the OS credential store.")


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("setup", "login"))
    args = parser.parse_args(argv)
    try:
        setup() if args.action == "setup" else login()
        return 0
    except Exception as exc:
        print(f"FYERS AUTH FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
