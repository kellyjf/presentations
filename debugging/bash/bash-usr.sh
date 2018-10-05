#!/bin/bash
a=0
function debug {
	[ "$((${a}%2))" == "1" ] && caller
}

function toggle1 {
	case "$(shopt -o xtrace)" in
		*off) set -x;;
		*)    set +x;;
	esac
}

function toggle2 {
	a=$((${a:-0}+1))
	echo toggle2 $a
	trap 'debug' DEBUG
}

function wheremi {
	for frame in $(seq 0 10); do
		caller $frame
	done
}

trap toggle1 USR1
trap toggle2 USR2

function amain() {
	while read word \
#		< /usr/share/dict/words
	do
		seeking=$word
		case "$word" in 
			*stuff*) echo $word ;;
		esac
	done \
	 < /usr/share/dict/words
}

function bmain() {
	amain
}

bmain

	
