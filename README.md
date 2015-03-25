# AppEnt (PoC, WIP, FIXME...:)

This tool lets you run your multi-container app in Kubernetes by calling a single command
##How to Run
```
cd my-app/
python $path_to_appent/app-ent.py [-a file]
```

##Artifacts
There are few files/atrifacts needed to successfully run the application - Atomicfile, params.ini, Kubernetes configuration files..

###Atomicfile
Atomicfile describes your application and defines the startup sequence.

For out simple wordpress app it looks like this

```
{
    "name": "Wordpress-App",
    "version": "0.0.1",
    "graph": [
        "mariadb",
        "wordpress"
    ]
}
```

The `graph` is the most important part here - it defines what and in which order should be started and in this case simply means: first, start the mariadb, then, if it succeeded, start wordpress.

###params.ini
In this file you can define values for `$variables` used in json/yaml k8s configuration files. 

A section corresponds with the graph item in Atomicfile. General section would be available for all graph items during the substitution

```
# This a a parameters file for an Application
[general]
registry = docker-registry.usersys.redhat.com
foo = bar

[mariadb]
password = test
rootpassword = roottest

[wordpress]
title = Team7
foo = baz
public_ip = None # None means required
```
###answers.ini
This file is optional and has the same structure as params.ini. File params.ini is part of the application and is defined by the developer where, on the other hand, answers.ini as used and modified by administration to override or fil in the blanks.

By default we search for `answers.ini` in current directory, but it can be overried with `-a file`

###Kuberentes configs
Configuration files for Kuberenetes as defined by the project (FIXME link). Variables can be used in these configs - they replaced with values from params.ini and answers.ini on start


