import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
import difflib

class EntryWindow(Gtk.Window):
    def __init__(self, correct_string):
        Gtk.Window.__init__(self, title="Multi-Field Entry")
        self.set_border_width(10)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.add(hbox)

        self.entry_boxes = []
        self.correct_string = correct_string

        # Set a monospace font
        font_desc = Pango.FontDescription("Monospace 17")

        for i in range(12):
            entry = Gtk.Entry()
            entry.set_max_length(4)
            if i == 11:
                entry.set_max_length(4)
            entry.set_width_chars(4)  # Set width_chars to 4
            entry.override_font(font_desc)  # Set the font
            entry.connect("changed", self.on_entry_changed)
            entry.connect("key-press-event", self.on_key_press) # Use key-press-event

            if i == 6:
                hbox.pack_start(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
            hbox.pack_start(entry, True, True, 0)

            self.entry_boxes.append(entry)

    def get_full_text(self):
        full_text = ""
        box_text = []
        for entry in self.entry_boxes:
            text = entry.get_text()
            full_text += text
            box_text += [ text ]
        return full_text, box_text

    def set_full_text(self,new_full_text=''):
        for i, entry in enumerate(self.entry_boxes):
            entry.set_text(new_full_text[i*4:i*4+4])

    def on_entry_changed(self, entry):
        print('entry_changed')
        # Rebuild full text
        full_text = self.get_full_text()[0]
        print('length after '+str(entry.get_text_length()))
        cursor_pos = entry.get_position()
        print('cursor after '+str(cursor_pos))
        # advance cursor if full
        index = self.entry_boxes.index(entry)
        if cursor_pos >= 3 and entry.get_text_length() == 4 and index < 11:
            next_box = self.entry_boxes[index + 1]
            print('advance entry changed')
            next_box.grab_focus()
            next_box.set_position(0)
        uppercase_diff = difflib.SequenceMatcher(None, full_text, self.correct_string.upper()).ratio()
        lowercase_diff = difflib.SequenceMatcher(None, full_text, self.correct_string.lower()).ratio()
        if uppercase_diff > lowercase_diff:
            self.correct_string = correct_string.upper()
        else:
            self.correct_string = correct_string.lower()
        diff = difflib.SequenceMatcher(self.correct_string, full_text)
        errors = []
        # add error location detection from difflib for highlighting. for line in diff:
        for i in range(12):
            if self.entry_boxes[i].get_text_length() == 4:
                text = self.entry_boxes[i].get_text()
                if text != self.correct_string[i*4:i*4+4]:
                    # Set text color to red
                    self.entry_boxes[i].override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(.80, 0.2, 0.2, 1))
                else:
                    # Reset color
                    self.entry_boxes[i].override_color(Gtk.StateFlags.NORMAL, None)
        last_pos = entry.get_position()
        self.set_full_text(full_text)
        entry.set_position(last_pos)


    def on_key_press(self, entry, event):
        print(event.string+' key pressed')
        index = self.entry_boxes.index(entry)
        entry_pos = entry.get_position()
        pos = 5 * index + entry_pos
        print('position in string '+str(pos))
        entry_length = entry.get_text_length()
        print(entry_length)
        full_text = self.get_full_text()[0]
        print('length entered '+str(len(full_text)))
        self.set_full_text(full_text)
        entry.set_position(entry_pos)
        if index > 0:
            prev_box = self.entry_boxes[index - 1]
        if index < 11:
            next_box = self.entry_boxes[index + 1]
        if event.keyval == Gdk.KEY_Left:
            if index > 0 and pos % 5 == 0:
                print('retard cursor 0')
                prev_box.grab_focus()
                prev_box.set_position(prev_box.get_text_length())
        if event.keyval == Gdk.KEY_Right:
            if index < 11 and pos % 5 == 4:
                next_box.grab_focus()
                next_box.set_position(0)
        elif event.string and event.keyval != Gdk.KEY_BackSpace and event.keyval != Gdk.KEY_Delete and event.keyval != Gdk.KEY_Tab:
            if entry_length == 4:
                self.set_full_text(full_text[:index*4+entry_pos]+event.string+full_text[index*4+entry_pos:])
                entry.set_position(pos % 5 + 1)
            if index < 11 and pos % 5 == 4:
                print('advance cursor 4')
                next_box.grab_focus()
                next_box.set_position(1)
        elif event.keyval == Gdk.KEY_BackSpace:
            if entry_length == 4:
                entry.set_position((pos) % 5)
            if pos % 5 == 0 and index > 0:
                print('retard cursor 0')
                prev_box.grab_focus()
                prev_box.set_position(prev_box.get_text_length())
        elif event.keyval == Gdk.KEY_Delete:
            if pos % 5 == 4 and index < 11:
                print('advance cursor 4')
                next_box.grab_focus()
                next_box.set_position(0)
            elif next_box.get_text_length() > 0:
                entry.set_position(pos % 5)
        return False

if __name__ == "__main__":
    correct_string = "ms12sq405jt9gxgqsnyg6pv53flaqp3y4n4dg42cwztypfjr"  # Replace this with your correct string

    dialog = EntryWindow(correct_string)
    dialog.connect('destroy', Gtk.main_quit)
    dialog.show_all()

    Gtk.main()



win = EntryWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
