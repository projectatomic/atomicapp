"""
 Copyright 2015 Red Hat, Inc.

 This file is part of Atomic App.

 Atomic App is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Atomic App is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public License
 along with Atomic App. If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys

import argparse
import logging
from lockfile import LockFile
from lockfile import AlreadyLocked

from atomicapp import set_logging
from atomicapp.constants import (__ATOMICAPPVERSION__,
                                 __NULECULESPECVERSION__,
                                 ANSWERS_FILE,
                                 ANSWERS_FILE_SAMPLE_FORMAT,
                                 APP_ENT_PATH,
                                 HOST_DIR,
                                 LOCK_FILE,
                                 PROVIDERS)
from atomicapp.nulecule import NuleculeManager
from atomicapp.nulecule.exceptions import NuleculeException
from atomicapp.utils import Utils

logger = logging.getLogger(__name__)


def print_app_location(app_path):
    if app_path.startswith(HOST_DIR):
        app_path = app_path[len(HOST_DIR):]
    print("\nYour application resides in %s" % app_path)
    print("Please use this directory for managing your application\n")


def cli_install(args):
    try:
        argdict = args.__dict__
        nm = NuleculeManager(app_spec=argdict['app_spec'],
                             destination=argdict['destination'],
                             answers_file=argdict['answers'])
        nm.install(**argdict)
        print_app_location(nm.app_path)
        sys.exit(0)
    except NuleculeException as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)


def cli_run(args):
    try:
        argdict = args.__dict__
        nm = NuleculeManager(app_spec=argdict['app_spec'],
                             destination=argdict['destination'],
                             answers_file=argdict['answers'])
        nm.run(**argdict)
        print_app_location(nm.app_path)
        sys.exit(0)
    except NuleculeException as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)


def cli_stop(args):
    try:
        argdict = args.__dict__
        nm = NuleculeManager(app_spec=argdict['app_spec'])
        nm.stop(**argdict)
        sys.exit(0)
    except NuleculeException as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)


class CLI():

    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):

        # We will have a few parsers that we use. The toplevel parser
        # will be the parser that ultimately gets called. It will consist
        # of subparsers for each "action" and each of those subparsers will
        # inherit from a parser for all global options.

        # === TOPLEVEL PARSER ===
        # Create the toplevel parser. This is the one we will return
        toplevel_parser = argparse.ArgumentParser(
            prog='atomicapp',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
            description=(
                "This will install and run an Atomic App, "
                "a containerized application conforming to the Nulecule Specification"))
        # Add a help function to the toplevel parser but don't output
        # help information for it. We need this because of the way we
        # are stitching help output together from multiple parsers
        toplevel_parser.add_argument(
            "-h",
            "--help"
            "--version",
            action='help',
            help=argparse.SUPPRESS)
        # Allow for subparsers of the toplevel_parser. Store the name
        # in the "action" attribute
        toplevel_subparsers = toplevel_parser.add_subparsers(dest="action")

        # === GLOBAL OPTIONS PARSER ===
        # Create the globals argument parser next. This will be a
        # parent parser for the subparsers
        globals_parser = argparse.ArgumentParser(add_help=False)
        globals_parser.add_argument(
            "-V",
            "--version",
            action='version',
            version='atomicapp %s, Nulecule Specification %s' % (
                __ATOMICAPPVERSION__, __NULECULESPECVERSION__),
            help="show the version and exit.")
        globals_parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            default=False,
            action="store_true",
            help="Verbose output mode.")
        globals_parser.add_argument(
            "-q",
            "--quiet",
            dest="quiet",
            default=False,
            action="store_true",
            help="Quiet output mode.")
        globals_parser.add_argument(
            "--dry-run",
            dest="dryrun",
            default=False,
            action="store_true",
            help=(
                "Don't actually call provider. The commands that should be "
                "run will be sent to stdout but not run."))
        globals_parser.add_argument(
            "--answers-format",
            dest="answers_format",
            default=ANSWERS_FILE_SAMPLE_FORMAT,
            choices=['ini', 'json', 'xml', 'yml'],
            help="The format for the answers.conf.sample file. Default: %s" % ANSWERS_FILE_SAMPLE_FORMAT)

        # === "run" SUBPARSER ===
        run_subparser = toplevel_subparsers.add_parser(
            "run", parents=[globals_parser])
        run_subparser.add_argument(
            "-a",
            "--answers",
            dest="answers",
            help="Path to %s" % ANSWERS_FILE)
        run_subparser.add_argument(
            "--write-answers",
            dest="answers_output",
            help="A file which will contain anwsers provided in interactive mode")
        run_subparser.add_argument(
            "--provider",
            dest="cli_provider",
            choices=PROVIDERS,
            help="The provider to use. Overrides provider value in answerfile.")
        run_subparser.add_argument(
            "--ask",
            default=False,
            action="store_true",
            help="Ask for params even if the defaul value is provided")
        run_subparser.add_argument(
            "app_spec",
            help=(
                "Application to run. This is a container image or a path "
                "that contains the metadata describing the whole application."))
        run_subparser.add_argument(
            "--destination",
            dest="destination",
            default=None,
            help="Destination directory for install")
        run_subparser.set_defaults(func=cli_run)

        # === "install" SUBPARSER ===
        install_subparser = toplevel_subparsers.add_parser(
            "install", parents=[globals_parser])
        install_subparser.add_argument(
            "-a",
            "--answers",
            dest="answers",
            help="Path to %s" % ANSWERS_FILE)
        install_subparser.add_argument(
            "--no-deps",
            dest="nodeps",
            default=False,
            action="store_true",
            help="Skip pulling dependencies of the app")
        install_subparser.add_argument(
            "-u",
            "--update",
            dest="update",
            default=False,
            action="store_true",
            help="Re-pull images and overwrite existing files")
        install_subparser.add_argument(
            "--destination",
            dest="destination",
            default=None,
            help="Destination directory for install")
        install_subparser.add_argument(
            "app_spec",
            help=(
                "Application to run. This is a container image or a path "
                "that contains the metadata describing the whole application."))
        install_subparser.set_defaults(func=cli_install)

        # === "stop" SUBPARSER ===
        stop_subparser = toplevel_subparsers.add_parser(
            "stop", parents=[globals_parser])
        stop_subparser.add_argument(
            "--provider",
            dest="cli_provider",
            choices=PROVIDERS,
            help="The provider to use. Overrides provider value in answerfile.")
        stop_subparser.add_argument(
            "app_spec",
            help=(
                "Path to the directory where the Atomic App is installed or "
                "an image containing an Atomic App which should be stopped."))
        stop_subparser.set_defaults(func=cli_stop)

        # Some final fixups.. We want the "help" from the global
        # parser to be output when someone runs 'atomicapp --help'
        # To get that functionality we will add the help from the
        # globals parser to the epilog of the toplevel parser and also
        # suppress the usage message from being output from the
        # globals parser.
        globals_parser.usage = argparse.SUPPRESS
        toplevel_parser.epilog = globals_parser.format_help()

        # Return the toplevel parser
        return toplevel_parser

    def run(self):
        cmdline = sys.argv[1:]  # Grab args from cmdline

        # If we are running in an openshift pod (via `oc new-app`) then
        # there is no cmdline but we want to default to "atomicapp run".
        # In this case copy files to cwd and use the working directory.
        if Utils.running_on_openshift():
            Utils.copy_dir(os.path.join('/', APP_ENT_PATH), './')
            cmdline = 'run --verbose ./'.split()

        # We want to be able to place options anywhere on the command
        # line. We have added all global options to each subparser,
        # but subparsers require all options to be after the 'action'
        # keyword. In order to handle this we just need to figure out
        # what subparser will be used and move it's keyword to the front
        # of the line.
        args, _ = self.parser.parse_known_args(cmdline)
        cmdline.remove(args.action)     # Remove 'action' from the cmdline
        cmdline.insert(0, args.action)  # Place 'action' at front

        # Finally, parse args and give error if necessary
        args = self.parser.parse_args(cmdline)
        if args.verbose:
            set_logging(level=logging.DEBUG)
        elif args.quiet:
            set_logging(level=logging.WARNING)
        else:
            set_logging(level=logging.INFO)

        lock = LockFile(os.path.join(Utils.getRoot(), LOCK_FILE))
        try:
            lock.acquire(timeout=-1)
            args.func(args)
        except AttributeError:
            if hasattr(args, 'func'):
                raise
            else:
                self.parser.print_help()
        except KeyboardInterrupt:
            pass
        except AlreadyLocked:
            logger.error("Could not proceed - there is probably another instance of Atomic App running on this machine.")
        except Exception as ex:
            if args.verbose:
                raise
            else:
                logger.error("Exception caught: %s", repr(ex))
                logger.error(
                    "Run the command again with -v option to get more information.")
        finally:
            if lock.i_am_locking():
                lock.release()


def main():
    cli = CLI()
    cli.run()

if __name__ == '__main__':
    main()
