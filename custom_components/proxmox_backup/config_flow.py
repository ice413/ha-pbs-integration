import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
from .api import ProxmoxBackupAPI

# Proxmox Backup Server integration for Home Assistant
# This code implements a configuration flow for connecting to a Proxmox Backup Server.
class ProxmoxBackupConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
# This class handles the configuration flow for the Proxmox Backup integration.
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input["pbs_host"]
            token_id = user_input["pbs_token_id"]
            token = user_input["pbs_token"]

            api = ProxmoxBackupAPI(host, token_id, token)
            try:
                await api.get_datastores()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Proxmox Backup ({host})",
                    data=user_input,
                )
            finally:
                await api.close()
# If the user input is not valid, show the form again with errors.
        data_schema = vol.Schema({
            vol.Required("pbs_host"): str,
            vol.Required("pbs_token_id"): str,
            vol.Required("pbs_token"): str,
            vol.Optional("update_interval", default=60): int,  # Default to 60 seconds
        })
# If there are errors, show the form with those errors.
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
