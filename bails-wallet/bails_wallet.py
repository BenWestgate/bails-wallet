import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class WalletCreationDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Create Wallet", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(400, 300)

        box = self.get_content_area()

        label = Gtk.Label()
        label.set_text("Do you want to make a new seed, or use an existing seed?\n\nIf this is your first use select 'Create a new seed'.")
        box.add(label)

        liststore = Gtk.ListStore(bool, str)
        iter_new_seed = liststore.append([True, "Create a new seed"])
        liststore.append([False, "Recover with codex32 seed backup"])
        liststore.append([False, "Import existing wallet descriptors"])

        treeview = Gtk.TreeView(model=liststore)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Select", renderer_text, text=1)
        treeview.append_column(column_text)

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.set_radio(True)
        renderer_toggle.connect("toggled", self.on_toggle, liststore, iter_new_seed)
        column_toggle = Gtk.TreeViewColumn("Menu Item", renderer_toggle, active=0)
        treeview.append_column(column_toggle)

        box.add(treeview)

        self.selected_item = "Create a new seed"  # Set the default selection

        self.show_all()

    def on_toggle(self, renderer, path, liststore, iter_new_seed):
        iter = liststore.get_iter(path)
        if iter:
            liststore.foreach(self.reset_selection, None)
            liststore.set(iter, 0, True)
            self.selected_item = liststore.get_value(iter, 1)

    def reset_selection(self, model, path, iter, data):
        model.set(iter, 0, False)

def main():
    dialog = WalletCreationDialog(None)
    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        selected_item = dialog.selected_item  # Get the selected item
        print(f"Selected Item: {selected_item}")
    elif response == Gtk.ResponseType.CANCEL:
        print("Cancel clicked")

    dialog.destroy()

if __name__ == "__main__":
    main()
