from pythonforandroid.recipes.hostpython3 import HostPython3Recipe as _BaseHostPython3Recipe


class HostPython3Recipe(_BaseHostPython3Recipe):
    # Force local tarball for hostpython build
    version = '3.11.5'
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/Python-3.11.5.tgz'


recipe = HostPython3Recipe()
