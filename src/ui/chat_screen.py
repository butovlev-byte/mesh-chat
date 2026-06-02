"""Экран чата с конкретным контактом."""
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.toolbar import MDTopAppBar

from ui.widgets import ChatBubble
from utils.helpers import format_timestamp


class ChatScreen(MDScreen):
    """Экран переписки."""

    messaging = ObjectProperty(None)
    current_contact_id = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "chat"
        self._build_ui()
        Clock.schedule_interval(self._refresh_messages, 2)

    def _build_ui(self):
        layout = MDBoxLayout(orientation="vertical")

        # Топ-бар
        self.top_bar = MDTopAppBar(
            title="Чат",
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
            right_action_items=[["information-outline", lambda x: None]],
        )
        layout.add_widget(self.top_bar)

        # Сообщения
        self.messages_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(8),
        )
        self.messages_layout.bind(minimum_height=self.messages_layout.setter("height"))

        scroll = MDScrollView()
        scroll.add_widget(self.messages_layout)
        layout.add_widget(scroll)

        # Поле ввода
        input_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=(dp(8), dp(4)),
            spacing=dp(8),
        )
        self.msg_input = MDTextField(
            hint_text="Сообщение...",
            multiline=False,
            on_text_validate=self._send_message,
        )
        send_btn = MDIconButton(
            icon="send",
            on_release=self._send_message,
        )
        input_box.add_widget(self.msg_input)
        input_box.add_widget(send_btn)
        layout.add_widget(input_box)

        self.add_widget(layout)

    def set_contact(self, contact_id: str):
        """Установка текущего собеседника."""
        self.current_contact_id = contact_id
        contact = self.messaging.db.get_contact(contact_id) if self.messaging else None
        name = contact["display_name"] if contact else contact_id[:8]
        self.top_bar.title = name
        self._refresh_messages()

    def _refresh_messages(self, dt=None):
        if not self.messaging or not self.current_contact_id:
            return
        self.messages_layout.clear_widgets()
        messages = self.messaging.get_chat_history(self.current_contact_id)
        for msg in reversed(messages):  # от старых к новым
            is_me = msg["sender_id"] == self.messaging.my_id
            bubble = ChatBubble(
                text=msg["content"],
                time_str=format_timestamp(msg["timestamp"]) if msg["timestamp"] else "",
                is_me=is_me,
                status="✓✓" if msg.get("delivered") else "✓",
            )
            self.messages_layout.add_widget(bubble)

    def _send_message(self, *args):
        text = self.msg_input.text.strip()
        if not text or not self.messaging or not self.current_contact_id:
            return

        contact = self.messaging.db.get_contact(self.current_contact_id)
        if not contact:
            return

        # Асинхронная отправка
        import asyncio
        asyncio.create_task(
            self.messaging.send_text(
                text,
                self.current_contact_id,
                contact["public_key"],
            )
        )
        self.msg_input.text = ""
        self._refresh_messages()

    def _go_back(self):
        self.manager.current = "contacts"
