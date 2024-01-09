#!/bin/bash
#title           :init_dial.bash
#description     :FTP setup code
#author          :Nauval Chantika
#date            :2023/12/19
#version         :1.1
#usage           :Iot Gateway
#notes           :
#==============================================================================

CONFIG_FILE="/etc/vsftpd.conf"
TMP_FILE="/tmp/vsftpd.conf.tmp"

# Check if the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Try using sudo."
    exit 1
fi

# Function to update a configuration setting
update_config() {
    local setting="$1"
    local value="$2"
    local commented="$3"

    # Check if the setting already exists
    if grep -qE "^[#]*\s*$setting" "$CONFIG_FILE"; then
        # Setting exists, modify it
        sed -i "/^[#]*\s*$setting/c$setting=$value" "$CONFIG_FILE"
    elif [ "$commented" = true ]; then
        # Setting does not exist, append it (commented)
        echo "#$setting=$value" >> "$CONFIG_FILE"
    else
        # Setting does not exist, append it
        echo "$setting=$value" >> "$CONFIG_FILE"
    fi
}

# Backup the original configuration file
cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

# Update the configuration settings
update_config "local_enable" "YES" false
update_config "write_enable" "YES" false
update_config "ssl_enable" "YES" false
update_config "force_local_data_ssl" "NO" false
update_config "force_local_logins_ssl" "NO" false
update_config "local_umask" "022" true

# Restart vsftpd to apply changes
systemctl restart vsftpd
echo "vsftpd configuration updated and service restarted."
