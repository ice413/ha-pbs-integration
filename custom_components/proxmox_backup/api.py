import aiohttp

# Proxmox Backup API Client
# This module provides an asynchronous client for interacting with the Proxmox Backup Server API.

class ProxmoxBackupAPI:
    def __init__(self, host, token_id, token_secret):
        self.base_url = f"https://{host}/api2/json"
        self.headers = {
            "Authorization": f"PBSAPIToken={token_id}:{token_secret}"
        }
        self._session = None
#        self._verify_ssl = False  # Set to True if you want to verify SSL certificates
    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self.headers, connector=aiohttp.TCPConnector(ssl=False))
        return self._session

    async def _get_json(self, endpoint):
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_datastores(self):
        return await self._get_json("admin/datastore")

    async def get_datastore_status(self, store_name):
        return await self._get_json(f"admin/datastore/{store_name}/status")

    async def get_snapshots(self, store_name):
        return await self._get_json(f"admin/datastore/{store_name}/snapshots")

    async def get_gc_status(self):
        return await self._get_json("admin/gc")

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
