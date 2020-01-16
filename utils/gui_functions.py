# see: https://gist.github.com/GriMel/181db149cc150d903f1a
def deleteLayout(cur_lay):
    if cur_lay is not None:
        while cur_lay.count():
            item = cur_lay.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                deleteLayout(item.layout())
