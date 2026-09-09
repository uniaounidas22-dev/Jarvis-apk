"""
JARVIS APP
Interface Kivy que empacota o núcleo (jarvis_core_v2_groq.py) num
app de chat simples para Android.

Fluxo:
- Se não houver chave da Groq salva, mostra uma tela pedindo a chave.
- Depois disso, mostra a tela de chat normal.
- A chave fica salva localmente no aparelho (config.py), nunca no código.
"""

from __future__ import annotations

import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from config import AppConfig
from jarvis_core_v2_groq import JarvisAI, OnlineAIProvider


class SetupScreen(Screen):
    """Primeira tela: pede a chave da API da Groq."""

    def __init__(self, config: AppConfig, on_done, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.on_done = on_done

        root = BoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(16),
        )

        root.add_widget(Label(
            text="[b]Configurar o JARVIS[/b]",
            markup=True,
            font_size="20sp",
            size_hint_y=None,
            height=dp(40),
        ))

        root.add_widget(Label(
            text=(
                "Cole abaixo a sua chave da API da Groq "
                "(console.groq.com -> API Keys).\n"
                "Ela fica salva só neste aparelho."
            ),
            size_hint_y=None,
            height=dp(80),
        ))

        self.key_input = TextInput(
            hint_text="gsk_...",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(48),
        )
        root.add_widget(self.key_input)

        self.status_label = Label(text="", size_hint_y=None, height=dp(30))
        root.add_widget(self.status_label)

        save_btn = Button(text="Salvar e continuar", size_hint_y=None, height=dp(48))
        save_btn.bind(on_press=self.on_save)
        root.add_widget(save_btn)

        root.add_widget(Label())  # espaçador
        self.add_widget(root)

    def on_save(self, *args):
        key = self.key_input.text.strip()
        if not key:
            self.status_label.text = "Cole uma chave válida antes de continuar."
            return

        self.config.groq_api_key = key
        self.on_done()


class ChatScreen(Screen):
    """Tela principal de conversa com o JARVIS."""

    def __init__(self, jarvis: JarvisAI, open_settings, **kwargs):
        super().__init__(**kwargs)
        self.jarvis = jarvis

        root = BoxLayout(orientation="vertical")

        top_bar = BoxLayout(size_hint_y=None, height=dp(48), padding=dp(6))
        top_bar.add_widget(Label(text=f"[b]{jarvis.name}[/b]", markup=True))
        settings_btn = Button(text="Chave API", size_hint_x=0.3)
        settings_btn.bind(on_press=lambda *_: open_settings())
        top_bar.add_widget(settings_btn)
        root.add_widget(top_bar)

        self.history = GridLayout(
            cols=1, size_hint_y=None, spacing=dp(8), padding=dp(8)
        )
        self.history.bind(minimum_height=self.history.setter("height"))

        self.scroll = ScrollView()
        self.scroll.add_widget(self.history)
        root.add_widget(self.scroll)

        input_row = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(6), spacing=dp(6))
        self.input = TextInput(
            hint_text="Fale com o JARVIS...",
            multiline=False,
            size_hint_x=0.8,
        )
        self.input.bind(on_text_validate=self.on_send)

        send_btn = Button(text="Enviar", size_hint_x=0.2)
        send_btn.bind(on_press=self.on_send)

        input_row.add_widget(self.input)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        self.add_widget(root)

        self._add_bubble("JARVIS", f"Olá! Sou o {jarvis.name}. Como posso ajudar?")

    def _add_bubble(self, sender: str, text: str) -> None:
        label = Label(
            text=f"[b]{sender}:[/b] {text}",
            markup=True,
            size_hint_y=None,
            text_size=(Window.width - dp(32), None),
            halign="left",
            valign="top",
        )
        label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(12))
        )
        self.history.add_widget(label)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.05)

    def on_send(self, *args) -> None:
        message = self.input.text.strip()
        if not message:
            return

        self.input.text = ""
        self._add_bubble("Você", message)
        self._add_bubble(self.jarvis.name, "...")
        thinking_label = self.history.children[0]  # último widget adicionado

        def worker() -> None:
            try:
                response = self.jarvis.respond(message)
            except Exception as exc:  # nunca deixar a UI travar
                response = f"Ocorreu um erro: {exc}"

            def update(dt):
                self.history.remove_widget(thinking_label)
                self._add_bubble(self.jarvis.name, response)

            Clock.schedule_once(update)

        threading.Thread(target=worker, daemon=True).start()


class JarvisApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.09, 1)

        self.config_store = AppConfig(self.user_data_dir)
        self.sm = ScreenManager()

        if self.config_store.has_api_key:
            self._go_to_chat()
        else:
            setup = SetupScreen(
                config=self.config_store,
                on_done=self._go_to_chat,
                name="setup",
            )
            self.sm.add_widget(setup)

        return self.sm

    def _build_jarvis(self) -> JarvisAI:
        memory_path = os.path.join(self.user_data_dir, "jarvis_memory.json")
        provider = OnlineAIProvider(api_key=self.config_store.groq_api_key)
        return JarvisAI(memory_file=memory_path, ai_provider=provider)

    def _go_to_chat(self) -> None:
        jarvis = self._build_jarvis()

        # Remove telas antigas de chat, se existirem (ex: ao trocar a chave).
        if self.sm.has_screen("chat"):
            self.sm.remove_widget(self.sm.get_screen("chat"))

        chat = ChatScreen(jarvis=jarvis, open_settings=self._go_to_setup, name="chat")
        self.sm.add_widget(chat)
        self.sm.current = "chat"

    def _go_to_setup(self) -> None:
        if not self.sm.has_screen("setup"):
            setup = SetupScreen(
                config=self.config_store,
                on_done=self._go_to_chat,
                name="setup",
            )
            self.sm.add_widget(setup)
        self.sm.current = "setup"


if __name__ == "__main__":
    JarvisApp().run()
