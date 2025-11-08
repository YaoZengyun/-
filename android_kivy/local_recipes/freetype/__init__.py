from pythonforandroid.recipes.freetype import FreetypeRecipe as _BaseFreetypeRecipe


class FreetypeRecipe(_BaseFreetypeRecipe):
    # Use local tarball to avoid network download
    # Keep version aligned with upstream recipe
    version = '2.10.1'
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/freetype-2.10.1.tar.gz'


recipe = FreetypeRecipe()
