FROM rhel7

MAINTAINER Vaclav Pavlin <vpavlin@redhat.com>

RUN echo -e "[epel]\nname=epel\nenabled=1\nbaseurl=https://dl.fedoraproject.org/pub/epel/7/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/epel.repo

RUN yum --enablerepo=rhel-7-server-extras-rpms --disablerepo=rhel-7-server-rt-htb-rpms --disablerepo=rhel-sap-for-rhel-7-server-rpms --disablerepo=rhel-rs-for-rhel-7-server-rpms --disablerepo=rhel-rs-for-rhel-7-server-htb-rpms --disablerepo=rhel-rs-for-rhel-7-server-eus-rpms --disablerepo=rhel-lb-for-rhel-7-server-htb-rpms --disablerepo=rhel-ha-for-rhel-7-server-rpms --disablerepo=rhel-ha-for-rhel-7-server-htb-rpms --disablerepo=rhel-ha-for-rhel-7-server-eus-rpms --disablerepo=rhel-7-server-rt-rpms -y install python-pip docker
RUN pip install yapsy

ADD run.py /opt/atomicapp/run.py
ADD containerapp.py /opt/atomicapp/containerapp.py
ADD create.py /opt/atomicapp/create.py
ADD providers /opt/atomicapp/providers

VOLUME /answers.conf

WORKDIR /application-entity

LABEL RUN docker run -it --privileged -v ${DATADIR}:/atomicapp -v /run:/run -v /:/host -v ${CONFDIR}/answers.conf:/application-entity/answers.conf --name NAME -e NAME=NAME -e IMAGE=IMAGE IMAGE /opt/atomicapp/containerapp.py -d run /atomicapp
LABEL INSTALL docker run --rm -it --privileged -v /run:/run -v ${DATADIR}:/atomicapp -v /:/host -v ${CONFDIR}/answers.conf:/application-entity/answers.conf -e IMAGE=IMAGE -e NAME=NAME --name NAME IMAGE /opt/atomicapp/containerapp.py -d install --update --path /atomicapp /application-entity

CMD python /opt/atomicapp/run.py -a /answers.conf -d

