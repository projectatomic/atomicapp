# Providers
This chapter describes how to use and configure the providers included with Atomic App. It gives you a short overview of all available providers and how to use them.


Not all Atomic Apps must support each provider: one Atomic App may only include deployment information for OpenShift3 while another does support OpenShift3 and Kubernetes.

## List of providers
Atomic App 0.2.3 includes three providers:

  * Docker
  * Kubernetes
  * OpenShift 3

The Docker and Kubernetes providers assume that you install and run the Atomic App on a host that is part of the backend cluster or runs docker directly.

OpenShift may be run in two modes.

1. OpenShift native, using `oc new-app` command
1. Atomic CLI

In native mode an application may be launched using the `oc new-app` command and it will be deployed on a pod. In Atomic mode applications are run like other providers using a local `answers.conf` file.

## Choosing and configuring a provider
While deploying an Atomic App you can choose one of the providers by setting it in `answers.conf`:

### OpenShift

Note: **skip this configuration** if running in *native mode*. To run the application using the Atomic CLI a configuration file is required. You need to specify something like the following in your `answers.conf` file:

```
[general]
provider: openshift
providerapi: https://10.1.2.2:8443
accesstoken: sadfasdfasfasfdasfasfasdfsafasfd
```


### Kubernetes

For Kubernetes the configuration file is optional, but you may find
that you need it for your setup. If you need it, then you can specify
the file in the same way that was done in the openshift example above:

```
[general]
provider: kubernetes
providerconfig: /host/home/foo/.kube/config
```

### Docker

**Features**

The Docker provider will simply start a Docker container on the host the Atomic App is deployed.


Atomic App will use the name within namespace and append it with `atomic` and a hash value. If `--name` is provided within the Docker artifacts file, this will be used but the user will be given a warning.a

This provider does not use `providerconfig` option.

**Configuration values**

Table 1. Docker default configuration values

Keyword  | Required | Description                                           | Default value
---------|----------|-------------------------------------------------------|--------------
namespace|   no     |   namespace to use when deploying docker containers   | default\*

\*The naming convention used when deploying is: `atomic\_APPNAME\_HASHVALUE`

**Operations**

```
atomicapp run
```

This command deploys the app in Docker. The deployment uses the value of `namespace` option within `answers.conf` and deploys with the naming convention `atomic_APPNAME_HASHVALUE`. If a previous deployment with the same name is detected, it will fail and warn the user.

```
atomicapp stop
```

This command undeploys the app in Docker. For the given namespace, the undeploy:

  1. Greps `docker ps` for the namespace

  2. Kills all Docker containers that match

If `--name` was provided in the Docker artifacts file, this command will not work.

### Kubernetes

**Features**

The Kubernetes Provider supports namespaces, this will deploy an application into a given namespace. All components of the applications will be created in that namespace. The `namespace` defined in the Kubernetes artifacts. If any are defined, they must match the namespace value in configuration.


The default value of `namespace` is `default` unless otherwise defined in the Kubernetes manifest.

This provider requires configuration file to be able to connect to Kubernetes Master. If the configuration file is not provided, it will try to generate default configuration file.

**Configuration values**

Table 1. Kubernetes default configuration values

Keyword  | Required | Description                                 | Default value
---------|----------|---------------------------------------------|--------------
namespace|   no     |   namespace to use with each kubectl call   | default

**Operations**

```
atomicapp run
```

This command deploys the app in Kubernetes cluster in a specified namespace. For the given namespace, the deploy process creates objects (pods, replicas, services) in order as enlisted in Nulecule Kubernetes artifacts.

```
atomicapp stop
```
This command undeploys the app in Kubernetes cluster in specified namespace. For the given namespace, the undeploy process consist of:

  1. Scaling down all replicas to 0

  2. Deleting all objects (pods, replicas, services)

### Openshift3

**Features**

The primary use case of the OpenShift3 Provider is to run the Atomic App image natively using the `oc new-app` command. Here is a diagram of how it works.

![OpenShift V3 and Atomic App](https://docs.google.com/drawings/d/13mfTkxv_M3jM6WMsgpJtoKkX4nuVuTPcPSfsebN3qKA/pub?w=884&h=320)

1. The Atomic App image has two metadata LABELs (see below).
1. When `oc new-app` is run the Atomic App image is remotely inspected.
1. The OpenShift Master run the Atomic App image based on the LABELs.
1. The user's token is passed into the resulting pod as a secret to authorize API calls.
1. The Atomic App pod makes API calls to the OpenShift Master to create or run the application.

An Atomic App may also be deployed and run using the `atomic` CLI provided via an OpenShift3 configuration file. An OpenShift3 configuration file is written to a disk provided that you have logged in see [osc login announcement](http://lists.openshift.redhat.com/openshift-archives/users/2015-March/msg00014.html)

You need to provide a path to a copy of `.config/openshift/.config` as `providerconfig` so that the provider may use this configuration to deploy and run the Atomic App.


As of 0.2.3 of Atomic App, OpenShift3 templates will only be processed by Atomic App during the run phase. The names of the parameters supplied by the OpenShift3 template file will be replaced by the parameters supplied to Atomic App.

**Configuration values**

There are no configuration values specific to OpenShift provider.

**LABELs**

There are two required labels for OpenShift to run an Atomic App.

1. `io.openshift.generate.job=true`
  * identify the image as an executable job
  * run the container to allow the image to determine what OpenShift objects are created.
1. `io.openshift.generate.token.as=env:TOKEN_ENV_VAR`
  * run the container with user token so `oc` commands can be run on behalf of the user from within the container pod.
