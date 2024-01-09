#!/bin/bash
#title           :alter_dial.bash
#description     :SIMHAT module installation script (alternative)
#author          :Nauval Chantika
#date            :2023/10/23
#version         :1.1
#usage           :Iot Gateway
#notes           :Use it when network connection still doesn't appear when you use init_dial.bash
#==============================================================================

echo ""
echo "Starting SIM Hat System installation..."
echo ""
echo "Press 'ctrl + C' to cancel"

# Enable execute (run program) privilege for all related files
sudo chmod +x /home/$(logname)/NIW/simhat_code/dial.bash
sudo chmod +x /home/$(logname)/NIW/simhat_code/route.bash

# Write RaspberyPi's username-dependent command in dial.bash
sudo > /home/$(logname)/NIW/simhat_code/dial.bash
sudo cat <<endoffile >> /home/$(logname)/NIW/simhat_code/dial.bash
#!/bin/bash
echo ""
date +"%Y-%m-%d %H:%M:%S"
echo ""

exit 0
endoffile

while true; do
echo ""
read -p "Will this machine act as a Router? (Y/n) " yn_router
case $yn_router in
[Yy]*)
while true; do
echo ""
read -p "Do you want to configure the SIM card first? (Y/n): " yn_sim
case $yn_sim in
[YyNn]*)
echo ""
echo "OK"
break;;
*)
echo ""
echo "Invalid input. Please answer 'y' or 'n'.";;
esac
done
break;;

[Nn]*)
echo ""
echo "OK"
yn_sim="y"
break;;
*)
echo ""
echo "Invalid input. Please answer 'y' or 'n'.";;
esac
done

echo "<======== Continuing ========>"

#=================================================
# ==== CONFIGURE SIMHAT CONNECTION (OPTIONAL) ====
if [[ "$yn_sim" == "y" || "$yn_sim" == "Y" ]]; then
  echo ""
  echo "Continuing with SIM Card configuration..."
  echo ""
  # Install Libraries/Packages
  ## Simhat module connection
  sudo apt update

  ## Network manager to make new connection profile
  sudo apt install network-manager -y
  sudo apt install modemmanager -y

  ## kernel modules for the SIM Hat's driver (OPTIONAL: Uncomment it manually)
  #sudo apt install linux-headers-$(uname -r) -y # for another debian OS
  #sudo apt install linux-image-rpi-$(uname -r | rev | cut -d- -f1 | rev) -y # for Raspberry pi OS
  #sudo apt install raspberrypi-kernel-headers -y # for Raspberry pi OS

  ## 'zerotier' for virtual LAN and remote access
  sudo apt install net-tools nmap -y
  sudo apt install curl -y
  curl -s https://install.zerotier.com | sudo bash

  ## cron for task automation
  sudo apt install cron -y
  sudo systemctl enable cron
  sudo chmod +x /etc/crontab

  ## on-screen keyboard for touchpanel (OPTIONAL)
  sudo apt install onboard -y

  ## ssh and VNC for remote access
  if ! systemctl is-enabled --quiet ssh; then
    sudo systemctl enable --now ssh
  fi
  if ! systemctl is-enabled --quiet vncserver-x11-serviced; then
    sudo raspi-config nonint do_vnc 0
  fi

  echo ""
  echo "<======== Packages Installation Done ========>"
  echo ""

  # Checking for Module Initialized and loaded correctly
  dmesg | grep -i modem
  echo ""
  echo "<== Please Check if modem is loaded correctly ==>"
  echo ""

  mmcli -L
  echo ""
  echo "<====== Note for modem connection path ======>"
  echo ""

  if ! systemctl is-active --quiet NetworkManager; then
    echo "Starting and Enabling NetworkManager Service"
    sudo systemctl enable NetworkManager
    sudo systemctl start NetworkManager
  else
    echo "NetworkManager Service is running"
  fi

  # Enable ModemManager while Make APN Connection
  if ! systemctl is-active --quiet ModemManager; then
      sudo systemctl start ModemManager
  fi
  if ! systemctl is-enabled --quiet ModemManager; then
      sudo systemctl enable ModemManager
  fi

  # ======== CONNECTING TO THE INTERNET ========
  while true; do
    echo ""
    echo "Create a mobile broadband connection profile (APN needed)"
    echo ""
    echo "Please input the SIM card's APN information"
    echo "Press 'Enter' for empty Username or Password"
    echo ""
    read -p "connection name: " conn_name
    read -p "connection APN : " conn_apn
    read -p "APN username   : " conn_user
    read -p "APN password   : " conn_pass
    echo ""
    if [ ! -z "$conn_name" ] && nmcli -f NAME connection show | grep -q "$conn_name"; then
      echo "Name already used, please change the name"
      echo ""
      nmcli connection show | grep "$conn_name"
      echo ""
    else
      break
    fi
  done
   
  if [ ! -z "$conn_name" ]; then
    gsm_conns=$(nmcli -f NAME,TYPE connection show | grep gsm | awk '{print $1}')
    declare -a list
    for gsm in $gsm_conns; do
      apn_line=$(nmcli connection show "$gsm" | grep gsm.apn)
      apn_value=$(echo "$apn_line" | awk -F: '{print $2}' | tr -d ' ')
      if [ "$apn_value" = "$conn_apn" ]; then
        list+=("$gsm")
      fi
    done
    if [ "${#list[@]}" -ne 0 ]; then
      echo "You already have connection with this APN before, this is the list"
      echo ""
      echo "NAME                UUID                                  TYPE      DEVICE  "
      for item in "${list[@]}"; do
        nmcli connection show | grep "$item"
      done
      while true; do
        echo ""
        read -p "Do you want to make a new connection? (Y/n): " yn_apn
        case $yn_apn in
        [Yy]*)
          yn_apn="Y"
          nmcli connection delete "$conn_name"
          break;;
        [Nn]*)
          yn_apn="n"
          break;;
        *)
          echo ""
          echo "Invalid input. Please answer 'y' or 'n'.";
          esac
      done
    else
      yn_apn="Y"
    fi
    if [[ "$yn_apn" == "Y" ]]; then
      echo ""
      echo "Create new connection profile"
      echo ""
      sudo nmcli connection add type gsm ifname '*' con-name "$conn_name" apn "$conn_apn"
      if [ ! -z "$conn_user" ]; then
          sudo nmcli connection modify "$conn_name" gsm.username "$conn_user"
      fi
      if [ ! -z "$conn_pass" ]; then
          sudo nmcli connection modify "$conn_name" gsm.password "$conn_pass"
      fi

      sudo nmcli connection up "$conn_name"

      conn_device=$(nmcli -g GENERAL.DEVICES connection show "$conn_name")
      if [ -z "$conn_device" ]; then
          echo "No device associated with $conn_name. Removing the connection..."
          nmcli connection delete "$conn_name"
      else
          echo "Connection $conn_name is associated with device $conn_device."
      fi

      echo ""
      echo "Check if the sim module is already appear (gsm) or (ppp0 / wwan0)"
      echo ""
      nmcli connection show --active
    fi
  fi

  # ======== CONFIGURE ZEROTIER NETWORK ========
  # Join the ZeroTier network
  echo ""
  echo "This machine needs to join ZeroTier network to enable remote access"
  while true; do
    read -p "Do you want to configure it now? (Y/n): " yn_zerotier
    case $yn_zerotier in
    [Yy]*)
      while true; do
        echo ""
        read -p "Please input the ZeroTier Network_ID: " zt_net_id
        sudo zerotier-cli join $zt_net_id
        sleep 2
        if sudo zerotier-cli listnetworks | grep -q "$zt_net_id"; then
          break
        else
          echo ""
          echo "Please try again."
        fi
      done

      while true; do
        read -p "Do you want this machine to join another ZeroTier network? (Y/n): " yn_zerotier
        case $yn_zerotier in
        [Yy]*)
          while true; do
            echo ""
            read -p "Please input the ZeroTier Network_ID: " zt_net_id
            sudo zerotier-cli join $zt_net_id
            sleep 2
            if sudo zerotier-cli listnetworks | grep -q "$zt_net_id"; then
              break
            else
              echo ""
              echo "Please try again."
            fi
          done;;
        [Nn]*)
          echo ""
          echo "OK."
          break;;
        *)
          echo ""
          echo "Invalid input. Please answer 'y' or 'n'.";;
          esac
      done
      break;;

    [Nn]*)
      echo ""
      echo "OK."
      break;;
    *)
      echo ""
      echo "Invalid input. Please answer 'y' or 'n'.";;
      esac
  done
  echo ""
  echo "Continuing with SIM Card and internet configuration..."
  echo ""
fi
# ==== END OF CONFIGURE SIMHAT CONNECTION (OPTIONAL) ====

#=================================================
# ==== RASPBERRY PI AS ROUTER ====
while true; do
  case $yn_router in
  [Yy]*)
    echo ""
    echo "Continuing with Router function configuration..."
    echo ""
    # Install packages for 'router' operation and debugging
    sudo apt install dnsmasq iptables iptables-persistent tcpdump -y

    # Input ZeroTier interface
    while true; do
      echo ""
      echo "Here is your machine's ZeroTier network information:"
      sudo zerotier-cli listnetworks
      echo ""
      echo "Type in the ZerotTier interface of the network that you want to route from the information above"
      read -p " it should be in the format zt********* from the <dev> section: " zt_iface
      if sudo zerotier-cli listnetworks | grep -q "$zt_iface"; then
        echo ""
        echo "OK"
        break
      else
        echo ""
        echo "Interface not found. Please try again."
      fi
    done

    # Input 'router' subnet address
    echo ""
    echo "Your Raspberry Pi will manage local network (ethernet) route 172.21.xxx.0/24"
    echo "with subnet xxx being between the value 2-254"
    echo "and different with other Raspberry Pi routers in ZeroTier network"
    read -p "Type in the value of subnet xxx: " subnet

    # Run route.bash to configure routing operation
    sudo bash /home/$(logname)/NIW/simhat_code/route.bash $zt_iface $subnet

    # Write RaspberyPi's subnet-dependent command in dial.bash
    sudo su -c "sed -i '/.*exit.*/d' /home/$(logname)/NIW/simhat_code/dial.bash"
    echo -e "
    echo \"\"
    # Run route.bash if no hosts are up (RasPi-as-Router LAN's network)
    if ! [ \$(sudo nmap -sP 172.21.$subnet.0/24 | grep \"Host is up\" | wc -l) -gt 1 ]; then
      echo \"NO ROUTING FUNCTION\"
      sudo bash /home/$(logname)/NIW/simhat_code/route.bash $zt_iface $subnet
    fi
    exit 0" | sudo tee -a /home/$(logname)/NIW/simhat_code/dial.bash &> /dev/null

    echo ""
    echo "=========================================================="
    echo "Installation of Raspberry Pi as Router system is finished"
    echo "The LAN's default gateway is 172.21.$subnet.1"
    echo "with Subnet Mask 255.255.255.0 and DNS Server 8.8.8.8 (Google)"
    echo "for up to 20 devices"

    echo "----------------------------------------------------------"
    echo "Follow these steps to route between ZeroTier network"
    echo " and this machine's local network (ethernet)"
    echo ""
    echo "Open my.zerotier.com/network/\$NETWORK_ID"
    echo "Go to Settings -> Advanced -> Managed Routes"
    echo "Fill in the \"Add Routes\" parameters:"
    echo "Destination = 172.21.$subnet.0/23"
    echo "Via = 172.21.$subnet.1"
    echo "Click \"Submit\""
    echo "Go to Members, search for this machine's ZeroTier address"
    echo "On the \"Managed IPs\" column, add IP address: 172.21.$subnet.1"
    break;;

  [Nn]*) 
    echo ""
    echo "=========================================================="
    echo "Installation of SIM Hat system (SIM Card configuration) is finished"
    break;;

  *)
    echo "Invalid input. Please answer 'y' or 'n'.";;
    esac
done

# Create cron command to check connection every 2 minutes, stars dial.bash if there is no internet
line='*/2 * * * * root sudo bash /home/$(logname)/NIW/simhat_code/dial.bash >> /home/$(logname)/NIW/simhat_code/dial.log 2>&1'
# Check whether the command line already exists in /etc/crontab, add or uncomment it if it does not

if [ ! -f "/etc/cron.d/dial" ]; then
  touch "/etc/cron.d/dial"
fi

sudo chmod 644 "/etc/cron.d/dial"
sudo su -c "sed -i '/simhat_code/d' /etc/crontab"
sudo su -c "sed -i '/simhat_code/d' /etc/cron.d/dial"
sudo su -c "echo \"$line\" >> /etc/cron.d/dial"
# Restart cron service
sudo service cron restart

# Disable ModemManager after add APN
if systemctl is-active --quiet ModemManager; then
    sudo systemctl stop ModemManager
fi
if systemctl is-enabled --quiet ModemManager; then
    sudo systemctl disable ModemManager
fi

echo ""
echo "This machine's ZeroTier address is $(echo "$(sudo zerotier-cli info)" | awk '{print $3}')"
echo "Please authorize this machine in the ZeroTier Central network settings [my.zerotier.com]."
echo ""
echo "Also, please reboot the RaspberryPi, just in case :)"
echo "=========================================================="
echo ""
# ==== END OF RASPBERRY PI AS ROUTER ====
exit 0

