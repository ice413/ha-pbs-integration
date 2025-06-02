from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
from .api import ProxmoxBackupAPI
from .coordinator import ProxmoxBackupDataUpdateCoordinator

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("pbs_host")
    token_id = entry.data.get("pbs_token_id")
    token = entry.data.get("pbs_token")
    update_interval = entry.options.get("update_interval", 60)

    api = ProxmoxBackupAPI(host, token_id, token)
    coordinator = ProxmoxBackupDataUpdateCoordinator(hass, api, update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)

