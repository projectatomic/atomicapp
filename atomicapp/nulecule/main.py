# -*- coding: utf-8 -*-
import anymarkup
import copy
import distutils.dir_util
import logging
import os

from atomicapp.constants import (GLOBAL_CONF,
                                 ANSWERS_FILE_SAMPLE_FORMAT,
                                 ANSWERS_FILE,
                                 ANSWERS_FILE_SAMPLE,
                                 ANSWERS_RUNTIME_FILE,
                                 DEFAULT_NAMESPACE,
                                 DEFAULT_PROVIDER,
                                 MAIN_FILE)
from atomicapp.nulecule.base import Nulecule
from atomicapp.utils import Utils

logger = logging.getLogger(__name__)


class NuleculeManager(object):
    """
    Interface to install, run, stop a Nulecule application.
    """

    def __init__(self):
        self.APP = None
        self.answers = {}
        self.answers_format = None

    def unpack(self, image, unpack_path, update=False, dryrun=False,
               nodeps=False, config=None):
        """
        Unpack a Nulecule application from a Nulecule image to a path.

        Args:
            image (str): Name of Nulecule image
            unpack_path (str): Path to unpack the Nulecule image to
            update (bool): Update existing Nulecule application in
                           unpack_path, if True
            dryrun (bool): Do not make any change to the host system
            nodeps (bool): Do not unpack any external dependency
            config (dict): Config data, if any, to use for unpacking

        Returns:
            A Nulecule instance.
        """
        logger.debug('Unpacking %s to %s' % (image, unpack_path))
        if not os.path.exists(os.path.join(unpack_path, MAIN_FILE)) or \
                update:
            logger.debug(
                'Nulecule application found at %s. Unpacking and updating...'
                % unpack_path)
            return Nulecule.unpack(image, unpack_path, nodeps=nodeps,
                                   dryrun=dryrun, update=update)
        else:
            logger.debug(
                'Nulecule application found at %s. Loading...')
            return Nulecule.load_from_path(unpack_path, dryrun=dryrun)

    def install(self, APP, answers, target_path=None, nodeps=False,
                update=False, dryrun=False,
                answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        """
        Instance method of NuleculeManager to install a Nulecule application
        from a local path or a Nulecule image name to specified target path
        or current working directory.

        Args:
            APP (str): Image name or local path
            answers (dict or str): Answers data or local path to answers file
            target_path (str): Path to install a Nulecule application
            nodeps (bool): Install the nulecule application without installing
                           external dependencies
            update (bool): Pull requisite Nulecule image and install or
                           update already installed Nulecule application
            dryrun (bool): Do not make any change to the host system if True
            answers_format (str): File format for writing sample answers file
            kwargs (dict): Extra keyword arguments

        Returns:
            None
        """
        self.answers = Utils.loadAnswers(
            answers or os.path.join(APP, ANSWERS_FILE))
        self.answers_format = answers_format or ANSWERS_FILE_SAMPLE_FORMAT
        target_path = target_path or os.getcwd()
        if os.path.exists(APP):
            Utils.copy_dir(APP, target_path, dryrun=dryrun)
            # Since directory is not copied to target_path during dry run
            # we fall back to load the app from APP.
            self.nulecule = Nulecule.load_from_path(
                APP if dryrun else target_path, dryrun=dryrun, update=update,
                config=self.answers)
        else:
            self.nulecule = self.unpack(APP, target_path, update, dryrun,
                                        config=self.answers)
        self.nulecule.load_config(config=self.nulecule.config,
                                  skip_asking=True)
        runtime_answers = self._get_runtime_answers(
            self.nulecule.config, None)
        # write sample answers file
        self._write_answers(os.path.join(target_path, ANSWERS_FILE_SAMPLE),
                            runtime_answers, answers_format,
                            dryrun=dryrun)

    def run(self, APP, answers, cli_provider, answers_output, ask,
            answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        """
        Instance method of NuleculeManager to run a Nulecule application from
        a local path or a Nulecule image name.

        Args:
            APP (str): Image name or local path
            answers (dict or str): Answers data or local path to answers file
            cli_provider (str): Provider to use to run the Nulecule
                                application
            answers_output (str): Path to file to export runtime answers data
                                  to
            ask (bool): Ask for values for params with default values from
                        user, if True
            answers_format (str): File format for writing sample answers file
            kwargs (dict): Extra keyword arguments

        Returns:
            None
        """
        self.answers = Utils.loadAnswers(
            answers or os.path.join(APP, ANSWERS_FILE))
        self.answers_format = answers_format or ANSWERS_FILE_SAMPLE_FORMAT
        dryrun = kwargs.get('dryrun') or False
        if os.path.exists(APP):
            self.nulecule = Nulecule.load_from_path(APP, config=self.answers,
                                                    dryrun=dryrun)
            app_path = APP
        else:
            app_path = os.getcwd()
            self.nulecule = Nulecule.unpack(APP, app_path, update=True,
                                            dryrun=dryrun,
                                            config=self.answers)
        self.nulecule.load_config(config=self.nulecule.config, ask=ask)
        self.nulecule.render(cli_provider, dryrun)
        self.nulecule.run(cli_provider, dryrun)
        runtime_answers = self._get_runtime_answers(
            self.nulecule.config, cli_provider)
        self._write_answers(os.path.join(app_path, ANSWERS_RUNTIME_FILE),
                            runtime_answers,
                            self.answers_format, dryrun=dryrun)
        if answers_output:
            self._write_answers(answers_output, runtime_answers,
                                self.answers_format, dryrun)

    def stop(self, APP, cli_provider, **kwargs):
        """
        Instance method of NuleculeManager to stop a running Nulecule
        application.

        Args:
            APP (str): Local path to installed Nulecule application
            cli_provider (str): Provider running the Nulecule application
            kwargs (dict): Extra keyword arguments
        """
        self.answers = Utils.loadAnswers(
            os.path.join(APP, ANSWERS_RUNTIME_FILE))
        dryrun = kwargs.get('dryrun') or False
        self.nulecule = Nulecule.load_from_path(APP, config=self.answers,
                                                dryrun=dryrun)
        self.nulecule.load_config(config=self.answers)
        self.nulecule.render(cli_provider, dryrun=dryrun)
        self.nulecule.stop(cli_provider, dryrun)

    def uninstall(self):
        # For future use
        self.stop()
        self.nulecule.uninstall()

    def clean(self, force=False):
        # For future use
        self.uninstall()
        distutils.dir_util.remove_tree(self.unpack_path)
        self.initialize()

    def _write_answers(self, path, answers, answers_format, dryrun=False):
        """
        Write answers data to file.

        Args:
            path (str): path to answers file to write to
            answers (dict): Answers data
            answers_format (str): Format to use to dump answers data to file,
                                  e.g., json
            dryrun (bool): Do not make any change to the host system,
                           while True

        Returns:
            None
        """
        if not dryrun:
            anymarkup.serialize_file(
                answers, path, format=answers_format)
        else:
            logger.info('ANSWERS: %s' % answers)

    def _get_runtime_answers(self, config, cli_provider):
        """
        Get runtime answers data from config (Nulecule config) by adding
        default data if missing.

        Args:
            config (dict): Nulecule config data
            cli_provider (str): Provider used for running Nulecule application

        Returns:
            dict
        """
        _config = copy.deepcopy(config)
        _config[GLOBAL_CONF] = config.get(GLOBAL_CONF) or {}
        _config[GLOBAL_CONF]['provider'] = cli_provider or \
            _config[GLOBAL_CONF].get('provider') or DEFAULT_PROVIDER
        _config[GLOBAL_CONF]['namespace'] = _config[GLOBAL_CONF].get(
            'namespace') or DEFAULT_NAMESPACE
        return _config
