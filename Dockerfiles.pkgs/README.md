
The Dockerfiles.pkgs directory is the place where Dockerfiles live that 
are used to create containers that only pull Atomic App code from the
package management mechanisms of the base OS distribution. For rpm
based distros the Atomic App code would come from the atomicapp rpm
and all dependencies will get pulled in by the package manager.

For example, if you want to build an Atomic App container for CentOS
that is composed of the atomicapp rpm within CentOS then you would run
the following command from the root of the git repo:

```
docker build -t centos-atomicapp-pkgs -f ./Dockerfiles.pkgs/Dockerfile.centos .
```

If you want to do the same thing for Fedora you would:

```
docker build -t fedora-atomicapp-pkgs -f ./Dockerfiles.pkgs/Dockerfile.fedora .
```
