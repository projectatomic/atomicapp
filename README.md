# Atomic App

Atomic App is a reference implementation of the [Nulecule specification](https://github.com/projectatomic/nulecule). It can be used to bootstrap packaged container environments and then run them. Atomic App is designed to be ran within a container. 

Examples of this tool may be found within the [Nulecule library repo](https://github.com/projectatomic/nulecule/tree/master/examples).

## Getting Started

Atomic App itself is packaged as a container. End-users typically do not install the software from source. Instead use the `atomicapp` container as the `FROM` line in a Dockerfile and package your application on top. For example:

```
FROM projectatomic/atomicapp

MAINTAINER Your Name <you@example.com>

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
```

For more information see the [Nulecule getting started guide](https://github.com/projectatomic/nulecule/blob/master/docs/getting-started.md).

## Developers

First of all, clone the github repository: `git clone https://github.com/projectatomic/atomicapp`.

### Installing Atomic App locally
Simply run

```
make install
```

If you want to do some changes to the code, I suggest to do:

```
cd atomicapp
export PYTHONPATH=`pwd`:$PYTHONPATH
alias atomicapp="python `pwd`/atomicapp/cli/main.py"
```

### Building for containerized execution
```
docker build -t [TAG] .
```

Use 'docker build' to package up the application and tag the resulting image.

### Fetch and run
```
atomicapp [--dry-run] [-v] [-a answers.conf] fetch|run|stop|genanswers [--provider docker] [--destination DST_PATH] APP|PATH
```

Pulls the application and its dependencies. If the last argument is
existing path, it looks for `Nulecule` file there instead of pulling anything.

* `--provider docker` Use the Docker provider within the Atomic App
* `--destination DST_PATH` Unpack the application into given directory instead of current directory
* `APP` Name of the image containing the application (ex. `projectatomic/apache-centos7-atomicapp`)
* `PATH` Path to a directory with installed (ex. result of `atomicapp fetch...`) app

Action `run` performs `fetch` prior to its own tasks if an `APP` is provided. Otherwise, it will use its respective `PATH`. When `run` is selected, providers' code is invoked and containers are deployed.

## Providers

Providers represent various deployment targets. They can be added by placing the artifact within the respective in `provider/` folder. For example, placing `deploy_pod.yml` within `providers/kubernetes/`. For a detailed description of all providers available see [docs/providers.md](docs/providers.md).

## Dependencies

See [REQUIREMENTS](https://github.com/projectatomic/atomicapp/blob/master/docs/requirements.md) for current Atomic App dependencies.

##Communication channels

* IRC: #nulecule (On Freenode)
* Mailing List: [container-tools@redhat.com](https://www.redhat.com/mailman/listinfo/container-tools)

# The Badges

[![Code Health](https://landscape.io/github/projectatomic/atomicapp/master/landscape.svg?style=flat)](https://landscape.io/github/projectatomic/atomicapp/master)
[![Build Status](https://travis-ci.org/projectatomic/atomicapp.svg?branch=master)](https://travis-ci.org/projectatomic/atomicapp)
[![Coverage Status](https://coveralls.io/repos/projectatomic/atomicapp/badge.svg?branch=master&service=github)](https://coveralls.io/github/projectatomic/atomicapp?branch=master)
[![Issue Stats](http://issuestats.com/github/projectatomic/atomicapp/badge/pr)](http://issuestats.com/github/projectatomic/atomicapp)
[![Issue Stats](http://issuestats.com/github/projectatomic/atomicapp/badge/issue)](http://issuestats.com/github/projectatomic/atomicapp)

# Copyright

Copyright (C) 2016 Red Hat Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

The GNU Lesser General Public License is provided within the file lgpl-3.0.txt.
