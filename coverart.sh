#!/bin/bash
#coverart.sh

DEFAULT_COVER="./icons/ic_album_white_36dp.png"

# for 'mpd' users
MUSICDIR=`cat /etc/mpd.conf | grep -v "#" | grep music_directory`
MUSICDIR=${MUSICDIR:16}
MUSICDIR=${MUSICDIR%/$}

MFILE=`mpc current -f %file%`
MFILE=${MFILE%/*}
MFILE=${MFILE%/$}

#FULLDIR="$MUSICDIR/$MFILE"
FULLDIR="/home/pi/mpd/music/$MFILE"


## for 'moc' users under Debian, not sure if other distros use the 'mocp' name for the program:
#MFILE=`mocp --format "%file"`
#[ -n "$MFILE" ] && FULLDIR=`dirname "$MFILE"`


[ -n "$FULLDIR" ] && COVERS=`ls "$FULLDIR" | grep "\.jpg\|\.png\|\.gif"`

if [ -z "$COVERS" ]; then
	COVERS="$DEFAULT_COVER"
else
	TRYCOVERS=`echo "$COVERS" | grep -i "cover\|front\|folder\|albumart" | head -n 1`

	if [ -z "$TRYCOVERS" ]; then
		TRYCOVERS=`echo "$COVERS" | head -n 1`
		if [ -z "$TRYCOVERS" ]; then
			TRYCOVERS="$DEFAULT_COVER"
		else
			TRYCOVERS="$FULLDIR/$TRYCOVERS"
		fi
	else
		TRYCOVERS="$FULLDIR/$TRYCOVERS"
	fi

	COVERS="$TRYCOVERS"
fi

echo -n "$COVERS"

