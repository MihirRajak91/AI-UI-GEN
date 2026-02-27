import os

import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse

DEFAULT_CLAUDE_MODEL = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
_MODEL_ALIASES = {
    "sonnet 4.5": DEFAULT_CLAUDE_MODEL,
    "sonnet-4.5": DEFAULT_CLAUDE_MODEL,
    "claude sonnet 4.5": DEFAULT_CLAUDE_MODEL,
    "claude-sonnet-4.5": DEFAULT_CLAUDE_MODEL,
    "sonnet 4.6": "global.anthropic.claude-sonnet-4-6",
    "sonnet-4.6": "global.anthropic.claude-sonnet-4-6",
    "claude sonnet 4.6": "global.anthropic.claude-sonnet-4-6",
    "claude-sonnet-4.6": "global.anthropic.claude-sonnet-4-6",
    "haiku 4.5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "haiku-4.5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude haiku 4.5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-haiku-4.5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
}


def _first_non_empty(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value is not None:
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _resolve_model_name(model_name: str | None) -> str:
    configured_model = (
        os.getenv("BEDROCK_MODEL_ID")
        or os.getenv("ANTHROPIC_BEDROCK_MODEL")
        or ""
    ).strip()
    raw = (model_name or "").strip()

    if not raw:
        target = configured_model or DEFAULT_CLAUDE_MODEL
    elif raw == DEFAULT_CLAUDE_MODEL and configured_model:
        target = configured_model
    else:
        target = raw

    return _MODEL_ALIASES.get(target.lower(), target)


def build_chat_model(
    model_name: str = DEFAULT_CLAUDE_MODEL,
    temperature: float = 0,
) -> ChatBedrockConverse:
    load_dotenv()
    profile = _first_non_empty("AWS_PROFILE", "aws_profile")
    access_key = _first_non_empty("AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY", "aws_access_key")
    secret_key = _first_non_empty("AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY", "aws_secret_key")
    session_token = _first_non_empty("AWS_SESSION_TOKEN", "aws_session_token")
    region = _first_non_empty(
        "BEDROCK_AWS_REGION",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "aws_region",
    ) or "us-east-1"
    resolved_model = _resolve_model_name(model_name)

    if access_key and secret_key:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name=region,
        )
    elif profile:
        session = boto3.Session(profile_name=profile, region_name=region)
    else:
        session = boto3.Session(region_name=region)

    if session.get_credentials() is None:
        raise RuntimeError(
            "AWS credentials were not found. Set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY "
            "(or aws_access_key/aws_secret_key), plus optional AWS_SESSION_TOKEN, "
            "or configure AWS_PROFILE."
        )

    kwargs = {
        "model": resolved_model,
        "region_name": region,
        "temperature": temperature,
    }
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
        if session_token:
            kwargs["aws_session_token"] = session_token
    elif profile:
        kwargs["credentials_profile_name"] = profile

    return ChatBedrockConverse(**kwargs)
