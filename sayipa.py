#!/usr/bin/env python3

import argparse
import pathlib
import subprocess
import sys
from urllib import request

import boto3


REGION = "us-west-2"
POOL_ID = "us-west-2:42521701-f77a-4555-8b1c-e160ad0210da"
REFERER = "https://ipa-reader.com/"


def build_signed_url(ipa_text: str, voice_id: str) -> str:
    cog = boto3.client("cognito-identity", region_name=REGION)
    identity_id = cog.get_id(IdentityPoolId=POOL_ID)["IdentityId"]
    creds = cog.get_credentials_for_identity(IdentityId=identity_id)["Credentials"]

    polly = boto3.client(
        "polly",
        region_name=REGION,
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretKey"],
        aws_session_token=creds["SessionToken"],
    )

    ssml = f"<phoneme alphabet='ipa' ph='{ipa_text}'></phoneme>"
    return polly.generate_presigned_url(
        "synthesize_speech",
        Params={
            "OutputFormat": "mp3",
            "SampleRate": "16000",
            "Text": ssml,
            "TextType": "ssml",
            "VoiceId": voice_id,
        },
        ExpiresIn=3600,
        HttpMethod="GET",
    )


def download_audio(url: str, output_path: pathlib.Path) -> None:
    req = request.Request(url, headers={"Referer": REFERER})
    with request.urlopen(req) as resp:
        data = resp.read()
    output_path.write_bytes(data)


def play_audio(output_path: pathlib.Path) -> None:
    subprocess.run(["afplay", str(output_path)], check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read IPA text aloud via IPA Reader's Polly flow."
    )
    parser.add_argument("ipa", help="IPA text, e.g. [həˈloʊ]")
    parser.add_argument("--voice", default="Salli", help="Polly voice id")
    parser.add_argument("--out", default="/tmp/ipa.mp3", help="Output MP3 path")
    parser.add_argument(
        "--no-play", action="store_true", help="Generate MP3 without playing it"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_path = pathlib.Path(args.out)

    try:
        url = build_signed_url(args.ipa, args.voice)
        download_audio(url, out_path)
        if not args.no_play:
            play_audio(out_path)
    except Exception as exc:
        print(f"sayipa error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
