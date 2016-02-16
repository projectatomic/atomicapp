Atomicapp Lifecycle Definition
==============================

The Atomic App software allows for several actions to be applied to
specified applications. The four actions that exist today are briefly
described below.

`genanswers`
------------
Will download and combine artifacts from the target application in a
temporary directory and then take the generated sample answers.conf
file and populate it in the users working directory. The temporary 
directory is then cleaned up.

`fetch`
-------
Will download and combine artifacts from the target application and any 
dependent applications including sample answers.conf file into a local 
directory for inspection and/or modification. Same for all providers.

`run`
-----
Run an application.

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Run application containers on local machine. |
| Kubernetes    | Run requested application in kubernetes target environment. |
| Openshift     | Run requested application in OpenShift target environment. |
| Marathon      | Run requested application in Marathon target environment. |

`stop`
------
Stop an application. 

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Stop application containers on local machine. |
| Kubernetes    | Stop requested application in kubernetes target environment. |
| Openshift     | Stop requested application in OpenShift target environment. |
| Marathon      | Stop requested application in Marathon target environment. |
