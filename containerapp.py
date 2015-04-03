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
    parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), run.ANSWERS_FILE), help="Path to %s" % run.ANSWERS_FILE)

    subparsers = parser.add_subparsers(dest="action")

    parser_create = subparsers.add_parser("create")
    parser_create.add_argument("--schema", default=None, help="Schema for the app spec")
    parser_create.add_argument("NAME", help="App name")

    
    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("-r", "--recursive", dest="recursive", default=True, help="Don't call k8s")
    parser_run.add_argument("APP", nargs="?", help="App to run")
    
    parser_install = subparsers.add_parser("install")

    parser_install.add_argument("-r", "--recursive", dest="recursive", default=True, help="Don't call k8s")
    parser_install.add_argument("-p", "--path", dest="path", default=None, help="Target directory for install")
    parser_install.add_argument("APP",  default=None, help="Name of the image containing your app")
    
    parser_run = subparsers.add_parser("build")
    parser_run.add_argument("TAG", nargs="?", default=None, help="Name of the image containing your app")
    
    


    args = parser.parse_args()
    print(args)
   
    if args.action == "create":
        ac = create.AtomicappCreate(args.NAME, args.schema, args.dryrun)
        ac.create()
    elif args.action == "build":
        if os.path.isfile(os.path.join(os.getcwd(), run.ATOMIC_FILE)):
            with open(os.path.join(os.getcwd(), run.ATOMIC_FILE), "r") as fp:
                data = json.load(fp)
                ac = create.AtomicappCreate(data["id"], args.dryrun)
                ac.build(args.TAG)
    elif args.action == "run" or args.action == "install":
        if not "path" in args:
            args.path = None
        ae = run.Atomicapp(args.answers, args.APP, args.recursive, args.path, args.dryrun, args.debug)
        if args.action == "run":
            ae.run(args.APP)
        else:
            ae.install(args.APP, run.AtomicappLevel.Main)

    sys.exit(0)


