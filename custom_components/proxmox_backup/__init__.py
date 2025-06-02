from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
from .api import ProxmoxBackupAPI
from .coordinator import ProxmoxBackupCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


# This function is called when the integration is set up via a config entry.
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("pbs_host")
    token_id = entry.data.get("pbs_token_id")
    token = entry.data.get("pbs_token")
    update_interval = entry.options.get("update_interval", 60)

    api = ProxmoxBackupAPI(host, token_id, token)
    coordinator = ProxmoxBackupCoordinator(hass, api, update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

# This function is called when the integration is unloaded or removed.
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

# This function is called when the config entry is updated.
async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)
