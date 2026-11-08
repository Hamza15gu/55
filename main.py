import email
import imaplib
import threading
from email.header import decode_header, make_header

from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


def decode(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


class MailApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        self.email_in = TextInput(
            hint_text="Gmail address",
            multiline=False,
            size_hint_y=None,
            height=48,
        )
        self.pass_in = TextInput(
            hint_text="App password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=48,
        )
        self.btn = Button(text="Connect", size_hint_y=None, height=52)
        self.btn.bind(on_release=self.start)

        self.out = Label(
            text="Enter your email and app password.",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        self.out.bind(
            width=lambda *a: setattr(self.out, "text_size", (self.out.width, None)),
            texture_size=lambda *a: setattr(self.out, "height", self.out.texture_size[1]),
        )
        scroll = ScrollView()
        scroll.add_widget(self.out)

        root.add_widget(self.email_in)
        root.add_widget(self.pass_in)
        root.add_widget(self.btn)
        root.add_widget(scroll)
        return root

    def start(self, *args):
        user = self.email_in.text.strip()
        pwd = self.pass_in.text.strip()
        if not user or not pwd:
            self.show("Please fill both fields.")
            return
        self.btn.disabled = True
        self.show("Connecting...")
        threading.Thread(target=self.read_gmail, args=(user, pwd), daemon=True).start()

    @mainthread
    def show(self, text, done=False):
        self.out.text = text
        if done:
            self.btn.disabled = False

    def read_gmail(self, user, pwd):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")
            if status != "OK":
                self.show("Search failed.", done=True)
                return

            nums = messages[0].split()
            lines = [f"Connected. Total messages: {len(nums)}", "", "Latest 5:", ""]

            for num in reversed(nums[-5:]):
                res, data = mail.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
                for part in data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        lines.append("From: " + decode(msg["From"]))
                        lines.append("Subject: " + decode(msg["Subject"]))
                        lines.append("")

            mail.logout()
            self.show("\n".join(lines), done=True)
        except Exception as e:
            self.show(f"Error: {e}", done=True)


if __name__ == "__main__":
    MailApp().run()