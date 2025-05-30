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


