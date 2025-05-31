import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from .const import DOMAIN

# Optional: import your API to test login
from .api import ProxmoxBackupAPI

class ProxmoxBackupConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proxmox Backup."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input["pbs_host"]
            token_id = user_input["pbs_token_id"]
            token = user_input["pbs_token"]

            # Optional: Validate connection
            try:
                api = ProxmoxBackupAPI(host, token_id, token)
                await self.hass.async_add_executor_job(api.get_datastores)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Proxmox Backup ({host})", data=user_input
                )

        data_schema = vol.Schema({
            vol.Required("pbs_host"): str,
            vol.Required("pbs_token_id"): str,
            vol.Required("pbs_token"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
