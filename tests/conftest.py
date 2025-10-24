import importlib
import os

import pytest

import shared


# conftest.py is automatically detected by pytest

# 1) Define a command line argument for outdir that is made available to tests via a fixture
# - https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions

def pytest_addoption(parser):
    parser.addoption("--my-outdir", action="store", default="output")


@pytest.fixture(scope='session')
def my_outdir(request):
    outdir = request.config.option.my_outdir
    if outdir is None:
        pytest.skip()
    else:
        try:
            os.mkdir(outdir)
        except Exception:
            pass
    return outdir


# 2) Register a custom marker and use it to skip certain tests depending on graph library installs
# (used in tox system tests to remove a lot of C++ dependencies)
# - http://doc.pytest.org/en/latest/mark.html#registering-marks
# - http://doc.pytest.org/en/latest/example/markers.html#marking-test-functions-and-selecting-them-for-a-run
def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'only_with_graph_libraries: mark test to run only when graph libraries are installed')
    config.addinivalue_line(
        'markers',
        'only_with_selenium: mark test to run only when Selenium is installed')


_GRAPH_LIBRARY_SOURCES = {
    'graph-tool': 'TESTDATA_GRAPH_TOOL',
    'igraph': 'TESTDATA_IGRAPH',
    'NetworKit': 'TESTDATA_NETWORKIT',
    'NetworkX': 'TESTDATA_NETWORKX',
    'Pyntacle (igraph)': 'TESTDATA_PYNTACLE',
    'SNAP': 'TESTDATA_SNAP',
}


def _missing_graph_libraries():
    missing = [
        name for name, attr in _GRAPH_LIBRARY_SOURCES.items()
        if getattr(shared, attr) is None
    ]
    return missing


def _selenium_available():
    try:
        importlib.import_module('selenium')
    except Exception:
        return False
    return True


def pytest_collection_modifyitems(config, items):
    missing_graph_libs = _missing_graph_libraries()
    if missing_graph_libs:
        reason = 'missing optional graph libraries: ' + ', '.join(missing_graph_libs)
        skip_marker = pytest.mark.skip(reason=reason)
        for item in items:
            if 'only_with_graph_libraries' in item.keywords:
                item.add_marker(skip_marker)

    if not _selenium_available():
        skip_marker = pytest.mark.skip(reason='missing optional dependency: selenium')
        for item in items:
            if 'only_with_selenium' in item.keywords:
                item.add_marker(skip_marker)
