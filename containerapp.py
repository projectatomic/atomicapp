#!/usr/bin/python

import run
import create
import os, sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

class ContainerApp():
    def __init__(self):
        pass

    def a():
        print "aaa"



if __name__ == "__main__":
    parser = ArgumentParser(description='TBD', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug")
    parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't call k8s")
    subparsers = parser.add_subparsers(dest="action")
    parser_create = subparsers.add_parser("create")
    parser_create.add_argument("NAME", help="App name")

    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), run.ANSWERS_FILE), help="Path to %s" % run.ANSWERS_FILE)
    parser_run.add_argument("app", help="App to run")

    args = parser.parse_args()
   
    if args.action == "create":
        ac = create.AtomicappCreate(args.NAME)
        ac.create()
    elif args.action == "run":
        ae = run.Atomicapp(args.answers, args.app, args.dryrun, args.debug)
        ae.run(args.app)

    sys.exit(0)


