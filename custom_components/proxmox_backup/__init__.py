from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
from .api import ProxmoxBackupAPI
from .coordinator import ProxmoxBackupCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


# This function is called when the integration is set up via a config entry.
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("pbs_host")
    token_id = entry.data.get("pbs_token_id")
    token = entry.data.get("pbs_token")
    update_interval = entry.options.get("update_interval", entry.data.get("update_interval", 60))

    try:
        # Initialize the API and coordinator
        api = ProxmoxBackupAPI(host, token_id, token)
        coordinator = ProxmoxBackupCoordinator(hass, api, update_interval)
        await coordinator.async_config_entry_first_refresh()

        # Store the coordinator in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # Forward the entry setup to the sensor platform
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

        # Register the update listener
        entry.async_on_unload(entry.add_update_listener(update_listener))

        _LOGGER.info("Proxmox Backup integration successfully set up for host: %s", host)
        return True

    except Exception as e:
        _LOGGER.error("Failed to set up Proxmox Backup integration for host %s: %s", host, e)
        return False

# This function is called when the integration is unloaded or removed.
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

# This function is called when the config entry is updated.
async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)
