# ProxmoxBackupServer integration  

##HowTo:
* create a dir; config/custom_components/proxmox_backup  
* copy all the files to that dir.  
* add the following to your configuration


```yaml  
# configuration.yaml
sensor:
  - platform: proxmox_backup
    pbs_host: !secret pbs_host
    pbs_token_id: !secret pbs_token_id
    pbs_token: !secret pbs_token
``` 

# Endpoints to be added:  
I'll start with those endpoints:  
```yaml
  /api2/json/admin
    /api2/json/admin/datastore  # Name of the datastore
    /api2/json/admin/gc
    /api2/json/admin/metrics
    /api2/json/admin/prune
    /api2/json/admin/sync
    /api2/json/admin/traffic-control
    /api2/json/admin/verify

```


# All Endpoint available:

```yaml  
/api2/json
  /api2/json/access
    /api2/json/access/acl
    /api2/json/access/domains
    /api2/json/access/openid
      /api2/json/access/openid/auth-url (Failed: 404)
      /api2/json/access/openid/login (Failed: 404)
    /api2/json/access/password (Failed: 404)
    /api2/json/access/permissions
    /api2/json/access/roles
    /api2/json/access/tfa
    /api2/json/access/ticket (Failed: 404)
    /api2/json/access/users
  /api2/json/admin
    /api2/json/admin/datastore
    /api2/json/admin/gc
    /api2/json/admin/metrics
    /api2/json/admin/prune
    /api2/json/admin/sync
    /api2/json/admin/traffic-control
    /api2/json/admin/verify
  /api2/json/backup (Failed: 400)
  /api2/json/config
    /api2/json/config/access
      /api2/json/config/access/ad
      /api2/json/config/access/ldap
      /api2/json/config/access/openid
      /api2/json/config/access/pam
      /api2/json/config/access/pbs
      /api2/json/config/access/tfa
        /api2/json/config/access/tfa/webauthn
    /api2/json/config/acme
      /api2/json/config/acme/account
      /api2/json/config/acme/challenge-schema
      /api2/json/config/acme/directories
      /api2/json/config/acme/plugins
      /api2/json/config/acme/tos
    /api2/json/config/changer
    /api2/json/config/datastore
    /api2/json/config/drive
    /api2/json/config/media-pool
    /api2/json/config/metrics
      /api2/json/config/metrics/influxdb-http
      /api2/json/config/metrics/influxdb-udp
    /api2/json/config/notifications
      /api2/json/config/notifications/endpoints
        /api2/json/config/notifications/endpoints/gotify
        /api2/json/config/notifications/endpoints/sendmail
        /api2/json/config/notifications/endpoints/smtp
        /api2/json/config/notifications/endpoints/webhook
      /api2/json/config/notifications/matcher-field-values
      /api2/json/config/notifications/matcher-fields
      /api2/json/config/notifications/matchers
      /api2/json/config/notifications/targets
    /api2/json/config/prune
    /api2/json/config/remote
    /api2/json/config/sync
    /api2/json/config/tape-backup-job
    /api2/json/config/tape-encryption-keys
    /api2/json/config/traffic-control
    /api2/json/config/verify
  /api2/json/nodes (Failed: 403)
  /api2/json/ping
  /api2/json/pull (Failed: 404)
  /api2/json/push (Failed: 404)
  /api2/json/reader (Failed: 400)
  /api2/json/status
    /api2/json/status/datastore-usage
    /api2/json/status/metrics
  /api2/json/tape
    /api2/json/tape/backup
    /api2/json/tape/changer
    /api2/json/tape/drive
    /api2/json/tape/media
      /api2/json/tape/media/content
      /api2/json/tape/media/destroy (Failed: 400)
      /api2/json/tape/media/list
      /api2/json/tape/media/media-sets
      /api2/json/tape/media/move (Failed: 404)
    /api2/json/tape/restore (Failed: 404)
    /api2/json/tape/scan-changers (Failed: 403)
    /api2/json/tape/scan-drives (Failed: 403)
  /api2/json/version

```
