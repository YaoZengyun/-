from pythonforandroid.recipes.Pillow import PillowRecipe as _Base


class PillowRecipe(_Base):
    # Only override source URL to local archive; keep upstream logic intact
    url = 'file:///home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/android_kivy/Pillow-10.3.0.tar.gz'


recipe = PillowRecipe()
