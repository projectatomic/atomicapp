# Atomic App Roadmap

This document provides a roadmap for current Atomic App development. The dates and features listed below are not considered final but rather an indication of what the core contributors are working on and the direction of Atomic App.

Atomic App is the implementation of the [Nulecule spec](https://github.com/projectatomic/nulecule). We follow the spec closely, the current spec version as well as Atomic App version can be found via `atomicapp --version`.

__Unless otherwise announced, the Atomic App CLI as well as Nulecule spec are subject to change. Backwards compatibility is a priority for version 1.0.0__

We rank all ROADMAP objectives by order of priority. These are subject to frequent change.

#### High priority
 - __Persistent storage__
 - Implement stop for OpenShift provider
 - Support running Kubernetes from an Openshift template

#### Medium priority
 - Refactor logging 
 - AWS provider support
 - Docker compose provider

#### Low priority
 - Nulecule index / library 
 - Keep versioning info in one location 
 - Ansible provider
 - Nspawn provider
 - Add a `USER` to Atomic App image
 - https/ssh/sftp support for artifacts
 - Use API instead of direct command-line for Docker && Kubernetes orchestration
