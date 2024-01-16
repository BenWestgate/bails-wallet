#######
# Scratch file not used.
#######
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

# Create a flag to prevent recursive calls to add_spacing_to_text
handling_change_event = False

def add_spacing_to_text(entry):
    global handling_change_event
    if handling_change_event:
        # Prevent recursive calls
        return

    text = entry.get_text()
    cursor_position = entry.get_position()  # Get the current cursor position
    spaced_text = ''
    cursor_offset = 0  # Offset to keep track of cursor's new position
    space_count = 0  # Count of added spaces
    existing_space_count = 0  # Count of existing 3 per em spaces

    for i, char in enumerate(text):
        if char == " ":
            existing_space_count += 1
            continue  # Skip existing spaces

        if (i - existing_space_count - space_count) > 0 and (i - existing_space_count - space_count) % 4 == 0:
            spaced_text += " "  # Add a 3-per-em space (U+2004) every 4 characters
            cursor_offset += 1  # Increment offset when adding a space
            space_count += 1  # Increment space count
        spaced_text += char

    # Set the flag to prevent recursion and update the text
    handling_change_event = True
    entry.set_text(spaced_text)
    # Set the new cursor position
    entry.set_position(cursor_position + cursor_offset)
    handling_change_event = False

def get_and_validate_string(string_type='string', progress='', string='', share_list=[]):
    if string_type == 'string':
        secret_or = ' secret or'
    else:
        secret_or = ''

    title = "Enter a codex32{} share {}".format(secret_or, progress)
    corr = ''
    if string:
        title = "Re-enter your codex32 {}".format(string_type)
        corr = " corrected"

    while True:
        dialog = Gtk.Dialog(
            title=title,
            buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        dialog.set_default_size(650, -1)

        label = Gtk.Label()
        label.set_text("Type your{} codex32 {}:".format(corr, string_type))
        entry = Gtk.Entry(text=string)
        entry.set_activates_default(True)

        # Connect the changed signal to add_spacing_to_text function
        entry.connect("changed", add_spacing_to_text)

        box = dialog.get_content_area()
        box.add(label)
        box.add(entry)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_entry = entry.get_text()
            if not new_entry:
                dialog.destroy()
                return 1
            string = new_entry
            # Handle user input and validation
            # ...

        dialog.destroy()

        VALID_IDENTIFIER = string[3:8]
        # TODO add ECC here
        corrected_string = string  # validate_and_correct(share, VALID_IDENTIFIER)
        if corrected_string:
            share_list.append(corrected_string)
            break

    if string.lower() in map(str.lower, share_list):
        # You can display a message here using your GUI framework to inform the user about the duplicate share.
        pass

    return string, share_list

get_and_validate_string()
