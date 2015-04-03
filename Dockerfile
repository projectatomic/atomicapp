FROM rhel7
MAINTAINER Vaclav Pavlin <vpavlin@redhat.com>

ADD run.py /opt/atomicapp/run.py
ADD providers /opt/atomicapp/providers
LABEL RUN docker run -it --privileged -v /var/run/docker.socker:/var/run/docker.socket -v /:/host IMAGE

WORKDIR /application-entity

RUN yum -y install 

CMD python /opt/atomicapp/run.py
