import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango
import codex32
import secrets

class Codex32EntryDialog:
    def __init__(self, title="Enter a codex32 secret or share", prefill='MS1',
                 text='Type your codex32 string:', used_indexes=[]):
        self.valid_checksum = False
        self.title = title
        self.text = text
        self.prefill = prefill.upper()
        self.used_indexes = used_indexes
        self.entry = Gtk.Entry()
        self.entry.set_activates_default(True)
        self.entry.set_text(self.prefill.upper())
        self.entry.set_position(len(self.prefill) + 1)
        self.ok_button = Gtk.Button.new_with_label("Submit")
        self.window = Gtk.Window(title=f"Enter your codex32")

    def on_dialog_response(self, dialog, response_id):
        # Handle the response types
        if response_id == Gtk.ResponseType.CANCEL or response_id == Gtk.ResponseType.DELETE_EVENT:
            # Close the dialog when Cancel is clicked
            dialog.destroy()
    def create_dialog(self):
        entry = Gtk.Dialog(
            title=self.title,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        )
        entry.set_default_size(631, -1)
        entry.get_action_area().add(self.ok_button)
        entry.connect("response", self.on_dialog_response)

        def on_ok_button_clicked(button):
            if self.valid_checksum:
                entry.response(Gtk.ResponseType.OK)
            else:
                Gtk.window("Display the closest correction")
        def on_entry_activate(entry):
            if self.ok_button.get_sensitive():
                self.ok_button.clicked()

        self.ok_button.connect("clicked", on_ok_button_clicked)
        self.ok_button.set_sensitive(False)
        self.entry.connect("activate", on_entry_activate)

        label = Gtk.Label()
        label.set_text(self.text)

        # Set the width of the entry box in terms of character width
        self.entry.set_width_chars(60)  # Adjust the number as needed

        # Create a Pango font description for monospace font
        font_desc = Pango.FontDescription()
        font_desc.set_family("Monospace")
        font_desc.set_size(Pango.units_from_double(12))

        self.entry.modify_font(font_desc)

        red_color = Gdk.RGBA()
        red_color.parse("red")
        green_color = Gdk.RGBA()
        green_color.parse("green")

        def on_entry_changed(entry):
            pos = self.prefill.rfind("1")
            text = entry.get_text().upper()
            sanitized_text = self.prefill
            if len(text) > pos + 1:
                char = text[pos + 1]
                if char not in ['0', '2', '3', '4', '5', '6', '7', '8', '9', '?']:
                    # Perform substitutions of non-threshold characters
                    # by visual similarity or qwerty keyboard proximity.
                    if char == '1':
                        corr_char = secrets.choice(['2', '?'])
                    elif char == 'Q':
                        corr_char = secrets.choice(['2', '?'])
                    elif char == 'W':
                        corr_char = secrets.choice(['2', '2', '3', '?'])
                    elif char == 'E':
                        corr_char = secrets.choice(['3', '3', '4', '?'])
                    elif char == 'R':
                        corr_char = secrets.choice(['4', '5', '?'])
                    elif char == 'S':
                        corr_char = secrets.choice([ '5', '?'])
                    elif char == 'T':
                        corr_char = secrets.choice(['3', '5', '6', '7', '?'])
                    elif char == 'Y':
                        corr_char = secrets.choice(['6', '7', '?'])
                    elif char == 'U':
                        corr_char = secrets.choice(['2', '7', '8', '?'])
                    elif char == 'I':
                        corr_char = secrets.choice(['8', '9', '?'])
                    elif char == 'O':
                        corr_char = secrets.choice(['0', '0', '9', '?'])
                    elif char == 'G':
                        corr_char = secrets.choice(['9', '?'])
                    elif char == 'D':
                        corr_char = secrets.choice(['0', '?'])
                    elif char == 'P':
                        corr_char = secrets.choice(['3', '0', '?'])
                    elif char == '-':
                        corr_char = secrets.choice(['0', '?'])
                    else:
                        corr_char = '?'
                    text = text[:pos + 1] + corr_char + text[pos + 2:]

            if len(text) > 10 and text[10] in self.used_indexes:
                dialog = Gtk.MessageDialog(
                    parent=None,
                    flags=Gtk.DialogFlags.MODAL,
                    type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    message_format="The share index you're entering appears to be a repeat. Continue?"
                )
                dialog.set_title("Confirm Share Index")
                response = dialog.run()
                repeating = False  # Default to False
                if response == Gtk.ResponseType.YES:
                    repeating = True
                dialog.destroy()
                if repeating:
                    text = text[:10] + '?' + text[11:]
                else:
                    text = text[:10] + text[11:]
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
            if len(codex32_str) > 43: # change to if checksum passes or a correction is found that passes
                self.ok_button.set_sensitive(True)

            else:
                self.ok_button.set_sensitive(False)
            try:
                codex32.Codex32.decode(codex32_str)
                entry.override_color(Gtk.StateFlags.NORMAL, green_color)
                self.valid_checksum = True
                self.ok_button.set_label("Submit")
                self.ok_button.grab_focus()
            except Exception as e:
                print(e)
                self.valid_checksum = False
                if str(e) == "Decoding failed: Invalid length" or "Parsing failed: Data part is too short, no threshold parameter found":
                    entry.override_color(Gtk.StateFlags.NORMAL, None)
                else:
                    warning_popup('ERROR', e)
                    # TODO: add a message explaining an invalid checksum.
                    entry.override_color(Gtk.StateFlags.NORMAL, red_color)
                    self.ok_button.set_label("Suggest Correction")
            if len(codex32_str) == len(self.prefill):
                entry.override_color(Gtk.StateFlags.NORMAL, None)
                self.ok_button.set_label("Submit")
            self.valid_checksum = False


        def space_text(entry):
            # Get the current text from the entry and convert it to uppercase
            orig_text = entry.get_text().upper()

            # Remove any existing spaces
            text = orig_text.replace(" ", "")

            # Add a space after every 4 non-space characters
            spaced_text = ""
            for i, char in enumerate(text.upper()):
                if i > 0 and i % 4 == 0:
                    spaced_text += " "
                if i > 0 and i % 24 == 0:
                    spaced_text += " "
                spaced_text += char

            if orig_text != spaced_text:
                # Set the modified text back to the entry
                entry.set_text(spaced_text)

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
                                   '-Sqrcode.enable'], capture_output=True, timeout=20)
            if scan.returncode == 0:
                output = scan.stdout
                scanned_text = str(output, 'utf')
                pos = self.prefill.rfind("1")
                hrp = self.prefill[:pos]
                if len(self.prefill) > pos + 1:
                    k = self.prefill[pos + 1]
                    ident = self.prefix[pos + 2:pos + 6]
                else:
                    k = '?'
                    ident = '????'
                if len(scanned_text) == 25:
                    codex32_str = codex32.decode_compact_qr(hrp, k, ident, scanned_text)
                    if codex32_str is None:
                        return header_mismatch()
                    if codex32_str[-40] in self.used_indexes:
                        return index_reused()
                    self.entry.set_text(codex32_str)
                    entry.response(Gtk.ResponseType.OK)  # press OK button
                elif len(scanned_text) > 46:
                    if len(scanned_text) < 48:
                        for last_char in codex32.CHARSET:
                            if codex32.decode(hrp, scanned_text+last_char) != (None, None, None, None):
                                scanned_text += last_char
                                break
                    if codex32.decode(hrp, scanned_text) != (None, None, None, None):
                        scanned_k, scanned_ident, share_index, _ = codex32.decode(hrp, scanned_text)
                        if share_index in self.used_indexes:
                            return index_reused()
                        if scanned_k != k or scanned_ident != ident:
                            return header_mismatch()
                        self.entry.set_text(scanned_text)  # Update the entry
                        entry.response(Gtk.ResponseType.OK)  # press OK button
        
        def warning_popup(title, msg):
            warning = Gtk.MessageDialog(
                parent=None,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=msg
            )
            warning.set_title(title)
            warning.run()
            warning.destroy()
        
        def index_reused():
            msg = "The share you've scanned is a repeat."
            title = "Scan a fresh share index"

        def header_mismatch():
            msg = "The header of your scanned share does not match previous shares."
            title = "Mismatched share scanned"
            warning_popup(title, msg)


        # Connect the signals
        self.entry.connect("key-release-event", on_key_release)
        self.entry.connect("changed", on_entry_changed)

        scan_button = Gtk.Button.new_with_label("Scan QR Code")
        scan_button.connect("clicked", on_scan_button_clicked)

        box = entry.get_content_area()
        box.add(label)
        box.add(self.entry)
        box.add(scan_button)
        entry.show_all()

        response = entry.run()
        if response == Gtk.ResponseType.OK:
            bech32_string = self.entry.get_text().replace(" ", "")
            string = ""
            for i, char in enumerate(bech32_string):
                if i > 0 and i % 4 == 0:
                    string += " "
                if i > 0 and i % 24 == 0:
                    string += " "
                string += char
            if not string:
                entry.destroy()
                return None
            entry.destroy()
            new_prefill = string[:10]
            return bech32_string, new_prefill
        
if __name__ == "__main__":
    dialog = Codex32EntryDialog()
    dialog_window = dialog.create_dialog()
    dialog_window.run()
    Gtk.main()
