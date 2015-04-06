FROM fedora
MAINTAINER langdon <langdon@fedoraproject.org>
#Derived from Vaclav Pavlin <vpavlin@redhat.com>; https://github.com/vpavlin/atomicapp-run
RUN yum clean all && yum -y update
RUN yum -y install python python-pip
RUN yum clean all

ADD requirements.txt /opt/atomicapp/
RUN pip install -r /opt/atomicapp/requirements.txt

ADD run.py /opt/atomicapp/run.py
ADD containerapp.py /opt/atomicapp/containerapp.py
ADD create.py /opt/atomicapp/create.py
ADD providers /opt/atomicapp/providers

VOLUME /application-entity
WORKDIR /application-entity

LABEL RUN docker run -it --privileged -v ${DATADIR}:/atomicapp -v /run:/run -v /:/host -v ${CONFDIR}/answers.conf:/application-entity/answers.conf --name NAME -e NAME=NAME -e IMAGE=IMAGE IMAGE /opt/atomicapp/containerapp.py -d run /atomicapp
LABEL INSTALL docker run --rm -it --privileged -v /run:/run -v ${DATADIR}:/atomicapp -v /:/host -v ${CONFDIR}/answers.conf:/application-entity/answers.conf -e IMAGE=IMAGE -e NAME=NAME --name NAME IMAGE /opt/atomicapp/containerapp.py -d install --update --path /atomicapp /application-entity

#CMD python /opt/atomicapp/run.py -a /answers.conf -d

ENTRYPOINT ["/opt/atomicapp/containerapp.py"]
