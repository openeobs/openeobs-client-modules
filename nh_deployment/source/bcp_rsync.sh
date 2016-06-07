#!/bin/bash

# Neova Health BCP Script
# Used to mount a remote CIFS share before RSYNC of PDFs from local BCP output path to destination

# Global variables
declare SCRIPT_NAME="${0##*/}"
declare SCRIPT_DIR="$(cd ${0%/*} ; pwd)"
declare ROOT_DIR="$PWD"

# Script functions

# Handles usage of script
usage() {
cat << EOF
Usage: $0

OPTIONS:
	o - Print opts from filename
	t - Test Run
	l - Live Run
EOF
exit 0
}

# Checks output for non-zero exit
function checkErrors() {
	# Function. Parameter 1 is the return code
	if [ "${1}" -ne "0" ]; then
		echo "ERROR: ${1} : ${2}"
		# as a bonus, make script exit with the right error code.
		exit ${1}
	fi
}

# Handles failures
function failed() {
	echo -e "ERROR: Run failed"
	echo -e "$1"
	exit 1
}

# Confirm action
function confirm() {
	# Tell the user what they are about to do.
	echo "INFO: About to $1";
	# Ask for confirmation from user
	read -r -p "Are you sure? [Y/n] : " response
	case "$response" in
	    [yY][eE][sS]|[yY]) 
          # If yes, then execute the passed parameters
           $2 $3
           ;;
	    *)
          # Otherwise exit...
          echo "INFO: End"
          exit
          ;;
	esac
}

#######################################################################################
# Set environment VARs here
SELF=(`id -u -n`)
VERSION=0.1

#######################################################################################
# Script functions below

getOptions() {
	# vars file is passed to function as $1
	echo "INFO: Sourcing options from $1"	
	source $1
}

printOptions() {
	echo "INFO: Display vars from conf file"
	echo "HOST = $HOST"
	echo "CREDENTIALS = $CREDENTIALS"
	echo "MOUNT_OPTS = $MOUNT_OPTS"
	echo "REMOTE_MOUNT_POINT = $REMOTE_MOUNT_POINT"
	echo "LOCAL_MOUNT_POINT = $LOCAL_MOUNT_POINT"
	echo "REMOTE_RSYNC_DIR = $REMOTE_RSYNC_DIR"
	echo "LOCAL_RSYNC_DIR = $LOCAL_RSYNC_DIR"
	exit 0
}

# Ping the host
pingDestination(){
	ping -c 1 ${HOST} > /dev/null 2>&1
	checkErrors $? "ERROR: unable to ping host ${HOST}"
}

mountDestination() {
	if [ ! "`mount | grep ${LOCAL_MOUNT_POINT}`" ] ; then #if its not alread mounted, mount it
		mount -v -t cifs -o credentials=${CREDENTIALS},${MOUNT_OPTS} "//${HOST}/${REMOTE_MOUNT_POINT}" ${LOCAL_MOUNT_POINT}
		checkErrors $? "ERROR: Directory did not mount correctly. Return code was: $?."
	fi
}

dryrunDestination() {
	DATE=$(date +"%Y-%m-%d %H:%M:%S")
	echo "INFO: rsync started at $DATE"
	rsync --dry-run -rv ${LOCAL_RSYNC_DIR} "${LOCAL_MOUNT_POINT}/${REMOTE_RSYNC_DIR}"
	checkErrors $? "ERROR: rsync errored for some reason. Return code was: $?."
}

rsyncDestination() {
	DATE=$(date +"%Y-%m-%d %H:%M:%S")
	echo "INFO: rsync started at $DATE"
	rsync -rv ${LOCAL_RSYNC_DIR} "${LOCAL_MOUNT_POINT}/${REMOTE_RSYNC_DIR}"
	checkErrors $? "ERROR: rsync errored for some reason. Return code was: $?."
}

completeRun() {
	DATE=$(date +"%Y-%m-%d %H:%M:%S")
	echo "INFO: rsync completed successfully"
}

umountDestination() {
	umount  ${LOCAL_MOUNT_POINT}
	checkErrors $? "ERROR: Directory did not mount correctly. Return code was: $?."
}

#######################################################################################
# Handles options passed to script

while getopts “odl” OPTION
do
    case $OPTION in
        o)
            ACTION="optsrun"
            VARS=$1
            ;;
        d)
            ACTION="dryrun"
            VARS=$1
            ;;
        l)
			ACTION="liverun"
			VARS=$1
			;;
        ?)
        	usage
            ;;
    esac
done

# If there isn't an action, show usage
if [[ -z $ACTION ]] ; then
	usage
    exit 1
fi

#######################################################################################
# Execute!

if [ $ACTION = optsrun ] ; then
	echo "INFO: Action = Opts";
	getOptions $2;
	printOptions;
fi

if [ $ACTION = dryrun ] ; then
	echo "INFO: Action = Dry";
	getOptions $2;
	pingDestination;
	mountDestination;
	dryrunDestination;
	completeRun;
	umountDestination;
fi

if [ $ACTION = liverun ] ; then
	echo "INFO: Action = Live";
	getOptions $2;
	pingDestination
	mountDestination;
	rsyncDestination;
	completeRun;
	umountDestination;
fi

#######################################################################################
# Done

cd ${ROOT_DIR}
echo -e "INFO: Exit with code 0"
echo
exit 0