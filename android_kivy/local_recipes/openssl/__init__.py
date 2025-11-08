from pythonforandroid.recipes.openssl import OpenSSLRecipe as _Base


class OpenSSLRecipe(_Base):
    # override versioned_url by overriding url directly
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/android_kivy/openssl-1.1.1w.tar.gz'

    @property
    def versioned_url(self):
        return self.url


recipe = OpenSSLRecipe()
