"""Кастомные виджеты KivyMD."""
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, ILeftBody
from kivymd.uix.button import MDIconButton


class ChatBubble(MDCard):
    """Пузырёк сообщения — слева (чужое) или справа (своё)."""
    text = StringProperty("")
    time_str = StringProperty("")
    is_me = BooleanProperty(False)
    status = StringProperty("")  # sent, delivered, read

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.width = dp(280)
        self.adaptive_height = True
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.padding = dp(10)
        self.spacing = dp(4)
        self.elevation = 1

        if self.is_me:
            self.md_bg_color = (0.38, 0.0, 0.93, 1)  # Primary
            self.pos_hint = {"right": 1}
        else:
            self.md_bg_color = (0.15, 0.15, 0.2, 1)  # Dark surface
            self.pos_hint = {"x": 0}

        self.add_widget(MDLabel(
            text=self.text,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1) if self.is_me else (0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=self.texture_size[1],
        ))

        footer = BoxLayout(size_hint_y=None, height=dp(16))
        footer.add_widget(MDLabel(
            text=self.time_str,
            font_style="Caption",
            theme_text_color="Secondary",
            halign="right",
        ))
        self.add_widget(footer)


class ContactListItem(OneLineAvatarIconListItem):
    """Элемент списка контактов."""
    node_id = StringProperty("")
    last_seen = StringProperty("")
    online = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._txt_left_pad = dp(72)


class StatusIndicator(ILeftBody, MDIconButton):
    """Индикатор статуса онлайн."""
    pass
