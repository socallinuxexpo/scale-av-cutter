import os, argparse, json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

def parse_args():
    parser = argparse.ArgumentParser(description="Obtains credentials for youtube separate from upload.py")

    parser.add_argument("-c", "--client", default="client_secrets.json", help="Path to client secrets file. Required if token is not valid (default: %(default)s)")
    parser.add_argument("-t", "--token", default="credentials.json", help="Path to authorization token file. If does not exist or invalid, this script will take you through the Google OAuth process (default: %(default)s)")
    parser.add_argument("--no-save-token", dest="save_token", action="store_false", help="Disable saving the authorization token to the path specified in (--token), after authorization.")
    return parser.parse_args()

def main():
    args = parse_args()

    if os.path.isfile(args.token):
        print(f"Found {args.token}, reusing credentials")
        credentials = obtain_credentials_from_token(args.token)
    else:
        print(f"Cannot find token file at {args.token}, starting authentication process")
        credentials = obtain_credentials_from_flow(args.client)
    if args.save_token:
        with open(args.token, "w") as f:
            json.dump({
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "refresh_token": credentials.refresh_token,
            }, f)

def obtain_credentials_from_flow(client_file):
    flow = InstalledAppFlow.from_client_secrets_file(
        client_file,
        scopes=['https://www.googleapis.com/auth/youtube.upload'])
    flow.run_local_server(bind_addr="0.0.0.0", open_browser=False, port=10000)
    return flow.credentials

def obtain_credentials_from_token(token_file):
    return Credentials.from_authorized_user_file(
        token_file,
        scopes=['https://www.googleapis.com/auth/youtube.upload'])

if __name__ == "__main__":
    main()
