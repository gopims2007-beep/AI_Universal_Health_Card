from functools import lru_cache

from supabase import create_client

from app.core.config import settings


@lru_cache
def get_storage_client():
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


def upload_report(stored_filename: str, data: bytes, content_type: str) -> None:
    get_storage_client().storage.from_(settings.supabase_storage_bucket).upload(
        stored_filename,
        data,
        {"content-type": content_type, "upsert": "false"},
    )


def download_report(stored_filename: str) -> bytes:
    return get_storage_client().storage.from_(
        settings.supabase_storage_bucket
    ).download(stored_filename)


def delete_report(stored_filename: str) -> None:
    get_storage_client().storage.from_(settings.supabase_storage_bucket).remove(
        [stored_filename]
    )