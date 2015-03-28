#!/usr/bin/python

import run
import create
import os, sys, json
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

if __name__ == "__main__":
    parser = ArgumentParser(description='TBD', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug")
    parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't call k8s")
    subparsers = parser.add_subparsers(dest="action")
    parser_create = subparsers.add_parser("create")
    parser_create.add_argument("NAME", help="App name")

    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), run.ANSWERS_FILE), help="Path to %s" % run.ANSWERS_FILE)
    parser_run.add_argument("APP", help="App to run")

    
    parser_run = subparsers.add_parser("build")
    parser_run.add_argument("TAG", nargs="?", default=None, help="Name of the image containing your app")


    args = parser.parse_args()
    print(args)
   
    if args.action == "create":
        ac = create.AtomicappCreate(args.NAME, args.dryrun)
        ac.create()
    elif args.action == "build":
        if os.path.isfile(os.path.join(os.getcwd(), run.ATOMIC_FILE)):
            with open(os.path.join(os.getcwd(), run.ATOMIC_FILE), "r") as fp:
                data = json.load(fp)
                ac = create.AtomicappCreate(data["id"], args.dryrun)
                ac.build(args.TAG)
    elif args.action == "run":
        ae = run.Atomicapp(args.answers, args.APP, args.dryrun, args.debug)
        ae.run(args.APP)

    sys.exit(0)


