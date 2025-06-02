from datetime import timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import ProxmoxBackupAPI

_LOGGER = logging.getLogger(__name__)

class ProxmoxBackupDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: ProxmoxBackupAPI, update_interval: int):
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="ProxmoxBackupDataUpdateCoordinator",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        try:
            return await self.api.get_datastores()
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {e}")

