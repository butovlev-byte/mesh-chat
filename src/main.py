"""MeshChat — точка входа приложения."""
import asyncio
import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "700")
Config.set("graphics", "resizable", False)

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.clock import Clock
from kivy.properties import ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import OneLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel

from crypto_utils import CryptoManager
from database import Database
from mesh_network import MeshNetwork
from messaging import MessagingService

from ui.contacts_screen import ContactsScreen
from ui.chat_screen import ChatScreen
from ui.settings_screen import SettingsScreen


KV = """
BoxLayout:
    orientation: "vertical"

    MDTopAppBar:
        id: top_bar
        title: "MeshChat"
        elevation: 4
        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]

    ScreenManager:
        id: screen_manager
        transition: FadeTransition(duration=0.2)

    MDNavigationDrawer:
        id: nav_drawer
        radius: (0, 16, 16, 0)

        MDBoxLayout:
            orientation: "vertical"
            padding: "8dp"
            spacing: "8dp"

            MDLabel:
                text: "MeshChat"
                font_style: "H6"
                size_hint_y: None
                height: self.texture_size[1]
                padding: "16dp", "16dp"

            MDLabel:
                text: "P2P Messenger"
                font_style: "Caption"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: self.texture_size[1]
                padding: "16dp", 0

            MDSeparator:

            ScrollView:
                MDList:
                    OneLineListItem:
                        text: "Контакты"
                        on_release:
                            app.switch_screen("contacts")
                            nav_drawer.set_state("close")

                    OneLineListItem:
                        text: "Настройки"
                        on_release:
                            app.switch_screen("settings")
                            nav_drawer.set_state("close")

                    OneLineListItem:
                        text: "О приложении"
                        on_release:
                            app.show_about()
                            nav_drawer.set_state("close")
"""


class MeshChatApp(MDApp):
    """Главное приложение MeshChat."""

    crypto = ObjectProperty(None)
    mesh = ObjectProperty(None)
    messaging = ObjectProperty(None)
    db = ObjectProperty(None)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Teal"

        # Инициализация подсистем
        self._init_core()

        # UI
        self.root = Builder.load_string(KV)
        self.screen_manager = self.root.ids.screen_manager
        self._init_screens()

        # Запуск mesh-сети
        Clock.schedule_once(self._start_network, 1)

        return self.root

    def _init_core(self):
        """Инициализация крипто, БД и сети."""
        self.crypto = CryptoManager()
        self.db = Database()
        self.mesh = MeshNetwork(self.crypto.node_id, self.crypto)
        self.messaging = MessagingService(self.crypto, self.mesh, self.db)

        # Подписка на входящие сообщения
        self.mesh.add_message_callback(self.messaging.on_message_received)

        print(f"[App] Node ID: {self.crypto.node_id}")

    def _init_screens(self):
        """Создание экранов."""
        contacts = ContactsScreen(name="contacts")
        contacts.messaging = self.messaging
        self.screen_manager.add_widget(contacts)

        chat = ChatScreen(name="chat")
        chat.messaging = self.messaging
        self.screen_manager.add_widget(chat)

        settings = SettingsScreen(name="settings")
        settings.crypto = self.crypto
        settings.mesh = self.mesh
        self.screen_manager.add_widget(settings)

        self.screen_manager.current = "contacts"

    def _start_network(self, dt):
        """Запуск mesh-сети в фоновом потоке."""
        import threading
        self._network_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._network_thread.start()
        print("[App] Mesh-сеть запущена")

    def _run_async_loop(self):
        """Собственный asyncio event loop для mesh-сети."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def main():
            await asyncio.gather(
                self.mesh.start_server(),
                self.mesh.start_discovery(),
                self.mesh.start_bluetooth_server(),
            )

        try:
            loop.run_until_complete(main())
        except Exception as e:
            print(f"[App] Network error: {e}")
        finally:
            loop.close()

    def switch_screen(self, name: str):
        """Переключение экрана."""
        if self.screen_manager.has_screen(name):
            self.screen_manager.current = name

    def show_about(self):
        """Диалог 'О приложении'."""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        dialog = MDDialog(
            title="О MeshChat",
            text=(
                "🔗 MeshChat v1.0\n"
                "Децентрализованный P2P мессенджер\n\n"
                "• Mesh-сеть через Wi-Fi/Bluetooth\n"
                "• ECIES шифрование\n"
                "• Без серверов и интернета"
            ),
            buttons=[MDFlatButton(text="Закрыть", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def on_stop(self):
        """При закрытии приложения."""
        if self.mesh:
            self.mesh.stop()
        print("[App] MeshChat остановлен")


if __name__ == "__main__":
    MeshChatApp().run()
