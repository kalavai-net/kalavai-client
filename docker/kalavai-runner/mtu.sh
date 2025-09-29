#!/bin/bash
MTU_VALUE=1280

echo "Setting MTU limits..."
# Loop through all interfaces
for iface in $(ls /sys/class/net); do
    type=$(cat /sys/class/net/$iface/type)
    state=$(cat /sys/class/net/$iface/operstate)

    # Skip if it's a loopback (type 772) or not up
    if [ "$type" -eq 772 ]; then
        echo "Skipping $iface (loopback)"
        continue
    fi
    echo "Setting MTU $MTU_VALUE on $iface (state: $state)"
    ip link set mtu "$MTU_VALUE" dev "$iface"
done
