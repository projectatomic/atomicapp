#!/usr/bin/env python

from __future__ import print_function
import os,sys
import distutils.dir_util

import subprocess

import logging
from pprint import pprint

from params import Params
import utils
from constants import APP_ENT_PATH, ANSWERS_FILE, ATOMIC_FILE, DEFAULT_PROVIDER

logger = logging.getLogger(__name__)


class AtomicappLevel:
    Main, Module = range(2)

class Install():
    dryrun = False
    params = None
    answers_file = None

    def __init__(self, answers, APP, recursive = True, update = False, target_path = None, dryrun = False, **kwargs):
        run_path = os.path.dirname(os.path.realpath(__file__))
        self.dryrun = dryrun

        app = APP #FIXME

        self.params = Params(recursive, update, target_path)
        self.utils = utils.Utils(self.params)

        if os.path.exists(app):
            logger.info("App path is %s, will be populated to %s" % (app, target_path))
            app = self.utils.loadApp(app)
        else:
            logger.info("App name is %s, will be populated to %s" % (app, target_path))
            
        if not target_path:
            if self.params.app_path:
                self.params.target_path = self.params.app_path
            else: 
                self.params.target_path = os.getcwd()

        self.params.app = app

        self.answers_file = answers

    def _copyFromContainer(self, image):
        image = self.utils.getImageURI(image)
        name = self.utils.getComponentName(image)
        
        create = ["docker", "create", "--name", name, image, "nop"]
        subprocess.call(create)
        cp = ["docker", "cp", "%s:/%s" % (name, utils.APP_ENT_PATH), self.utils.tmpdir]
        logger.debug(cp)
        if not subprocess.call(cp):
            logger.debug("Application entity data copied to %s" % self.utils.tmpdir)

        rm = ["docker", "rm", name]
        subprocess.call(rm)

    def _populateMainApp(self, src = None, dst = None):
        logger.info("Copying app %s" % self.utils.getComponentName(self.params.app))
        if not src:
            src = os.path.join(self.utils.tmpdir, APP_ENT_PATH)
            
        if not dst:
            dst = self.params.target_path
        distutils.dir_util.copy_tree(src, dst, update=(not self.params.update))
    
    def _populateModule(self):

        data_list = [
                "graph/%s/" % self.params.app_id,
                "Atomicfile",
                "params.conf"
                ]
        
        logger.info("Populating module %s" % self.utils.getComponentName(self.params.app))
        for item in data_list:
            path = os.path.join(self.utils.tmpdir, APP_ENT_PATH, item)
            if os.path.isdir(path):
                distutils.dir_util.copy_tree(path, self.utils.getComponentDir(self.params.app_id))
            else:
                distutils.file_util.copy_file(path, os.path.join(self.utils.getComponentDir(self.params.app_id), item))

    def install(self, level = AtomicappLevel.Main):

        if not self.params.loadAnswers(self.answers_file):
            logger.info("No %s file found, using defaults" % ANSWERS_FILE)

        if self.params.app_path and not self.params.target_path == self.params.app_path:
            logger.info("Copying content of directory %s to %s" % (self.params.app_path, self.params.target_path))
            self._populateMainApp(src=self.params.app_path)

        atomicfile_path = os.path.join(self.params.target_path, ATOMIC_FILE)
        
        if level == AtomicappLevel.Module:
            atomicfile_path = os.path.join(self.utils.getComponentDir(self.params.app), ATOMIC_FILE)
        
        #logger.debug("Test: %s -> %s" % (self.params.app, ( not self.app_path and not os.path.exists(self.utils.getComponentDir(self.params.app)))))
        if not self.params.app_path and (self.params.update or not os.path.exists(self.utils.getComponentDir(self.params.app))):
            self.utils.pullApp(self.params.app)
            self._copyFromContainer(self.params.app)
            atomicfile_path = os.path.join(self.utils.getTmpAppDir(), ATOMIC_FILE)
            logger.debug("Atomicfile path for pulled image: %s" % atomicfile_path)
            self.params.loadAtomicfile(atomicfile_path)
            logger.debug("App ID: %s" % self.params.app_id)
       
            if level == AtomicappLevel.Main:
                self._populateMainApp()
            elif level == AtomicappLevel.Module:
                self._populateModule()
        else:
            logger.info("Component data exist in %s, skipping population..." % self.utils.getComponentDir(self.params.app))
       
        if not self.params.atomicfile_data:
            self.params.loadAtomicfile(atomicfile_path)

        if self.params.recursive:
            self._installDependencies()

        return self.params.app_id

    def _installDependencies(self):
        for graph_item in self.params.atomicfile_data["graph"]:
            component = self.utils.getComponentName(graph_item)
            component_path = self.utils.getComponentDir(component)
            logger.debug("Component path: %s" % component_path)
            logger.debug("%s == %s -> %s" % (component, self.params.app_id, component == self.params.app_id))
            if not component == self.params.app_id and (not os.path.isdir(component_path) or self.params.update): #not self.params.app_path or  ???

                image_name = self.utils.getComponentImageName(graph_item)
                logger.debug("Pulling %s" % image_name)
                component_atomicapp = Install(self.answers_file, image_name, self.params.recursive, self.params.update, self.params.target_path, self.dryrun)
                component = component_atomicapp.install(AtomicappLevel.Module)
                component_path = self.utils.getComponentDir(component)
                logger.info("Component installed into %s" % component_path)
