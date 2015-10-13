# Requirements

Requirements needed to run Atomic App.

## Python requirements

* anymarkup >= 0.4.1
* lockfile

## Non-Python requirements

__Atomic App Core:__

* Docker
* Atomic (after commit: c97e5d3255b85c715fbbb8e17945beffeefc2332)

__Providers:__

*  Docker Provider
  * `docker` installed in the container (ver: 1.7.1, API ver: 1.19)
* Kubernetes Provider
  * `kubectl` either in container or in the /host (ver: v0.9.0)
  * /etc/kubernetes either in container or in the /host
* OpenShift Provider
  * `oc` either in container or in the /host
  * OpenShift config specified in the answers.conf
