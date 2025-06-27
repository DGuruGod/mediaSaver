from kivymd.uix.progressbar import MDProgressBar
from kivy.animation import Animation

class AnimatedProgressBar(MDProgressBar):
    def animate_complete(self):
        Animation.cancel_all(self, 'value')
        self.color = [0, 1, 0, 1]  # green
        anim = Animation(value=100, duration=0.5)
        anim.start(self)

    def animate_indeterminate(self):
        self.color = [0, 0.5, 1, 1]  # blue loading
        self.value = 0
        anim = Animation(value=100, duration=1)
        anim += Animation(value=0, duration=0)
        anim.repeat = True
        anim.start(self)

    def reset(self):
        Animation.cancel_all(self, 'value')
        self.value = 0
        self.color = [0, 0.5, 1, 1]

