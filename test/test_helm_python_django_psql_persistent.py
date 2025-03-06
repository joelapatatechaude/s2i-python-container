import os

import pytest
from pathlib import Path

from container_ci_suite.helm import HelmChartsAPI

test_dir = Path(os.path.abspath(os.path.dirname(__file__)))

VERSION = os.getenv("VERSION")
IMAGE_NAME = os.getenv("IMAGE_NAME")
OS = os.getenv("TARGET")

TAGS = {
    "rhel8": "-ubi8",
    "rhel9": "-ubi9",
    "rhel10": "-ubi10",
}
TAG = TAGS.get(OS, None)
BRANCH_TO_TEST = "master"
if VERSION == "3.11" or VERSION == "3.12":
    BRANCH_TO_TEST = "4.2.x"

class TestHelmPythonDjangoPsqlTemplate:

    def setup_method(self):
        package_name = "redhat-django-psql-persistent"
        path = test_dir
        self.hc_api = HelmChartsAPI(path=path, package_name=package_name, tarball_dir=test_dir, shared_cluster=True)
        self.hc_api.clone_helm_chart_repo(
            repo_url="https://github.com/sclorg/helm-charts", repo_name="helm-charts",
            subdir="charts/redhat"
        )

    def teardown_method(self):
        self.hc_api.delete_project()


    def test_django_psql_curl_output(self, version, branch):

        if self.hc_api.oc_api.shared_cluster:
            pytest.skip("Do NOT test on shared cluster")
        self.hc_api.package_name = "redhat-postgresql-imagestreams"
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation()
        self.hc_api.package_name = "redhat-python-imagestreams"
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation()
        self.hc_api.package_name = "redhat-django-psql-persistent"
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation(
            values={
                "python_version": f"{VERSION}{TAG}",
                "namespace": self.hc_api.namespace,
                "source_repository_ref": BRANCH_TO_TEST,
            }
        )
        assert self.hc_api.is_s2i_pod_running(pod_name_prefix="django-psql")
        assert self.hc_api.test_helm_curl_output(
            route_name="django-psql",
            expected_str="Welcome to your Django application"
        )

    def test_django_psql_helm_test(self, version, branch):
        new_version = VERSION
        if "minimal" in VERSION:
            new_version = VERSION.replace("-minimal", "")
        if OS == "rhel10":
            pytest.skip("Do NOT test on rhel10. Imagestreams are not ready yet.")
        self.hc_api.package_name = "redhat-postgresql-imagestreams"
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation()
        self.hc_api.package_name = "redhat-python-imagestreams"
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation()
        self.hc_api.package_name = "redhat-django-psql-persistent"
        assert self.hc_api.helm_package()
        assert self.hc_api.helm_installation(
            values={
                "python_version": f"{new_version}{TAG}",
                "namespace": self.hc_api.namespace,
                "source_repository_ref": BRANCH_TO_TEST,
            }
        )
        assert self.hc_api.is_s2i_pod_running(pod_name_prefix="django-psql")
        assert self.hc_api.test_helm_chart(expected_str=["Welcome to your Django application"])
