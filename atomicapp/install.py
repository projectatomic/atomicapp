from __future__ import print_function
import os
import distutils.dir_util
import random, string

import subprocess

import logging

from nulecule_base import Nulecule_Base
from utils import Utils
from constants import APP_ENT_PATH, MAIN_FILE

logger = logging.getLogger(__name__)

class Install(object):
    dryrun = False
    params = None
    answers_file = None

    def __init__(self, answers, APP, nodeps = False, update = False, target_path = None, dryrun = False, **kwargs):
        self.dryrun = dryrun
        self.kwargs = kwargs

        app = APP #FIXME

        self.nulecule_base = Nulecule_Base(nodeps, update, target_path)

        if os.path.exists(app):
            logger.info("App path is %s, will be populated to %s", app, target_path)
            app = self._loadApp(app)
        else:
            logger.info("App name is %s, will be populated to %s", app, target_path)

        if not target_path:
            if self.nulecule_base.app_path:
                self.nulecule_base.target_path = self.nulecule_base.app_path
            else:
                self.nulecule_base.target_path = os.getcwd()
        
        self.utils = Utils(self.nulecule_base.target_path)

        self.nulecule_base.app = app

        self.answers_file = answers

    def _loadApp(self, app_path):
        self.nulecule_base.app_path = app_path

        if not os.path.basename(app_path) == MAIN_FILE:
            app_path = os.path.join(app_path, MAIN_FILE)

        mainfile_data = self.nulecule_base.loadMainfile(app_path)
        app = os.environ["IMAGE"] if "IMAGE" in os.environ else mainfile_data["id"]
        logger.debug("Setting path to %s", self.nulecule_base.app_path)

        return app

    def _copyFromContainer(self, image):
        image = self.nulecule_base.getImageURI(image)

        name = "%s-%s" % (self.utils.getComponentName(image), ''.join(random.sample(string.letters, 6)))
        logger.debug("Creating a container with name %s", name)

        create = ["docker", "create", "--name", name, image, "nop"]
        subprocess.call(create)
        cp = ["docker", "cp", "%s:/%s" % (name, APP_ENT_PATH), self.utils.tmpdir]
        logger.debug(cp)
        if not subprocess.call(cp):
            logger.debug("Application entity data copied to %s", self.utils.tmpdir)

        rm = ["docker", "rm", name]
        subprocess.call(rm)

    def _populateApp(self, src = None, dst = None):
        logger.info("Copying app %s", self.utils.getComponentName(self.nulecule_base.app))
        if not src:
            src = os.path.join(self.utils.tmpdir, APP_ENT_PATH)

        if not dst:
            dst = self.nulecule_base.target_path
        distutils.dir_util.copy_tree(src, dst, update=(not self.nulecule_base.update))
        self.nulecule_base.checkAllArtifacts()

    def install(self):
        self.nulecule_base.loadAnswers(self.answers_file)

        if self.nulecule_base.app_path and not self.nulecule_base.target_path == self.nulecule_base.app_path:
            logger.info("Copying content of directory %s to %s", self.nulecule_base.app_path, self.nulecule_base.target_path)
            self._populateApp(src=self.nulecule_base.app_path)

        mainfile_path = os.path.join(self.nulecule_base.target_path, MAIN_FILE)

        if not self.nulecule_base.app_path and (self.nulecule_base.update or not os.path.exists(mainfile_path)):
            self.nulecule_base.pullApp()
            self._copyFromContainer(self.nulecule_base.app)
            mainfile_path = os.path.join(self.utils.getTmpAppDir(), MAIN_FILE)
            logger.debug("%s path for pulled image: %s", MAIN_FILE, mainfile_path)
            self.nulecule_base.loadMainfile(mainfile_path)
            logger.debug("App ID: %s", self.nulecule_base.app_id)

            self._populateApp()
        else:
            logger.info("Component data exist in %s, skipping population...", self.nulecule_base.target_path)

        if not self.nulecule_base.mainfile_data:
            self.nulecule_base.loadMainfile(mainfile_path)

        values = {}
        if not self.nulecule_base.nodeps:
            logger.info("Installing dependencies for %s", self.nulecule_base.app_id)
            values = self._installDependencies()

        logger.debug(values)
        self.nulecule_base.loadAnswers(values)
        logger.debug(self.nulecule_base.answers_data)
        if self.nulecule_base.write_sample_answers:
            self.nulecule_base.writeAnswersSample()

        return values

    def _installDependencies(self):
        values = {}
        for graph_item in self.nulecule_base.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                raise ValueError("Component name missing in graph")

            if not self.utils.isExternal(graph_item):
                values[component] = self.nulecule_base.getValues(component, skip_asking = True)
                logger.debug("Component %s is part of the app", component)
                logger.debug("Values: %s", values)
                continue

            logger.info("Component %s is external dependency", component)

            image_name = self.utils.getSourceImage(graph_item)
            component_path = self.utils.getExternalAppDir(component)
            mainfile_component_path = os.path.join(component_path, MAIN_FILE)
            logger.debug("Component path: %s", component_path)
            if not os.path.isfile(mainfile_component_path) or self.nulecule_base.update:
                logger.info("Pulling %s", image_name)
                component_app = Install(self.nulecule_base.answers_data, image_name, self.nulecule_base.nodeps, 
                                        self.nulecule_base.update, component_path, self.dryrun)
                values = Utils.update(values, component_app.install())
                logger.info("Component installed into %s", component_path)
            else:
                logger.info("Component %s already exists at %s - remove the directory or use --update option", component, component_path)

        return values
