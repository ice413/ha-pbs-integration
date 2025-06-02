import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class ProxmoxBackupCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, update_interval):
        """Initialize coordinator."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="Proxmox Backup Server",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Fetch data from the Proxmox Backup Server API."""

        try:
            datastores_resp = await self.api.get_datastores()
            datastores = datastores_resp.get("data", [])

            usage_data = {}
            snapshots = []
            gc_data = []

            # Gather usage info for each datastore
            for ds in datastores:
                store_name = ds.get("store")
                if not store_name:
                    continue

                usage_resp = await self.api.get_datastore_status(store_name)
                usage = usage_resp.get("data", {})
                usage_data[store_name] = usage

                # Gather snapshots for each datastore
                snapshots_resp = await self.api.get_snapshots(store_name)
                snapshots.extend(snapshots_resp.get("data", []))

            # Get GC status
            gc_resp = await self.api.get_gc_status()
            gc_data = gc_resp.get("data", [])

            return {
                "usage": usage_data,
                "snapshots": snapshots,
                "gc": gc_data,
            }

        except Exception as err:
            _LOGGER.error("Error fetching data from Proxmox Backup Server: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}")

