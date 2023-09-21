import gi
import qrcode

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango
import codex32
import secrets


class Codex32EntryDialog:
    def __init__(self, title="Enter a Codex32 secret or share",
                 text='Type your Codex32 string:', prefill='MS1', indexes=[]):
        self.valid_checksum = True  # Initialize as True
        self.title = title
        self.text = text
        self.prefill = prefill.upper()
        self.indexes = indexes
        self.entry = Gtk.Entry()
        self.entry.set_activates_default(True)
        self.entry.set_text(self.prefill.upper())  # Convert to uppercase
        self.entry.set_position(len(self.prefill) + 1)

    def create_dialog(self):
        dialog = Gtk.Dialog(
            title=self.title,
            buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        dialog.set_default_size(631, -1)

        label = Gtk.Label()
        label.set_text(self.text)

        # Set the width of the entry box in terms of character width
        self.entry.set_width_chars(60)  # Adjust the number as needed

        # Create a Pango font description for monospace font
        font_desc = Pango.FontDescription()
        font_desc.set_family("Monospace")
        font_desc.set_size(Pango.units_from_double(12))

        # Set the font for the entry
        self.entry.modify_font(font_desc)

        # Define custom colors
        red_color = Gdk.RGBA()
        red_color.parse("red")

        green_color = Gdk.RGBA()
        green_color.parse("green")

        def on_entry_changed(entry):
            text = entry.get_text().upper()
            sanitized_text = self.prefill

            for char in text[len(self.prefill):]:
                if char in codex32.CHARSET.upper():
                    sanitized_text += char
                elif char == "?" or char == " ":
                    sanitized_text += char
                # Perform substitutions of non-bech32 characters by
                # visual similarity or qwerty keyboard proximity.
                elif char == "B":
                    sanitized_text += secrets.choice(["8", "G", "N", "?"])
                elif char == "I":
                    sanitized_text += secrets.choice(["L", "U", "?"])
                elif char == "O":
                    sanitized_text += secrets.choice(["0", "L", "P", "?"])
                elif char == "1":
                    sanitized_text += secrets.choice(["L", "2", "Q", "?"])
                elif char == "-":
                    sanitized_text += secrets.choice(["0", "P", "?"])
                elif char == "_" or char == "[" or char == "{":
                    sanitized_text += secrets.choice(["P", "?"])
                elif char == ";" or char == ":":
                    sanitized_text += secrets.choice(["L", "P", "?"])
                elif char == "." or char == '>':
                    sanitized_text += secrets.choice(["L", "?"])
                elif char == "," or char == "<":
                    sanitized_text += secrets.choice(["M", "K", "L", "?"])
                else:
                    sanitized_text += "?"

            entry.set_text(sanitized_text)

            if len(sanitized_text) < len(self.prefill):
                entry.set_text(self.prefill)
            else:
                for i, char in enumerate(self.prefill):
                    if sanitized_text[i] != char:
                        sanitized_text = sanitized_text[
                                         :i] + char + sanitized_text[i:]
                entry.set_text(sanitized_text)

            if entry.get_position() <= len(self.prefill):
                entry.set_position(len(self.prefill))

            codex32_str = sanitized_text.replace(" ", "")
            if len(codex32_str) >= 48:
                if codex32.decode('ms', codex32_str) == (None, None, None, None):
                    # TODO: add a message explaining an invalid checksum.
                    entry.override_color(Gtk.StateFlags.NORMAL, red_color)
                    self.valid_checksum = False
                else:
                    entry.override_color(Gtk.StateFlags.NORMAL, green_color)
                    self.valid_checksum = True
            else:
                if self.valid_checksum or len(codex32_str) == len(self.prefill):
                    entry.override_color(Gtk.StateFlags.NORMAL, None)

        def on_key_release(entry, event):
            # Get the current cursor position
            cursor_position = entry.get_position()
            original_pos = cursor_position

            # Get the current text from the entry and convert it to uppercase
            orig_text = entry.get_text()

            # Count existing spaces before the cursor
            spaces = orig_text[:cursor_position].count(" ")
            cursor_position -= spaces

            # Remove any existing spaces
            text = orig_text.replace(" ", "")

            # Add a space after every 4 non-space characters
            spaced_text = ""
            for i, char in enumerate(text):
                if i > 0 and i % 4 == 0:
                    spaced_text += " "
                    if i < cursor_position:
                        cursor_position += 1
                if i > 0 and i % 24 == 0:
                    spaced_text += " "
                    if i < cursor_position:
                        cursor_position += 1
                spaced_text += char

            if orig_text != spaced_text:
                # Set the modified text back to the entry
                entry.set_text(spaced_text)
                # Set the cursor position back to where it was
                if orig_text[original_pos - 1] == spaced_text[
                    cursor_position - 1]:
                    entry.set_position(cursor_position)
                else:
                    entry.set_position(original_pos)

        def on_scan_button_clicked(button):
            # Add your QR code scanning logic here
            import subprocess
            scan = subprocess.run(['zbarcam', '-1', '--raw', '-Sdisable',
                                   '-Sqrcode.enable'], capture_output=True,
                                  timeout=15)
            if scan.returncode == 0:
                output = scan.stdout
                pos = self.prefill.rfind("1")
                hrp = self.prefill[:pos]
                if len(self.prefill) > pos:
                    k = self.prefill[pos + 1]
                    ident = self.prefix[pos + 2:pos + 6]
                if len(output) == 17:
                    data = codex32.convertbits(output, 8, 5)
                    share_index = codex32.CHARSET[data[0]]
                    if len(self.prefill) > pos:
                        codex32_str = codex32.ms32_encode(hrp, [
                            codex32.CHARSET.find(x.lower()) for x in
                            k + ident + share_index] + data[-1])
                    else:
                        k = '3' if data[-1] else '2'
                        ident = '????'
                        codex32_str = hrp + "1" + k + ident + "".join([codex32.CHARSET[d] for d in data[-1]]) + '?' * 13
                    self.entry.set_text(codex32_str)
                    dialog.response(Gtk.ResponseType.OK)  # press OK button
                elif len(output) > 46:
                    scanned_text = str(output, 'utf')
                    if codex32.decode(hrp, scanned_text) != (None, None, None, None):
                        if ident == codex32.decode(hrp, scanned_text):
                            self.entry.set_text(scanned_text)  # Update the entry
                            dialog.response(Gtk.ResponseType.OK)  # press OK button

        # Connect the signals
        self.entry.connect("key-release-event", on_key_release)
        self.entry.connect("changed", on_entry_changed)

        scan_button = Gtk.Button.new_with_label("Scan QR Code")
        scan_button.connect("clicked", on_scan_button_clicked)

        box = dialog.get_content_area()
        box.add(label)
        box.add(self.entry)
        box.add(scan_button)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            string = self.entry.get_text()
            if not string:
                dialog.destroy()
                return None
            dialog.destroy()
            return string



if __name__ == "__main__":
    dialog = Codex32EntryDialog()
    result = dialog.create_dialog()
    if result:
        print("User entered:", result)
