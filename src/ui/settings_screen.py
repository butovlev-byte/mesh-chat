"""Экран настроек и информации о сети."""
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton

from utils.helpers import get_local_ip


class SettingsScreen(MDScreen):
    """Экран настроек MeshChat."""

    crypto = ObjectProperty(None)
    mesh = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
        self._build_ui()
        Clock.schedule_interval(self._refresh_stats, 3)

    def _build_ui(self):
        layout = MDBoxLayout(orientation="vertical")

        layout.add_widget(MDLabel(
            text="Настройки",
            font_style="H5",
            theme_text_color="Primary",
            size_hint_y=None,
            height="56dp",
            padding=("16dp", "16dp"),
        ))

        self.settings_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.settings_list)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def on_enter(self):
        self._refresh_stats()

    def _refresh_stats(self, dt=None):
        self.settings_list.clear_widgets()

        # Мой ID
        if self.crypto:
            self.settings_list.add_widget(TwoLineListItem(
                text="Мой Node ID",
                secondary_text=self.crypto.node_id,
            ))
            self.settings_list.add_widget(OneLineListItem(
                text="Публичный ключ (нажми чтобы скопировать)",
                on_release=lambda x: self._copy_pubkey(),
            ))

        # Сеть
        self.settings_list.add_widget(TwoLineListItem(
            text="Локальный IP",
            secondary_text=get_local_ip(),
        ))

        if self.mesh:
            peers_count = len(self.mesh.peers)
            self.settings_list.add_widget(TwoLineListItem(
                text="Активные пиры",
                secondary_text=str(peers_count),
            ))

        # Кнопки
        self.settings_list.add_widget(MDRaisedButton(
            text="Очистить БД",
            on_release=self._clear_db,
            pos_hint={"center_x": 0.5},
        ))

    def _copy_pubkey(self):
        """Копирование публичного ключа в буфер обмена."""
        if self.crypto:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.crypto.public_key_pem)

    def _clear_db(self, *args):
        """Очистка базы данных."""
        # TODO: диалог подтверждения
        pass
