#!/bin/bash -eu


function newns {
	nsname=$1
	ip netns del $nsname &> /dev/null || true
	ip netns add $nsname
	ip netns exec $nsname ip link set lo up
}
function newlink {
	wanname=$1
	lanname=$2
	subnet=${3:-192.168.1}
	wanhost=${4:-1}
	lanhost=${5:-2}
	vid=${6:-}


	for ns in $wanname $lanname; do
		if ! ip netns ls | grep $ns &> /dev/null ; then
			newns $ns
		fi	
	done	

	if ! [[  -e /sys/class/net/wan ]] ; then
		ip link del wan &> /dev/null || true
		ip link del lan &> /dev/null || true
		ip link add wan type veth peer name lan
		ip link set wan up
		ip link set lan up
	fi	

	if [[ ! $vid ]]; then
		vid=${subnet##*.}
	fi
	wanaddr="${subnet}.${wanhost}"
	lanaddr="${subnet}.${lanhost}"

	ip link del wan-${vid} &> /dev/null || true
	ip link add link wan name wan-${vid} type vlan id $vid

	ip link del lan-${vid} &> /dev/null || true
	ip link add link lan name lan-${vid} type vlan id $vid

	ip link set wan-${vid} netns $wanname
	ip link set lan-${vid} netns $lanname

	ip netns exec $wanname ip link set wan-${vid} up	
	ip netns exec $lanname ip link set lan-${vid} up	


	if [[ ${wanhost} != 0 ]]; then
		ip netns exec $wanname ip addr add dev wan-${vid} ${wanaddr}/24	
	fi
	if [[ ${lanhost} != 0 ]]; then
		ip netns exec $lanname ip addr add dev lan-${vid} ${lanaddr}/24	
		ip netns exec $lanname ip route replace default via ${subnet}.1 
	fi
}
