import os
from os.path import join, exists
from shutil import rmtree
from tempfile import mkdtemp
from unittest.mock import MagicMock

from nose.tools import assert_equals, assert_raises

from benchmark.data.pattern import Pattern
from benchmark.subprocesses.tasks.base.project_task import Response
from benchmark.subprocesses.tasks.implementations.detect import Detect, DetectorMode
from benchmark.utils.io import write_yaml
from benchmark_tests.test_utils.data_util import create_project, create_version, create_misuse


# noinspection PyAttributeOutsideInit
class TestDetect:
    def setup(self):
        self.temp_dir = mkdtemp(prefix='mubench-detect-test_')
        self.checkout_base = join(self.temp_dir, "checkout")
        self.findings_file = "findings.yml"
        self.results_path = join(self.temp_dir, "results")

        os.chdir(self.temp_dir)

        self.uut = Detect("detector", self.findings_file, self.checkout_base, self.results_path, 2, None, [], False)

        self.last_invoke = None

        # mock command-line invocation
        def mock_invoke_detector(detect, absolute_misuse_detector_path: str, detector_args: str):
            self.last_invoke = absolute_misuse_detector_path, detector_args

        self.orig_invoke_detector = Detect._invoke_detector
        Detect._invoke_detector = mock_invoke_detector

        # mock path resolving
        def mock_get_misuse_detector_path(detector: str):
            self.last_detector = detector
            return detector + ".jar"

        self.orig_get_misuse_detector_path = Detect._Detect__get_misuse_detector_path
        Detect._Detect__get_misuse_detector_path = mock_get_misuse_detector_path

    def teardown(self):
        Detect._invoke_detector = self.orig_invoke_detector
        Detect._Detect__get_misuse_detector_path = self.orig_get_misuse_detector_path
        rmtree(self.temp_dir, ignore_errors=True)

    def test_invokes_detector(self):
        project = create_project("project")
        version = create_version("0", project=project)

        self.uut.process_project_version(project, version)

        assert_equals(self.last_invoke[0], "detector.jar")

    def test_passes_detect_only_paths(self):
        project = create_project("project")
        misuse = create_misuse("misuse", project=project)
        misuse._PATTERNS = [Pattern("", "")]
        version = create_version("0", misuses=[misuse])
        self.uut.detector_mode = DetectorMode.detect_only

        self.uut.process_project_version(project, version)

        compile = version.get_compile(self.checkout_base)
        self.assert_last_invoke_path_equals(self.uut.key_training_src_path, compile.pattern_sources_path)
        self.assert_last_invoke_path_equals(self.uut.key_training_classpath, compile.pattern_classes_path)
        self.assert_last_invoke_path_equals(self.uut.key_target_src_path, compile.misuse_source_path)
        self.assert_last_invoke_path_equals(self.uut.key_target_classpath, compile.misuse_classes_path)

    def test_passes_mine_and_detect_paths(self):
        project = create_project("project")
        version = create_version("0")
        self.uut.detector_mode = DetectorMode.mine_and_detect

        self.uut.process_project_version(project, version)

        compile = version.get_compile(self.checkout_base)
        self.assert_arg_not_in_last_invoke(self.uut.key_training_src_path)
        self.assert_arg_not_in_last_invoke(self.uut.key_training_classpath)
        self.assert_last_invoke_path_equals(self.uut.key_target_src_path, compile.original_sources_path)
        self.assert_last_invoke_path_equals(self.uut.key_target_classpath, compile.original_classes_path)

    def test_passes_findings_file(self):
        project = create_project("project")
        version = create_version("0", project=project)

        self.uut.process_project_version(project, version)

        self.assert_last_invoke_path_equals(self.uut.key_findings_file,
                                            join(self.results_path, "project", "0", self.findings_file))

    def test_invokes_detector_with_mode(self):
        project = create_project("project")
        version = create_version("0", project=project)
        self.uut.detector_mode = DetectorMode.mine_and_detect

        self.uut.process_project_version(project, version)

        self.assert_last_invoke_path_equals(self.uut.key_detector_mode, '0')

    def test_writes_results(self):
        project = create_project("project")
        version = create_version("0", project=project)

        self.uut.process_project_version(project, version)

        assert exists(join(self.results_path, version.project_id, version.version_id, "run.yml"))

    def test_skips_detect_if_previous_run_succeeded(self):
        project = create_project("project")
        version = create_version("0", project=project)
        write_yaml({"result": "success"},
                   file=join(self.results_path, version.project_id, version.version_id, "run.yml"))
        self.uut._invoke_detector = MagicMock(side_effect=UserWarning)

        self.uut.process_project_version(project, version)

    def test_skips_detect_if_previous_run_was_error(self):
        project = create_project("project")
        version = create_version("0", project=project)
        write_yaml({"result": "error"},
                   file=join(self.results_path, version.project_id, version.version_id, "run.yml"))
        self.uut._invoke_detector = MagicMock(side_effect=UserWarning)

        self.uut.process_project_version(project, version)

    def test_force_detect_on_new_detector(self):
        project = create_project("project")
        version = create_version("0", project=project)
        write_yaml({"result": "success"},
                   file=join(self.results_path, version.project_id, version.version_id, "run.yml"))
        self.uut._new_detector_available = lambda x: True
        self.uut._invoke_detector = MagicMock(side_effect=UserWarning)

        assert_raises(UserWarning, self.uut.process_project_version, project, version)

    def test_skips_detect_only_if_no_patterns_are_available(self):
        project = create_project("project")
        version = create_version("0", project=project)
        self.uut.detector_mode = DetectorMode.detect_only
        self.uut._invoke_detector = MagicMock(side_effect=UserWarning)

        response = self.uut.process_project_version(project, version)

        assert_equals(Response.skip, response)

    def assert_last_invoke_path_equals(self, key, value):
        self.assert_arg_value_equals(self.last_invoke[1], key, '"' + value + '"')

    def assert_arg_not_in_last_invoke(self, key):
        assert key not in self.last_invoke[1]

    @staticmethod
    def assert_arg_value_equals(args, key, value):
        assert key in args, "{} not in {}".format(key, args)
        for i, arg in enumerate(args):
            if arg is key:
                assert_equals(args[i + 1], value)


class TestDetectGetDetectorMode:
    def test_detect_only_for_1(self):
        assert_equals(DetectorMode.detect_only, Detect._get_detector_mode(1))

    def test_mine_and_detect_for_2(self):
        assert_equals(DetectorMode.mine_and_detect, Detect._get_detector_mode(2))

    def test_mine_and_detect_for_3(self):
        assert_equals(DetectorMode.mine_and_detect, Detect._get_detector_mode(3))


class TestDetectDownload:
    # noinspection PyAttributeOutsideInit
    def setup(self):
        self.temp_dir = mkdtemp(prefix='mubench-detect-test_')
        self.checkout_base = join(self.temp_dir, "checkout")
        self.findings_file = "findings.yml"
        self.results_path = join(self.temp_dir, "results")

        self.uut = Detect("detector", self.findings_file, self.checkout_base, self.results_path, 1, None, [], False)
        self.uut._download = MagicMock(return_value=True)

    def test_downloads_detector_if_not_available(self):
        self.uut._detector_available = MagicMock(return_value=False)

        self.uut.start()

        self.uut._download.assert_called_with()
