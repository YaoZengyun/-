from pythonforandroid.recipes.sdl2_image import LibSDL2Image as _BaseLibSDL2Image
from pythonforandroid.recipe import Recipe


class LibSDL2Image(_BaseLibSDL2Image):
    # Override to use local tarball instead of network and skip external git downloads
    version = '2.8.0'
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/android_kivy/SDL2_image-2.8.0.tar.gz'

    # Keep patches list from base so WEBP stays enabled; copy patch file into local dir separately
    patches = ['enable-webp.patch']

    def prebuild_arch(self, arch):  # noqa: D401
        # Skip running download.sh (offline environment); rely on system libjpeg/libpng already provided.
        # Call super only to proceed with standard prebuild logic minus external downloads.
        # We deliberately DO NOT invoke the original download script.
        super(_BaseLibSDL2Image, self).prebuild_arch(arch)


recipe = LibSDL2Image()
