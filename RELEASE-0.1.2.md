# Atomic App Base Image 0.1.2

Welcome to Atomic App 0.1.2, this is the reference implementation of the [Container
Application Specification](http://www.projectatomic.io/nulecule/spec/0.0.2/index.html) (aka the Nulecule Specification)

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
