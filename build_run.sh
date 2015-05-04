#!/bin/bash

WHAT=$1

[ -z "${WHAT}" ] && echo "Need to provide a distro you want to build for (fedora|centos|rhel7)" && exit
ln -s Dockerfile.${WHAT} Dockerfile

if [ -z "$USERNAME" ]; then
    echo "setting USERNAME to " `whoami` 
    USERNAME=`whoami`
fi

echo docker build --rm -t $USERNAME/atomicapp-run .


docker build --rm -t $USERNAME/atomicapp-run .

rm -f Dockerfile

#doesn't really make sense to run it
#test
#docker run -it --privileged -v /run:/run -v /:/host -v `pwd`:/application-entity $USERNAME/atomicapp-run /bin/bash
#run
#docker run -dt --privileged -v /run:/run -v /:/host -v `pwd`:/application-entity $USERNAME/atomicapp-run
