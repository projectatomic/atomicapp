FROM projectatomic/atomicapp:0.4.1

MAINTAINER Your Name <you@email.com>

LABEL io.projectatomic.nulecule.specversion="0.0.2" \
      io.projectatomic.nulecule.providers="kubernetes, docker" \
      Build="docker build --rm --tag test/$app_name-atomicapp ."

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
