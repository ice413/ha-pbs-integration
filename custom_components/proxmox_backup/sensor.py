from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .api import ProxmoxBackupAPI
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proxmox Backup sensors from a config entry."""

    host = entry.data.get("pbs_host")
    token_id = entry.data.get("pbs_token_id")
    token = entry.data.get("pbs_token")

    api = ProxmoxBackupAPI(host, token_id, token)

    sensors = []

    try:
        response = api.get_datastores()
        datastores = response.get("data", [])

        # Datastore usage sensors
        for ds in datastores:
            store_name = ds.get("store")
            if not store_name:
                continue

            usage_response = api.get_datastore_status(store_name)
            usage = usage_response.get("data", {})
            sensors.append(ProxmoxBackupSensor(store_name, usage))

        # Snapshot and GC logic stays the same
        snapshot_counts_per_node = {}
        snapshot_sizes_per_node = {}
        total_snapshots_count = 0
        total_snapshots_size = 0

        for ds in datastores:
            store_name = ds.get("store")
            if not store_name:
                continue

            try:
                snapshots_resp = api.get_snapshots(store_name)
                for snap in snapshots_resp.get("data", []):
                    backup_type = snap.get("backup-type")
                    backup_id = snap.get("backup-id")
                    size = snap.get("size", 0)
                    if not backup_type or not backup_id:
                        continue

                    key = (backup_type, backup_id)
                    snapshot_counts_per_node[key] = snapshot_counts_per_node.get(key, 0) + 1
                    snapshot_sizes_per_node[key] = snapshot_sizes_per_node.get(key, 0) + size

                    total_snapshots_count += 1
                    total_snapshots_size += size

            except Exception as e:
                _LOGGER.warning("Failed to get snapshots for %s: %s", store_name, e)

        for (backup_type, backup_id), count in snapshot_counts_per_node.items():
            size_bytes = snapshot_sizes_per_node.get((backup_type, backup_id), 0)
            sensors.append(ProxmoxSnapshotSensorPerNode(backup_type, backup_id, count, size_bytes))

        sensors.append(ProxmoxSnapshotTotalSensor(total_snapshots_count, total_snapshots_size))

        try:
            gc_data = api.get_gc_status()
            for gc_entry in gc_data.get("data", []):
                store = gc_entry.get("store")
                if not store:
                    continue
                sensors.append(ProxmoxBackupGCSensor(store, gc_entry))
        except Exception as e:
            _LOGGER.warning("Failed to get GC status: %s", e)

    except Exception as e:
        _LOGGER.error("Error setting up Proxmox sensors: %s", e)
        return

    async_add_entities(sensors)


class ProxmoxBackupSensor(Entity):
    def __init__(self, name, usage):
        self._name = name
        self._used = usage.get("used", 0)
        self._total = usage.get("total", 0)
        self._avail = usage.get("avail", 0)

    @property
    def name(self):
        return f"Proxmox Backup {self._name} Usage"

    @property
    def unique_id(self):
        return f"proxmox_backup_usage_{self._name}"

    @property
    def state(self):
        return self._used

    @property
    def extra_state_attributes(self):
        return {
            "used_bytes": self._used,
            "total_bytes": self._total,
            "available_bytes": self._avail,
            "used_percent": round((self._used / self._total) * 100, 2) if self._total else None,
            "free_percent": round((self._avail / self._total) * 100, 2) if self._total else None,
        }

    @property
    def device_class(self):
        return "data_size"

    @property
    def unit_of_measurement(self):
        return "bytes"

    @property
    def icon(self):
        return "mdi:harddisk"


class ProxmoxSnapshotSensorPerNode(Entity):
    def __init__(self, backup_type, backup_id, count, size_bytes):
        self._backup_type = backup_type
        self._backup_id = backup_id
        self._count = count
        self._size_bytes = size_bytes

    @property
    def name(self):
        return f"Proxmox Backup {self._backup_type}/{self._backup_id} Snapshots"

    @property
    def unique_id(self):
        return f"proxmox_backup_{self._backup_type}_{self._backup_id}_snapshots"

    @property
    def state(self):
        return self._count

    @property
    def extra_state_attributes(self):
        return {
            "backup_type": self._backup_type,
            "backup_id": self._backup_id,
            "snapshot_count": self._count,
            "total_snapshot_size_bytes": self._size_bytes,
            "total_snapshot_size_human": self._human_readable_size(self._size_bytes),
        }

    @property
    def icon(self):
        return "mdi:backup-restore"

    @property
    def device_class(self):
        return "count"

    @property
    def unit_of_measurement(self):
        return "snapshots"

    def _human_readable_size(self, size, decimal_places=2):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024
        return f"{size:.{decimal_places}f} PB"


class ProxmoxSnapshotTotalSensor(Entity):
    def __init__(self, total_count, total_size_bytes):
        self._total_count = total_count
        self._total_size_bytes = total_size_bytes

    @property
    def name(self):
        return "Proxmox Backup Total Snapshots"

    @property
    def unique_id(self):
        return "proxmox_backup_total_snapshots"

    @property
    def state(self):
        return self._total_count

    @property
    def extra_state_attributes(self):
        return {
            "total_snapshot_count": self._total_count,
            "total_snapshot_size_bytes": self._total_size_bytes,
            "total_snapshot_size_human": self._human_readable_size(self._total_size_bytes),
        }

    @property
    def icon(self):
        return "mdi:backup-restore"

    @property
    def device_class(self):
        return "count"

    @property
    def unit_of_measurement(self):
        return "snapshots"

    def _human_readable_size(self, size, decimal_places=2):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024
        return f"{size:.{decimal_places}f} PB"


class ProxmoxBackupGCSensor(Entity):
    def __init__(self, store, gc_data):
        self._store = store
        self._gc_data = gc_data

    @property
    def name(self):
        return f"Proxmox Backup GC Status {self._store}"

    @property
    def unique_id(self):
        return f"proxmox_backup_gc_status_{self._store.lower()}"

    @property
    def state(self):
        return self._gc_data.get("last-run-state", "unknown")

    @property
    def extra_state_attributes(self):
        dedup_factor = self._calculate_dedup_factor()
        return {
            "store": self._store,
            "last_run_endtime": self._format_timestamp(self._gc_data.get("last-run-endtime")),
            "next_run": self._format_timestamp(self._gc_data.get("next-run")),
            "removed_bytes": self._gc_data.get("removed-bytes"),
            "removed_chunks": self._gc_data.get("removed-chunks"),
            "index_data_bytes": self._gc_data.get("index-data-bytes"),
            "disk_bytes": self._gc_data.get("disk-bytes"),
            "deduplication_factor": dedup_factor,
        }

    def _format_timestamp(self, ts):
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(ts).isoformat()
        except Exception:
            return str(ts)

    def _calculate_dedup_factor(self):
        index_data = self._gc_data.get("index-data-bytes", 0)
        disk_data = self._gc_data.get("disk-bytes", 1)
        return round(index_data / disk_data, 2) if disk_data else None

    @property
    def icon(self):
        return "mdi:recycle"

