## Atomic App 0.2.1 (11-04-2015)

This is a major release for Atomic App that refactors most of the base code as well as adds numerous features.

  * Complete refactor of the Atomic App core codebase
  * JSON Pointer xpathing for artifacts
  * Integration of unpacking to /var/lib/atomicapp rather than `cwd`
  * Numerous bug fixes && improvements to integration tests


Please see the `git shortlog` summary below for all commits since the previous release.

```
Charlie Drage <charlie@charliedrage.com> (8):
      Remove dotfiles from tests
      Sync requirements with master. Fixes lockfile issue.
      add xpathing

Dusty Mabe <dusty@dustymabe.com> (15):
      Don't unpack files to cwd
      Enables running atomicapp from within a container again.
      Implement a few comments from code review #356.
      Remove Aaron from MAINTAINERS upon his request.
      Add Ratnadeep to MAINTAINERS :)
      Adds preferred email for Dusty to MAINTAINERS.
      Adds nice error message for Docker client/server out of sync. Closes #174
      Syncs up run labels in Dockerfiles.
      Fixes run label in Dockerfiles so that atomic run <image> works.

Jeroen van Meeuwen (Kolab Systems) <vanmeeuwen@kolabsys.com> (1):
      Use epel-release rather than echo'ing .repo config files

Ratnadeep Debnath <rtnpro@gmail.com> (19):
      Updated docs for file handling for artifact path. #143
      Added note on not supporting nested artifact dir. #143
      Added unittests for Nulecule class.
      Added tests for NuleculeComponent load
      Added tests for NuleculeComponent run.
      Added tests for stopping NuleculeComponent.
      Added tests for NuleculeComponent load_config.
      Added tests for loading external app in NuleculeComponent.
      Added tests for accessing components of a nulecule component.
      In NuleculeComponent, pass 'dryrun' param when calling render of external Nulecule.
      Added tests for rendering a NuleculeComponent
      Added tests for retrieving artifact paths for a NuleculeComponent.
      Added tests for rendering an artifact in NuleculeComponent.
      Reorganize and group code in each testcase for atomicapp/nulecule into
      Bugfix in merging config and updated tests for the same
      Fix unittest for Nulecule load config.
      Fix mocking 'open' in nulecule/base.py.
      Fixed test for rendering artifact.
      Fixed test for rendering local artifact for provider.

Tomas Kral <tkral@redhat.com> (1):
      do not create symlink if source doesn't exist
```

## Atomic App 0.1.12 (10-22-2015)

We have fixed many bugs as well as implemented more enhancements to the Atomic App life cycle with this release. 

Please see below for a summary of commits for the 0.1.12 release.

```
Aaron Weitekamp <aweiteka@redhat.com> (2):
      Add openshift LABELs
      Add OpenShift LABEL information

Charlie Drage <charlie@charliedrage.com> (10):
      update testing
      dup code
      add two new cool maintainers!
      fix artifact bug
      added makefile
      update travis
      add requirement doc
      docker stop terminology fix

Christoph Görn <goern@redhat.com> (13):
      add some issuestats.com stats
      prepared Atomic App 0.1.11 release
      added merge rules

Dusty Mabe <dusty@dustymabe.com> (4):
      Fixes handling of directory for answers argument.
      Reverts "artifact logic bugfix". Fixes #306
      Fixes broken builds bc of lockfile dependency.

Subin M <subin@apache.org> (1):
      add new method find_executable_binary

Swapnil Kulkarni <me@coolsvap.net> (1):
      Small fix for pep8 error

Václav Pavlín <vaclav.pavlin@gmail.com> (5):
      Generate provider config for kubernetes if it does not exist
      Do not use sudo in Docker provider
      Use DEFAULT_PROVIDER_CONFIG in exception message
      Mention config file generation in Kubes provider descripion
      Fix bad indentation issue
```

# Atomic App Base Container Image

Welcome to Atomic App, this is the reference implementation of the [Container
Application Specification](http://www.projectatomic.io/nulecule/spec/0.0.2/index.html) (aka the Nulecule Specification)

## Atomic App 0.1.11 (2015-Sept-23)

This is a hotfix to 0.1.10 and removed a bug we had in [Missing config file error (~/.kube/config) in 0.1.10](https://github.com/projectatomic/atomicapp/issues/280).

Author: Václav Pavlín <vaclav.pavlin@gmail.com>
 * Do not use sudo in Docker provider, Fixes #281

 * Generate provider config for kubernetes if it does not exist

    There is new unimplemented method in Plugin - generateConfigFile.
    This method is invoked in case a provider calls checkConfigFile
    and the file does not exist. If provider does not implement
    this method, error about missing configuration file will
    be printed out. Config file will be generated and used if the method
    is implemented.  
    Currently, it is implemented only by Kubernetes provider.
    Fixes #280

Author: Charlie Drage <charlie@charliedrage.com>

 * fix openshift import warning

## Atomic App 0.1.10 (2015-Sept-21)

With this releasewe have fixed many bugs and implemented many enhancements, please see the [Atomic App Issue tracker](https://github.com/projectatomic/atomicapp/issues/) for the past.

A summary of the major new features is given below.

Author: Charlie Drage <charlie@charliedrage.com>

 * More unit testing / restructure
 * undeploy added to docker provider
 * dont ask for missing artifacts if stopping
 * debian dockerfile support

Author: Ratnadeep Debnath <rtnpro@gmail.com>

 * Convert global params in Nulecule file to `Dict` rather than `List`, fixed #276

Author: Václav Pavlín <vaclav.pavlin@gmail.com>

 * Add `providerconfig` option to fix #266
 * Add Dockerfile for running tests, add How-to-test to CONTRIBUTION.md

Author: Navid Shaikh <nshaikh@redhat.com>
 * Add the right nodePort from allowed port range, reference <https://github.com/kubernetes/kubernetes/blob/master/docs/user-guide/services.md#type-nodeport>
 * Add tests for fix of issue #212
 * Fixes processing multiple k8s artifacts resources
      - Nulecule multiple resource artifacts defined per kind of resource can now be
      processed without overriding earlier artifacts
      - Modifies the methods names as per <https://www.python.org/dev/peps/pep-0008/#method-names-and-instance-variables>
      - Alters order of imports as per <https://www.python.org/dev/peps/pep-0008/#imports>
      - Adds docstring to methods
 * Adds support for resizing replicas if using kube v1 APIs   
      This patch adds provision for lookup of resource identity based on the API
      version under processing. Presently support for v1, v1beta3 and v1beta1 APIs
      are included.

Author: Aaron Weitekamp <aweiteka@redhat.com>

 * Fix typo in docs/cli.md
 * Add provider documentation
 * Add --provider option
    The --provider option is constrained to supported providers.
    Providers can be specified in answers.conf. If --provider opt
    is specified it will be overridden. Otherwise the default provider
    is used.

Author: Swapnil Kulkarni <me@coolsvap.net>

* Update tox.ini to execute the pep8 tests
    Currently if i do tox -e pep8
    - it does not run
    - fails to create the test env
    Updated following,
    - tox.ini to include testenv
    Added test-requirements for flake8


## Atomic App 0.1.3 (2015-Aug-17)

This is a hotfix to 0.1.2 and removed a bug we had in [all LABELs of the Dockerfiles](https://github.com/projectatomic/atomicapp/issues/217).


## Atomic App 0.1.2

With this release we have fixed many bugs and implemented many enhancements. To follow
the development in details, please have a look at the [Atomic App Issue tracker](https://github.com/projectatomic/atomicapp/issues/).

This release contains the changes support the deployment of Atomic Apps via [Cockpit web UI](http://cockpit-project.org/).

Starting with 0.1.2 a new LABEL has been added to the docker container image: `io.projectatomic.nulecule.atomicappversion` so that
an external entity can figure out what version of atomicapp is provided by that container image.

A short overview of the major new features is given below.

Author: Subin M <subin@apache.org>

 * add LABEL for atomicapp version to Atomic App Base Container Image

Author: Václav Pavlín <vaclav.pavlin@gmail.com>

 * Create a lock file and fail if it's already locked to prevent concurrent Atomic Apps running

 * Merge pull request #206 from goern/feature/travis-pep8
   [trivial] Feature/travis pep8

 * Merge pull request #169 from sub-mod/cockpit-integration, see https://github.com/cockpit-project/cockpit/pull/2474

 * Add dry-run checks to install

Author: Daniel Veillard <veillard@redhat.com>

 *  Fix a logic bug -  if the id is not found the exception won't be raised by the expected
    code for it but ny the access to the dict in the message before it

Author: Aaron Weitekamp <aweiteka@redhat.com>

 *  Update openshift provider command

 *  OpenShift is now using 'oc', formerly 'osc'.
    This updates the CLI string and also adds support
    for non-root usage. When non-root the oc symlink
    is broken inside the container. In this case we
    create a symlink inside the container.

Author: Christoph Görn <goern@redhat.com>

 * replaces GNU AGPL by GNU LGPL

 *  initial version of python unittest and coveralls based testing
    I removed shell based tests, as they are replaced by python based tests.

 *  using pytest and coverage, converted to a TestSuite
    added an sys.exit() to cli.main.run(), as a CLI should return something.

Author: Ian McLeod <imcleod@redhat.com>

 *  Initial drop of tests for Travis CI

    These two tests take advantage of the --dry-run option as well as the caching of
    previously extracted Docker image content.  If any element of this caching
    behavior is changed, these test will likely need to be recreated.

    The two tests Nulecules are borrowed from the nulecule spec examples here:

    https://github.com/projectatomic/nulecule/tree/master/examples

    I created this test content by doing a dry run on a system actually running
    Docker, then extracting the "external" directory.
