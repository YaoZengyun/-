from pythonforandroid.recipes.sdl2_image import LibSDL2Image as _BaseLibSDL2Image


class LibSDL2Image(_BaseLibSDL2Image):
    # Use local tarball and avoid external downloads
    version = '2.8.0'
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/android_kivy/SDL2_image-2.8.0.tar.gz'

    # Disable patches to avoid looking for enable-webp.patch in this local dir
    patches = []

    def prebuild_arch(self, arch):
        # Intentionally skip external deps download and don't call base prebuild_arch,
        # which would try to execute download.sh.
        # Most BootstrapNDKRecipe prebuild is a no-op here, so we just pass.
        pass


recipe = LibSDL2Image()
