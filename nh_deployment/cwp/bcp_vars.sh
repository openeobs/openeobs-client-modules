export HOST_IP="cwp00840v"
export CREDENTIALS="/root/.smbcredentials"
export MOUNT_OPTS="iocharset=utf8,file_mode=0777,dir_mode=0777,verbose"
export REMOTE_MOUNT_POINT="cwp"
export LOCAL_MOUNT_POINT="/bcp/remote"
export LOCAL_RSYNC_DIR="/bcp/out/"

declare -A REMOTEDIRMAP
REMOTEDIRMAP[Meadowbank]="SpringView/Meadowbank Ward"
REMOTEDIRMAP[Cherry]="West5/Ward_Drives/Cherry Ward"
declare -p REMOTEDIRMAP > wards_to_backup