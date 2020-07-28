#!/bin/bash -eu


# Helper function to reliably create a new namespace
function newns {
	nsname=$1
	ip netns del $nsname &> /dev/null || true
	ip netns add $nsname
	ip netns exec $nsname ip link set lo up
}

# Create a new link between namespaces
function newlink {
	wanname=${1:-}
	lanname=${2:-}
	subnet=${3:-192.168.1}
	wanhost=${4:-1}
	lanhost=${5:-2}
	vid=${6:-}

	# Usage line if required args are missing
	if [[ -z $wanname || -z $lanname ]] ; then
		echo "Usage newlink wan-ns [lan-ns subnet wanhost lanhost vid]"
		return
	fi

	# Ensure namespaces exist
	for ns in $wanname $lanname; do
		if ! ip netns ls | grep $ns &> /dev/null ; then
			newns $ns
		fi
	done

	# Compute temp interaces names, and ensure they are pre-removed
	# in the main namespace
	if [[ ! $vid ]]; then
		vid=${subnet##*.}
	fi
	ip link del wan-${vid} &> /dev/null || true
	ip link del lan-${vid} &> /dev/null || true

	# Implement two approaches to creating virtual links
	# If NONET is unset, create a VLAN on the base pair,
	# if set, use a separate veth pair for the link
	if [[ ${NONET:-} ]] ; then
		ip link add wan-${vid} type veth peer name lan-${vid}
	else
		# Ensure a wan/lan pair exist in the main namespace
		if ! [[  -e /sys/class/net/wan ]] ; then
			ip link del wan &> /dev/null || true
			ip link del lan &> /dev/null || true
			ip link add wan type veth peer name lan
			ip link set wan up
			ip link set lan up
		fi

		ip link add link wan name wan-${vid} type vlan id $vid
		ip link add link lan name lan-${vid} type vlan id $vid
	fi
	 
	# Push enpoint pairs into namespaces and rename for 
	# the destination namespace
	ip link set wan-${vid} netns $wanname name $lanname
	ip link set lan-${vid} netns $lanname name $wanname
	ip netns exec $wanname ip link set $lanname up
	ip netns exec $lanname ip link set $wanname up

	# Configure link addresses
	# set default route of lan side to wan as gateway
	wanaddr="${subnet}.${wanhost}"
	lanaddr="${subnet}.${lanhost}"
	
	if [[ ${wanhost} != 0 ]]; then
		ip netns exec $wanname ip addr add dev ${lanname} ${wanaddr}/24
	fi
	if [[ ${lanhost} != 0 ]]; then
		ip netns exec $lanname ip addr add dev $wanname ${lanaddr}/24
		ip netns exec $lanname ip route replace default via ${subnet}.1 
	fi
}

