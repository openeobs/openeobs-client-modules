#!/bin/bash

if [ $# -ne 6 ]; then 
    echo "usage: backup [HOST] [CREDENTIALS] [REMOTE_MOUNT_POINT] [LOCAL_MOUNT_POINT] [REMOTE_RSYNC_DIR] [LOCAL_RSYNC_DIR] "
    exit 1
fi

HOST=$1
CREDENTIALS=$2
REMOTE_MOUNT_POINT=$3
LOCAL_MOUNT_POINT=$4
REMOTE_RSYNC_DIR=$5
LOCAL_RSYNC_DIR=$6


ping -c 1 $HOST &>/dev/null
# if the destination is up mount it (if it's not already mounted)
if [ $? -eq 0 ]; then  # check the exit code
		if [ ! "`mount | grep $LOCAL_MOUNT_POINT`" ] #if its not alread mounted, mount it
		then 
				mount -t cifs -o credentials=$CREDENTIALS,iocharset=utf8,file_mode=0777,dir_mode=0777 "//$HOST$REMOTE_MOUNT_POINT" $LOCAL_MOUNT_POINT
				if [ $? -ne 0 ]; # check the exit code
				then	
						echo "ERROR: Directory did not mount correctly. Return code was: $?. Rsync not attempted"
						exit 1
				fi
		fi
		DATE=$(date +"%Y-%m-%d %H:%M:%S")
		echo "$DATE - rsync started."
		rsync -rlOD "$LOCAL_RSYNC_DIR"  "$LOCAL_MOUNT_POINT$REMOTE_RSYNC_DIR"
		# Check the rsync
		if [ $? -eq 0 ]; then  # check exit OK
				DATE=$(date +"%Y-%m-%d %H:%M:%S")
				echo "OK: $DATE - rsync to $HOST$REMOTE_MOUNT_POINT success"
		else
				DATE=$(date +"%Y-%m-%d %H:%M:%S")
				echo "ERROR: $DATE - rsync to $HOST$REMOTE_MOUNT_POINT failed"
		fi

		# Either way, unmount the destination
		umount  $LOCAL_MOUNT_POINT
		if [ $? -ne 0 ]; then  # check the exit code
				echo "WARNING: Directory did not unmount correctly"
				exit 1
		fi
else
		echo "ERROR: $HOST is not reponding to ICMP"
fi