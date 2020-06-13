# -*- coding: utf-8 -*-

from kivy.lang import Builder
from kivy.properties import ListProperty, OptionProperty, BooleanProperty
from kivy.utils import get_color_from_hex
from kivymd.color_definitions import colors
from kivymd.theming import ThemableBehavior
from kivy.uix.progressbar import ProgressBar


Builder.load_string('''
<MDProgressBar>:
    canvas:
        Clear
        Color:
            rgba:  self.theme_cls.divider_color
        Rectangle:
            size:    (self.width , dp(4)) if self.orientation == 'horizontal' else (dp(4),self.height) 
            pos:   (self.x, self.center_y - dp(4)) if self.orientation == 'horizontal' \
                else (self.center_x - dp(4),self.y)
        
            
        Color:
            rgba:  self.theme_cls.primary_color
        Rectangle:
            size:     (self.width*self.value_normalized, sp(4)) if self.orientation == 'horizontal' else (sp(4), \
                self.height*self.value_normalized)
            pos:    (self.width*(1-self.value_normalized)+self.x if self.reversed else self.x, self.center_y - dp(4)) \
                if self.orientation == 'horizontal' else \
                (self.center_x - dp(4),self.height*(1-self.value_normalized)+self.y if self.reversed else self.y)
<JZWideProgressBar>:
    canvas:
        Clear
        Color:
            rgba:  self.theme_cls.divider_color
        Rectangle:
            size:    (self.width , dp(30)) if self.orientation == 'horizontal' else (dp(30),self.height)
            pos:   (self.x, self.center_y - dp(30)) if self.orientation == 'horizontal' \
                else (self.center_x - dp(30),self.y)


        Color:
            rgba:  self.theme_cls.primary_color
        Rectangle:
            size:     (self.width*self.value_normalized, sp(30)) if self.orientation == 'horizontal' else (sp(30), \
                self.height*self.value_normalized)
            pos:    (self.width*(1-self.value_normalized)+self.x if self.reversed else self.x, self.center_y - dp(30)) \
                if self.orientation == 'horizontal' else \
                (self.center_x - dp(30),self.height*(1-self.value_normalized)+self.y if self.reversed else self.y)

<JZWideRedProgressBar>:
    canvas:
        Clear
        Color:
            rgba:  self.theme_cls.divider_color
        Rectangle:
            size:    (self.width , dp(30)) if self.orientation == 'horizontal' else (dp(30),self.height)
            pos:   (self.x, self.center_y - dp(30)) if self.orientation == 'horizontal' \
                else (self.center_x - dp(30),self.y)


        Color:
            rgba: ((1, 0, 0, 1) if app.obdRPMval > app.obdRPMredline else self.theme_cls.primary_color)
        Rectangle:
            size:     (self.width*self.value_normalized, sp(30)) if self.orientation == 'horizontal' else (sp(30), \
                self.height*self.value_normalized)
            pos:    (self.width*(1-self.value_normalized)+self.x if self.reversed else self.x, self.center_y - dp(30)) \
                if self.orientation == 'horizontal' else \
                (self.center_x - dp(30),self.height*(1-self.value_normalized)+self.y if self.reversed else self.y)

<JZWideCoolantProgressBar>:
    canvas:
        Clear
        Color:
            rgba:  self.theme_cls.divider_color
        Rectangle:
            size:    (self.width , dp(30)) if self.orientation == 'horizontal' else (dp(30),self.height)
            pos:   (self.x, self.center_y - dp(30)) if self.orientation == 'horizontal' \
                else (self.center_x - dp(30),self.y)


        Color:
            #rgba: ((1, 0, 0, 1) if app.obdRPMval > app.obdRPMredline else self.theme_cls.primary_color)
            rgba: ((0, 0, 1, 1) if app.obdcoolanttempval < 190 else ((1, 0, 0, 1) if app.obdcoolanttempval > 220 else (0, 1, 0, 1))) #green normally, red if overheating, blue if cold
        Rectangle:
            size:     (self.width*self.value_normalized, sp(30)) if self.orientation == 'horizontal' else (sp(30), \
                self.height*self.value_normalized)
            pos:    (self.width*(1-self.value_normalized)+self.x if self.reversed else self.x, self.center_y - dp(30)) \
                if self.orientation == 'horizontal' else \
                (self.center_x - dp(30),self.height*(1-self.value_normalized)+self.y if self.reversed else self.y)

        
''')


class MDProgressBar(ThemableBehavior, ProgressBar):
    reversed = BooleanProperty(False)
    ''' Reverse the direction the progressbar moves. '''
    
    orientation = OptionProperty('horizontal', options=['horizontal', 'vertical'])
    ''' Orientation of progressbar'''


class JZWideProgressBar(ThemableBehavior, ProgressBar):
    reversed = BooleanProperty(False)
    ''' Reverse the direction the progressbar moves. '''

    orientation = OptionProperty('horizontal', options=['horizontal', 'vertical'])
    ''' Orientation of progressbar'''

class JZWideRedProgressBar(ThemableBehavior, ProgressBar):
    reversed = BooleanProperty(False)
    ''' Reverse the direction the progressbar moves. '''

    orientation = OptionProperty('horizontal', options=['horizontal', 'vertical'])
    ''' Orientation of progressbar'''

class JZWideCoolantProgressBar(ThemableBehavior, ProgressBar):
    reversed = BooleanProperty(False)
    ''' Reverse the direction the progressbar moves. '''

    orientation = OptionProperty('horizontal', options=['horizontal', 'vertical'])
    ''' Orientation of progressbar'''
            
    
if __name__ == '__main__':
    from kivy.app import App
    from kivymd.theming import ThemeManager
    
    class ProgressBarApp(App):
        theme_cls = ThemeManager()

        def build(self):
            return Builder.load_string("""#:import MDSlider kivymd.slider.MDSlider
BoxLayout:
    orientation:'vertical'
    padding: '8dp'
    MDSlider:
        id:slider
        min:0
        max:100
        value: 40
        
    MDProgressBar:
        value: slider.value
    MDProgressBar:
        reversed: True
        value: slider.value
    BoxLayout:
        MDProgressBar:
            orientation:"vertical"
            reversed: True
            value: slider.value
            
        MDProgressBar:
            orientation:"vertical"
            value: slider.value
        
""")
            

    ProgressBarApp().run()
