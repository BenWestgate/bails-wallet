import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
import difflib
import sys

class EntryWindow(Gtk.Window):
    def __init__(self, correct_string, progress=''):
        self.string_type = "share" if int(correct_string[3]) else "secret"
        Gtk.Window.__init__(self, title=f"Enter your codex32 {self.string_type} {progress}")
        self.set_border_width(10)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.add(hbox)
        self.entry_boxes = []
        self.correct_string = correct_string.upper()
        self.progress = progress
        self.universal_pos = 0
        self.bad_boxes = []
        self.words = (len(correct_string) + 3) // 4

        # Set a monospace font
        font_desc = Pango.FontDescription("Monospace 17")

        for i in range(self.words):
            entry = Gtk.Entry()
            entry.set_max_length(5)
            if i == self.words - 1:
                entry.set_max_length(4)
            entry.set_width_chars(4)  # Set width_chars to 4
            entry.override_font(font_desc)  # Set the font
            entry.connect("changed", self.on_entry_changed)
            entry.connect("key-press-event", self.on_key_press) # Use key-press-event
            entry.connect("key-release-event", self.on_key_release) # Use this for Del and Backspace

            if i == self.words // 2:
                hbox.pack_start(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
            hbox.pack_start(entry, True, True, 0)

            self.entry_boxes.append(entry)
            self.connect("delete-event", self.on_delete_event)


    def get_full_text(self):
        full_text = ""
        for entry in self.entry_boxes:
            text = entry.get_text()
            full_text += text
        return full_text

    def set_full_text(self,new_full_text=''):
        for i, entry in enumerate(self.entry_boxes):
            entry.set_text(new_full_text[i*4:i*4+4])

    def set_cursor(self, offset=0):
        # Rebuild full text
        full_text = self.get_full_text().upper()
        # advance or retreat cursor if needed
        cursor_location = (len(full_text) - self.universal_pos - offset)
        new_index = cursor_location // 4
        new_position = cursor_location % 4
        if 0 <= new_index < self.words:
            next_box = self.entry_boxes[new_index]
            next_box.grab_focus()
            next_box.set_position(new_position)
        self.set_full_text(full_text)
        return

    def on_entry_changed(self, entry):
        self.set_cursor()
        s = difflib.SequenceMatcher(None, self.get_full_text(), self.correct_string)
        self.bad_boxes = []
        for tag, i1, i2, _, j2 in s.get_opcodes():
            if tag == 'equal':
                continue
            if tag == 'insert' and i1 == i2 and j2 == len(self.correct_string):
                continue # This just means Entry is incomplete
            self.bad_boxes.append(i1 // 4)
            
        # add error location detection from difflib for highlighting.
        correct_are_sensitive = False
        for i in range(self.words):
            if self.entry_boxes[i].get_text_length() == 4:
                if i in self.bad_boxes:
                    # Set text color to red
                    self.entry_boxes[i].override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(.80, 0.2, 0.2, 1))
                    correct_are_sensitive = True
                else:
                    # Reset color
                    self.entry_boxes[i].override_color(Gtk.StateFlags.NORMAL, None)
                    if not correct_are_sensitive: # Lock good boxes from editing
                        self.entry_boxes[i].set_sensitive(correct_are_sensitive)
                        self.entry_boxes[i].override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.8, 1.0, 0.8, 1.0))
        if self.get_full_text() == self.correct_string:
            self.show_success_dialog()
            Gtk.main_quit()
            sys.exit(0)
    
    def show_success_dialog(self):
        dialog = Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.MODAL,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            f"You or a trustworthy heir will store this codex32 {self.string_type} in a secure place; either under lock and key or hidden where only you or they will find."
        )
        dialog.set_title(f"{self.string_type.title()} {self.progress} successfully confirmed")
        dialog.run()
        dialog.destroy()

    def on_key_release(self, entry, event):
        index = self.entry_boxes.index(entry)
        pos = entry.get_position()
        if index > 0:
            prev_box = self.entry_boxes[index - 1]
        if index < self.words - 1:
            next_box = self.entry_boxes[index + 1]
        if event.keyval == Gdk.KEY_BackSpace:
            if pos % 5 == 0 and index > 0:
                prev_box.grab_focus()
                prev_box.set_position(5)
        if event.keyval == Gdk.KEY_Delete and index < self.words - 1:
            if pos % 5 == 4:
                next_box.grab_focus()
                next_box.set_position(0)
            elif next_box.get_text_length() > 0:
                entry.set_position(pos % 5)
            self.set_cursor(-1)

        return False

    def on_key_press(self, entry, event):
        index = self.entry_boxes.index(entry)
        entry_pos = entry.get_position()
        full_text = self.get_full_text()
        self.universal_pos = len(full_text) - (4 * index + entry_pos)

        if index > 0:
            prev_box = self.entry_boxes[index - 1]
        if index < self.words - 1:
            next_box = self.entry_boxes[index + 1]
        if event.keyval == Gdk.KEY_Left:
            if index > 0 and entry_pos % 5 == 0:
                prev_box.grab_focus()
                prev_box.set_position(prev_box.get_text_length())
        if event.keyval == Gdk.KEY_Right:
            if entry_pos % 5 == 4 and index < self.words - 1:
                next_box.grab_focus()
                next_box.set_position(0)
        if len(self.bad_boxes):
            if event.keyval == Gdk.KEY_Return: # Pop the last bad box
                self.entry_boxes[max(self.bad_boxes)].grab_focus()
            if event.keyval == Gdk.KEY_Down: # Grab the next bad box
                self.bad_boxes.reverse()
                self.bad_boxes = [self.bad_boxes.pop()] + self.bad_boxes
                self.entry_boxes[self.bad_boxes[0]].grab_focus()
                self.bad_boxes.reverse()
            if event.keyval == Gdk.KEY_Up: # Grab the previous bad box
                self.bad_boxes = [self.bad_boxes.pop()] + self.bad_boxes
                self.entry_boxes[self.bad_boxes[0]].grab_focus()

        return False
    
    def on_delete_event(self, widget, event):
        # Exit with code 1 if the dialog is closed before completing the entry
        Gtk.main_quit()
        sys.exit(1)

progress = sys.argv[2] if len(sys.argv) > 2 else ''
dialog = EntryWindow(sys.argv[1], progress)
dialog.connect("destroy", Gtk.main_quit)
dialog.show_all()
Gtk.main()
