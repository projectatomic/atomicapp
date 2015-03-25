# AppEnt (PoC, WIP, FIXME...:)

This tool lets you run your multi-container app in Kubernetes by calling a single command
##How to Run
```
cd my-app/
python $path_to_appent/app-ent.py [-a file] [--dry-run]
```

###Output


##Artifacts
There are a few files/atrifacts needed to successfully run the application - `Atomicfile`, `params.ini`, and Kubernetes configuration files..

###Atomicfile
`Atomicfile` describes your application and defines the startup sequence.

For our simple WordPress app it looks like this

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

The `graph` is the most important part here - it defines what containers and in which order they should be started. In this example it simply means: first, start the `mariadb` container, then, if it succeeded, start the `wordpress` container.

###params.ini
In this file you can define values for `$variables` used in JSON/YAML Kubernetes configuration files. 

A section corresponds with the `graph` item in `Atomicfile`. A general section is available for all `graph` items during the substitution

```
# This a a parameters file for an Application
[general]
registry = docker-registry.example.com
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
This file is optional and has the same structure as `params.ini`. File `params.ini` is part of the application and is defined by the developer where, on the other hand, `answers.ini` is used and modified by administration to override or fill in the blanks.

By default we search for `answers.ini` in the current directory, but it can be overried with `-a file`.

###Kuberentes configs
Configuration files for Kuberenetes as defined by the project (FIXME link). Variables can be used in these configs - they replace with values from `params.ini` and `answers.ini` on start.


