import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import string_entry
import codex32
from electrum.bip32 import BIP32Node


class WalletCreationDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Create Wallet", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(400, 350)
        ## add a new image
        image = Gtk.Image()
        image.set_from_file('./thin_banner_no_subtitle2.png')
        image_area = Gtk.Box()
        image_area.add(image)
        image_area.show_all()
        self.get_content_area().add(image_area)  # Add the image area to the content area of the dialog


        box = self.get_content_area()

        label = Gtk.Label()
        label.set_text("\nDo you want to make a new seed, or use an existing seed?\n\nIf this is your first use select 'Create a new seed'.\n")
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

def recover():
    dialog = string_entry.Codex32EntryDialog(title="Enter a codex32 secret or share", prefill='MS1',
                                text='Type your codex32 string:', used_indexes=[])
    codex32_string_set = set()
    used_indexes = set()
    k = 1

    while k > len(codex32_string_set):
        result = dialog.create_dialog()
        if result:
            print(result)
            pos = result[0].rfind("1")
            hrp = result[0][:pos]
            k = int(result[0][pos+1])
            if len(result[0]) > 47:
                codex32_string_set.add(result[0])
                if 'S' == result[0][8]:
                    print("Done! " + result[0] + " is the secret!")
                    print(BIP32Node.from_rootseed(codex32.decode(hrp, result[0])[3],xtype='standard').to_xprv())
                    break
            if len(codex32_string_set) == k:
                print(BIP32Node.from_rootseed(codex32.recover_master_seed(list(codex32_string_set)),xtype='standard').to_xprv())
                break
            for share in codex32_string_set:
                print(share)
                used_indexes.add(share[8])
            print("User entered:", result)
            print(used_indexes)
            dialog = string_entry.Codex32EntryDialog(title="Enter codex32 share " + str(len(codex32_string_set) + 1) + " of " + str(k), prefill=result[1], text='Type your codex32 share:', used_indexes=used_indexes)
        else:
            break
def main():
    dialog = WalletCreationDialog(None)
    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        selected_item = dialog.selected_item  # Get the selected item
        print(f"Selected Item: {selected_item}")
        if selected_item == 'Recover with codex32 seed backup':
            dialog.destroy()
            recover()
            main()

    elif response == Gtk.ResponseType.CANCEL:
        print("Cancel clicked")

    dialog.destroy()

if __name__ == "__main__":
    main()
