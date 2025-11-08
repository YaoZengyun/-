from pythonforandroid.recipes.python3 import Python3Recipe as _BasePython3Recipe


class Python3Recipe(_BasePython3Recipe):
    # Force local tarball for CPython source
    version = '3.11.5'
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/Python-3.11.5.tgz'


recipe = Python3Recipe()
