from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class ProxmoxBackupOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        update_interval = options.get("update_interval", 60)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("update_interval", default=update_interval): int,
            }),
        )

