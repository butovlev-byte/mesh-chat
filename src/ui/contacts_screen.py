"""Экран списка контактов / обнаруженных узлов."""
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

from ui.widgets import ContactListItem
from utils.helpers import format_timestamp


class ContactsScreen(MDScreen):
    """Экран контактов и обнаруженных узлов."""

    messaging = ObjectProperty(None)
    dialog = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "contacts"
        self._build_ui()
        Clock.schedule_interval(self._refresh_contacts, 5)

    def _build_ui(self):
        layout = MDBoxLayout(orientation="vertical")

        # Заголовок
        layout.add_widget(MDLabel(
            text="Контакты",
            font_style="H5",
            theme_text_color="Primary",
            size_hint_y=None,
            height="56dp",
            padding=("16dp", "16dp"),
        ))

        # Список
        self.contact_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.contact_list)
        layout.add_widget(scroll)

        # FAB — добавить контакт
        fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"right": 0.95, "y": 0.05},
            on_release=self._show_add_dialog,
        )
        layout.add_widget(fab)

        self.add_widget(layout)

    def on_enter(self):
        self._refresh_contacts()

    def _refresh_contacts(self, dt=None):
        if not self.messaging:
            return
        self.contact_list.clear_widgets()
        contacts = self.messaging.get_contacts()
        for c in contacts:
            item = ContactListItem(
                text=f"{c['display_name']}  ({c['node_id'][:8]}...)",
                secondary_text=f"Последний раз: {format_timestamp(c['last_seen']) if c['last_seen'] else 'никогда'}",
                on_release=lambda x, cid=c['node_id']: self._open_chat(cid),
            )
            self.contact_list.add_widget(item)

    def _open_chat(self, contact_id: str):
        """Переход к чату с контактом."""
        chat_screen = self.manager.get_screen("chat")
        chat_screen.set_contact(contact_id)
        self.manager.current = "chat"

    def _show_add_dialog(self, *args):
        if self.dialog:
            return
        self.dialog = MDDialog(
            title="Добавить контакт",
            type="custom",
            content_cls=MDTextField(hint_text="Node ID или Public Key"),
            buttons=[
                MDFlatButton(text="Отмена", on_release=self._close_dialog),
                MDRaisedButton(text="Добавить", on_release=self._add_contact),
            ],
        )
        self.dialog.open()

    def _close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    def _add_contact(self, *args):
        # TODO: добавление по публичному ключу
        self._close_dialog()
