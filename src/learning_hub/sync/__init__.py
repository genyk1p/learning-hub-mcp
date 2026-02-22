"""Sync provider dispatch registry.

Maps SyncProviderType enum values to handler functions.
Each handler has the signature:
    async def handler(session, provider) -> ProviderSyncResult
"""

from learning_hub.models.enums import SyncProviderType
from learning_hub.sync.edupage import run_edupage_sync
from learning_hub.sync.pronote import run_pronote_sync

SYNC_HANDLERS = {
    SyncProviderType.EDUPAGE: run_edupage_sync,
    SyncProviderType.PRONOTE: run_pronote_sync,
}
