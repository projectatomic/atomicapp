from __future__ import print_function
import os
import subprocess
import tempfile

import logging

from constants import PARAMS_FILE, GRAPH_DIR, APP_ENT_PATH, MAIN_FILE, EXTERNAL_APP_DIR, WORKDIR, __NULECULESPECVERSION__

__all__ = ('isTrue', 'Utils')

logger = logging.getLogger(__name__)


true_values = ('true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure')


def isTrue(val):
    return str(val).lower() in true_values


class Utils(object):

    __tmpdir = None
    __workdir = None

    @property
    def workdir(self):
        if not self.__workdir:
            self.__workdir = os.path.join(self.params.target_path, WORKDIR)
            logger.debug(self.__workdir)
            if not os.path.isdir(self.__workdir):
                os.mkdir(self.__workdir)

        return self.__workdir

    @property
    def tmpdir(self):
        if not self.__tmpdir:
            self.__tmpdir = tempfile.mkdtemp(prefix="appent-%s" % self.getComponentName(self.params.app)) #FIXME include the app name!
            logger.info("Using temporary directory %s", self.__tmpdir)

        return self.__tmpdir

    def __init__(self, params, workdir = None):
        self.params = params
        if workdir:
            self.__workdir = workdir

    def loadApp(self, app_path):
        self.params.app_path = app_path
        if not os.path.basename(app_path) == MAIN_FILE:
            app_path = os.path.join(app_path, MAIN_FILE)
        mainfile_data = self.params.loadMainfile(app_path)
        app = os.environ["IMAGE"] if "IMAGE" in os.environ else mainfile_data["id"]
        logger.debug("Setting path to %s", self.params.app_path)

        return app

    def sanitizeName(self, app):
        return app.replace("/", "-")

    def getExternalAppDir(self, component):
        return os.path.join(self.params.target_path, EXTERNAL_APP_DIR, self.getComponentName(component))

    def getComponentDir(self, component):
        return os.path.join(self.params.target_path, GRAPH_DIR, self.getComponentName(component))

    def getProviderDir(self, component):
        return os.path.join(self.params.target_path, GRAPH_DIR, component, self.params.provider)

    def getComponentConf(self, component):
        return os.path.join(self.getComponentDir(component), self.params.provider, PARAMS_FILE)

    def getTmpAppDir(self):
        return os.path.join(self.tmpdir, APP_ENT_PATH)

    def getGraphDir(self):
        return os.path.join(self.params.target_path, GRAPH_DIR)

    @staticmethod
    def getComponentName(graph_item):
        #logger.debug("Getting name for %s", graph_item)
        if type(graph_item) is str or type(graph_item) is unicode:
            return os.path.basename(graph_item).split(":")[0]
        elif type(graph_item) is dict:
            return graph_item["name"].split(":")[0]
        else:
            raise ValueError

    def getComponentImageName(self, graph_item):
        if type(graph_item) is str or type(graph_item) is unicode:
            return graph_item
        elif type(graph_item) is dict:
            repo = ""
            if "repository" in graph_item:
                repo = graph_item["repository"]

            return os.path.join(repo, graph_item["name"])
        else:
            return None

    def getImageURI(self, image):
        config = self.params.get()
        logger.debug(config)

        if "registry" in config:
            logger.info("Adding registry %s for %s", config["registry"], image)
            image = os.path.join(config["registry"], image)

        return image

    def pullApp(self, image):
        image = self.getImageURI(image)
        if not self.params.update:
            check_cmd = ["docker", "images", "-q", image]
            image_id = subprocess.check_output(check_cmd)
            logger.debug("Output of docker images cmd: %s", image_id)
            if len(image_id) != 0:
                logger.debug("Image %s already present with id %s. Use --update to re-pull.", image, image_id.strip())
                return

        pull = ["docker", "pull", image]
        if subprocess.call(pull) != 0:
            raise Exception("Couldn't pull %s" % image)

    def isExternal(self, graph_item):
        logger.debug(graph_item)
        if "artifacts" in graph_item:
            return False

        if not "source" in graph_item:
            return False

        return True

    def getSourceImage(self, graph_item):
        if not "source" in graph_item:
            return None

        if graph_item["source"].startswith("docker://"):
            return graph_item["source"][len("docker://"):]

        return None

    @staticmethod
    def sanitizePath(path):
        if path.startswith("file://"):
            return path[7:]

    def getArtifacts(self, component):
        graph_item = self.getComponent(component)
        if "artifacts" in graph_item:
            return graph_item["artifacts"]

        return None

    def getComponent(self, component):
        for graph_item in self.params.mainfile_data["graph"]:
            name = graph_item.get("name")
            if name is component:
                return graph_item

    def _checkInherit(self, component, inherit_list, checked_providers):
        for inherit_provider in inherit_list:
            if not inherit_provider in checked_providers:
                logger.debug("Checking %s because of 'inherit'", inherit_provider)
                checked_providers += self.checkArtifacts(component, inherit_provider)

    def checkArtifacts(self, component, check_provider = None):
        checked_providers = []
        artifacts = self.getArtifacts(component)
        if not artifacts:
            logger.debug("No artifacts for %s", component)
            return []

        for provider, artifact_list in artifacts.iteritems():
            if (check_provider and not provider == check_provider) or provider in checked_providers:
                continue

            logger.debug("Provider: %s", provider)
            for artifact in artifact_list:
                if "inherit" in artifact:
                    self._checkInherit(component, artifact["inherit"], checked_providers)
                    continue
                path = os.path.join(self.params.target_path, self.sanitizePath(artifact))
                if os.path.isfile(path):
                    logger.debug("Artifact %s: OK", artifact)
                else:
                    raise Exception("Missing artifact %s (%s)" % (artifact, path))
            checked_providers.append(provider)

        return checked_providers

    def checkAllArtifacts(self):
        for graph_item in self.params.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                raise ValueError("Component name missing in graph")

            checked_providers = self.checkArtifacts(component)
            logger.info("Artifacts for %s present for these providers: %s", component, ", ".join(checked_providers))

    def checkSpecVersion(self):
        if not self.params.mainfile_data:
            raise ValueError("Could not access %s data" % MAIN_FILE)

        if "specversion" not in self.params.mainfile_data:
            raise ValueError("Data corrupted: couldn't find specversion in %s" % MAIN_FILE)

        if self.params.mainfile_data["specversion"] == __NULECULESPECVERSION__:
            logger.info("Version check successful: specversion == %s", __NULECULESPECVERSION__)
        else:
            logger.error("Your version in %s file (%s) does not match supported version (%s)", MAIN_FILE, self.params.mainfile_data["specversion"], __NULECULESPECVERSION__)
            raise Exception("Spec version check failed")
