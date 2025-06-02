import logging
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import ProxmoxBackupDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ProxmoxBackupDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    # Datastore usage sensors
    for ds in coordinator.data.get("data", []):
        store_name = ds.get("store")
        if store_name:
            sensors.append(ProxmoxBackupSensor(coordinator, store_name))

    # Snapshot and GC sensors
    try:
        snapshot_counts = {}
        snapshot_sizes = {}
        total_count = 0
        total_size = 0

        for ds in coordinator.data.get("data", []):
            store_name = ds.get("store")
            if not store_name:
                continue
            snapshots = await coordinator.api.get_snapshots(store_name)
            for snap in snapshots.get("data", []):
                btype = snap.get("backup-type")
                bid = snap.get("backup-id")
                size = snap.get("size", 0)
                if not btype or not bid:
                    continue
                key = (btype, bid)
                snapshot_counts[key] = snapshot_counts.get(key, 0) + 1
                snapshot_sizes[key] = snapshot_sizes.get(key, 0) + size
                total_count += 1
                total_size += size

        for (btype, bid), count in snapshot_counts.items():
            sensors.append(ProxmoxSnapshotSensorPerNode(coordinator, btype, bid, count, snapshot_sizes[(btype, bid)]))

        sensors.append(ProxmoxSnapshotTotalSensor(coordinator, total_count, total_size))

    except Exception as e:
        _LOGGER.warning("Snapshot sensor setup failed: %s", e)

    try:
        gc_data = await coordinator.api.get_gc_status()
        for entry in gc_data.get("data", []):
            store = entry.get("store")
            if store:
                sensors.append(ProxmoxBackupGCSensor(coordinator, store, entry))
    except Exception as e:
        _LOGGER.warning("GC sensor setup failed: %s", e)

    async_add_entities(sensors)

# ------------------ SENSOR CLASSES ------------------

class ProxmoxBackupSensor(Entity):
    def __init__(self, coordinator, name):
        self.coordinator = coordinator
        self._name = name
        self._state = None
        self._attrs = {}
        self.update_from_data()

    @property
    def name(self):
        return f"Proxmox Backup {self._name} Usage"

    @property
    def unique_id(self):
        return f"proxmox_backup_usage_{self._name}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def device_class(self):
        return "data_size"

    @property
    def unit_of_measurement(self):
        return "bytes"

    @property
    def icon(self):
        return "mdi:harddisk"

    def update_from_data(self):
        for ds in self.coordinator.data.get("data", []):
            if ds.get("store") == self._name:
                used = ds.get("used", 0)
                total = ds.get("total", 1)
                avail = ds.get("avail", 0)
                self._state = used
                self._attrs = {
                    "used_bytes": used,
                    "total_bytes": total,
                    "available_bytes": avail,
                    "used_percent": round((used / total) * 100, 2) if total else None,
                    "free_percent": round((avail / total) * 100, 2) if total else None,
                }

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    def _handle_update(self):
        self.update_from_data()
        self.async_write_ha_state()

class ProxmoxSnapshotSensorPerNode(Entity):
    def __init__(self, coordinator, btype, bid, count, size):
        self.coordinator = coordinator
        self._btype = btype
        self._bid = bid
        self._count = count
        self._size = size

    @property
    def name(self):
        return f"Proxmox Backup {self._btype}/{self._bid} Snapshots"

    @property
    def unique_id(self):
        return f"proxmox_backup_{self._btype}_{self._bid}_snapshots"

    @property
    def state(self):
        return self._count

    @property
    def extra_state_attributes(self):
        return {
            "backup_type": self._btype,
            "backup_id": self._bid,
            "snapshot_count": self._count,
            "total_snapshot_size_bytes": self._size,
            "total_snapshot_size_human": self._human_readable_size(self._size),
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
    def __init__(self, coordinator, count, size):
        self.coordinator = coordinator
        self._count = count
        self._size = size

    @property
    def name(self):
        return "Proxmox Backup Total Snapshots"

    @property
    def unique_id(self):
        return "proxmox_backup_total_snapshots"

    @property
    def state(self):
        return self._count

    @property
    def extra_state_attributes(self):
        return {
            "total_snapshot_count": self._count,
            "total_snapshot_size_bytes": self._size,
            "total_snapshot_size_human": self._human_readable_size(self._size),
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
    def __init__(self, coordinator, store, gc_data):
        self.coordinator = coordinator
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
        return {
            "store": self._store,
            "last_run_endtime": self._format_timestamp(self._gc_data.get("last-run-endtime")),
            "next_run": self._format_timestamp(self._gc_data.get("next-run")),
            "removed_bytes": self._gc_data.get("removed-bytes"),
            "removed_chunks": self._gc_data.get("removed-chunks"),
            "index_data_bytes": self._gc_data.get("index-data-bytes"),
            "disk_bytes": self._gc_data.get("disk-bytes"),
            "deduplication_factor": self._calculate_dedup_factor(),
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

