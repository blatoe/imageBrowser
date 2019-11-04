import os

from PySide2 import QtGui, QtCore, QtWidgets

import paths, lists, multiThread



class DockWidget(QtWidgets.QDockWidget):
    def __init__(self, *args, **kwargs):
        """Default DockWidget class to configure widgets to be dockable with
         consistent setup.
        Reimplementation of QtWidgets.QDockWidget.

        :param args: standard inputs for a inherited class
        :param kwargs: standard inputs for a inherited class
        """
        super(DockWidget, self).__init__(*args, **kwargs)
        # assign window title based on class name
        parts = lists.fragment(self.__class__.__name__,
                               camelCase=True, clean=True)
        self.setWindowTitle(' '.join(parts))
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.resize(800, 600)

        # assign stylesheet
        #theme = styleSheets.Themes.load(styleSheets.Themes.Dark)
        #self.setStyleSheet(theme)

        # assign default widget
        widget = QtWidgets.QWidget()
        self.setWidget(widget)
        self.show()


class ImageIcon(QtGui.QIcon):
    MOVIE_TYPES = '.gif'.split()

    def __init__(self, path):
        """Widget used to load supported image types as a picture image or an
         animated movie in a view that support icons.
        Reimplementation of QtGui.QIcon.


        :param path: 'str' File path that will attempt to be loaded onto
            QIcon as image or movie.
        """
        super(ImageIcon, self).__init__(str(path))

        self.var_path = path
        self.var_item = None
        self.var_column = None
        self.var_pixmap = None
        self.var_movie = None
        # setup pixmap for icon
        if path.suffix.lower() not in self.MOVIE_TYPES:
            pixmap = QtGui.QPixmap(str(path))
            self.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        else:
            # need to hook into to a movie 'frameChanged' signal to animate
            self.var_movie = QtGui.QMovie(str(path))
            pixmap = self.var_movie.currentPixmap()
            self.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.var_movie.frameChanged.connect(self.on_image_update)
        self.var_pixmap = pixmap

    def on_image_update(self, frame):
        """Updates the render image of the icon to the give frame number.

        :param frame: 'int' Movie frame number to render onto the icon.
        """
        if not self.var_movie:
            return
        self.var_item.setIcon(self.var_column, self.var_movie.currentPixmap())


class ImageView(QtWidgets.QTreeWidget):
    signal_file_selected = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        """A view that displays supported image types in a panel. Icons can be
         scaled up by holding 'Ctrl and scrolling', and rearrange to fill in a
         resized panel.
        Reimplementation of QtWidgets.QTreeWidget

        :param args: standard inputs for a inherited class
        :param kwargs: standard inputs for a inherited class
        """
        super(ImageView, self).__init__(*args, **kwargs)
        self.var_files = []
        self.var_icons = {}
        self.var_icon_maximum = 0

        self.on_ui_create()

    def wheelEvent(self, event):
        """Holding 'Ctrl and scrolling' allows for icons to be scaled up in
         size, only if image was originally scaled down. The layout will be
          reorganize to fit the resized content.
        Reimplementation of inherited function.
        """
        ctrlMod = event.modifiers() == QtCore.Qt.ControlModifier
        if ctrlMod:
            oldSize = self.iconSize().width()
            # check the absolute value of the delta to determine if we need to
            # scale the icons up or down
            delta = event.delta()
            if delta == abs(delta):
                # clamp the new size to prevent some troublesome scaling
                newSize = min(self.var_icon_maximum, oldSize * 1.4)
            else:
                newSize = max(100, oldSize / 1.4)
            self.setIconSize(QtCore.QSize(newSize, newSize))
            # reorganize the scaled images
            self.on_ui_reorganize()
        # maintain the original functionality of this event
        return super(ImageView, self).wheelEvent(event)

    def resizeEvent(self, event):
        """Toggle the playback state of movies that are active as we resize
         the window, in order to prevent some issues in pixmap updates as the
         contents get reorganized.
        Reimplementation of inherited function.
        """
        # check if the current selected item has a movie
        movie = False
        indices = self.selectedIndexes()
        if indices:
            index = indices[0]
            path = self.itemFromIndex(index).toolTip(index.column())
            if path and self.var_icons[path].var_movie:
                icon = self.var_icons[path]
                movie = True
        # TODO: There are some limitations to using a tree view for this type
        #  of scheme. Will need to look into a tableView and see if a different
        #  model may help with the hacked together functionality we're roping in.
        # disable the movie
        if movie:
            icon.var_movie.stop()
        self.on_ui_reorganize()
        # re-enable the movie
        if movie:
            icon.var_movie.start()
        # maintain the original functionality of this event
        return super(ImageView, self).resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Find the selected path from the item's columns and pass it into the
         file selection signal.
        Reimplementation of inherited function.
        """
        position = event.pos()
        index = self.indexAt(position)
        item = self.itemFromIndex(index)
        if item:
            path = item.toolTip(index.column())
            if path:
                self.signal_file_selected.emit(path)
        # maintain the original functionality of this event
        return super(ImageView, self).mouseDoubleClickEvent(event)

    def on_ui_create(self):
        """Setups up view settings to a consistent configuration and standard
        signal connections."""
        self.setSelectionMode(self.NoSelection)
        self.setIconSize(QtCore.QSize(150, 150))
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        # signal connections
        self.currentItemChanged.connect(self.on_movie_toggle)

    def on_movie_toggle(self, currentItem, previousItem):
        """Enable movie playback on selected item index and disable playback on
        previously selected item.
        Called by 'currentItemChanged' signal.
        """
        if previousItem:
            # since we don't know the column of the previous select index,
            # disable all movies in the given previous item
            for i in range(self.columnCount()):
                path = previousItem.toolTip(i)
                if not path:
                    continue
                icon = self.var_icons[path]
                if icon.var_movie:
                    icon.var_movie.stop()
                    icon.var_movie.jumpToFrame(0)
        if currentItem:
            # enable the movie of the current item index
            position = self.mapFromGlobal(QtGui.QCursor().pos())
            index = self.indexAt(position)
            path = currentItem.toolTip(index.column())
            if path and self.var_icons[path].var_movie:
                self.var_icons[path].var_movie.start()

    def on_ui_reorganize(self):
        """Reconfigure the Layout of all the icons to move off screen images or
        fill in empty space, after the icon or view size updates.
        """
        # determine how many images in a row by dividing the view size
        # by icon size, minimum of one.
        columnCount = self.size().width() // self.iconSize().width()
        if columnCount < 1:
            columnCount = 1
        self.setColumnCount(columnCount)
        # reset all the icons with the new column count
        self.on_file_set()
        # update the column size and headers
        headers = []
        for i in range(self.columnCount()):
            headers.append('')
            self.resizeColumnToContents(i)
        self.setHeaderLabels(headers)

    def on_icon_create(self, path):
        """Creation function that generates a new icon and caches it into
         memory, as well as tracking a maximum icon size.
        A scalable function for multiThreading.

        :param path: 'str' file path for image to be displayed
        """
        # if str(path) in self.var_icons:
        #    return
        icon = ImageIcon(path)
        self.var_icons[str(path)] = icon
        # determine a maximum icon size
        self.var_icon_maximum = max([self.var_icon_maximum,
                                     icon.var_pixmap.width(),
                                     icon.var_pixmap.height()])

    def on_file_process(self, files=None):
        """Files will be processed to generate icons to update the display of
         the view, based on the given or cached input.

        :param files: 'list' File paths to create icons and update display
        """
        if files is None:
            files = self.var_files
        else:
            self.var_files = files
        # create icons for images
        # This process seemed to length the ui load times for large numbers of
        # images. MultiThreading this operation appears to cut the time by half.
        threadPool = multiThread.ThreadPool(name='generateIcons',
                                            functionArgs=[[f] for f in files],
                                            function=self.on_icon_create,
                                            pause=True, mainThread=True)
        threadPool.run()
        self.on_ui_reorganize()

    def on_file_set(self, files=None):
        """Given or cached images will be displayed in the view, using the
         current row column configuration.

        :param files: 'list' files to be displayed
        """
        if files is None:
            files = self.var_files
        else:
            self.var_files = files
        # add icons to display
        self.clear()
        rowItems = []
        for i, path in enumerate(files):
            # determine the row and column for this icon entry
            columnCount = self.columnCount()
            row = i // columnCount
            column = i - (row * columnCount)
            if len(rowItems) != row + 1:
                # use existing items if they're will be on the same row
                item = QtWidgets.QTreeWidgetItem(self)
                rowItems.append(item)
            else:
                item = rowItems[row]
            # reuse and update the cached icon
            icon = self.var_icons[str(path)]
            icon.var_item = item
            icon.var_column = column
            if not icon.var_pixmap and not icon.var_movie:
                relativePath = path.name
                item.setText(column, relativePath)
            item.setIcon(column, icon)
            item.setToolTip(column, str(path))
            item.setTextAlignment(column, QtCore.Qt.AlignCenter)


class ImageBrowser(DockWidget):
    signal_path_process = QtCore.Signal(str)
    signal_filter_process = QtCore.Signal(str)

    def __init__(self, path='', *args, **kwargs):
        """Widget to search given or set folder path and find all files in
         subfolders to display images in view. Widget includes string field for
         manual folder path entry/editing, brower button to explore to
         directory, and a filter line to refine displayed items.

        :param path: 'str' Folder path to recursively search for files
        :param args: standard inputs for a inherited class
        :param kwargs: standard inputs for a inherited class
        """
        super(ImageBrowser, self).__init__(*args, **kwargs)
        self.ui_pathLine = None
        self.ui_fileView = None
        self.ui_filterLine = None

        self.var_files = []
        self.var_files_filtered = []
        self.on_ui_create()
        if path:
            self.ui_pathLine.setText(path)

    def on_ui_create(self):
        """Setups up widget settings to a consistent configuration and standard
         signal connections."""

        # mainLayout
        mainLayout = QtWidgets.QVBoxLayout()
        self.widget().setLayout(mainLayout)

        # searchLayout
        searchLayout = QtWidgets.QHBoxLayout()
        mainLayout.addLayout(searchLayout)
        # pathLine
        pathLine = QtWidgets.QLineEdit()
        pathLine.setPlaceholderText('Enter search path...')
        pathLine.setMaximumHeight(30)
        pathLine.setToolTip('Enter in directory path to search for files.')
        pathLine.textChanged.connect(self.signal_path_process)
        self.ui_pathLine = pathLine
        searchLayout.addWidget(pathLine)
        # browseButton
        browseButton = QtWidgets.QPushButton('Browse')
        browseButton.setToolTip('Browse to directory to search for files')
        browseButton.pressed.connect(self.on_directory_browse)
        searchLayout.addWidget(browseButton)

        # file view
        self.ui_fileView = ImageView()
        self.ui_fileView.setToolTip('''Hold "Ctrl" and scroll to de/increase image size
Double click on icon to open file''')
        self.ui_fileView.signal_file_selected.connect(self.on_file_open)
        mainLayout.addWidget(self.ui_fileView)

        # filter
        filterLine = QtWidgets.QLineEdit()
        filterLine.setPlaceholderText('Enter in filter terms...')
        filterLine.setMaximumHeight(30)
        filterLine.setToolTip('''Enter certain characters to expand search
, : separates terms and finds any matching entries
- : matching entry will be excluded
! : term will be required for matches
+ : display entries matching any of these terms
< : term should include any prefix
> : any suffix should be a term''')
        filterLine.textChanged.connect(self.signal_filter_process)
        self.ui_filterLine = filterLine
        mainLayout.addWidget(filterLine)

        # signal connections
        self.signal_path_process.connect(self.on_file_process)
        self.signal_filter_process.connect(self.on_filter_process)

    def on_filter_process(self, filter_terms=None):
        """Filter terms will be processed to filter file paths displayed in
         view, by fragmenting text input into groups and using regExpressions
         include valid matches.

        :param filter_terms: 'str' Formatted terms to filter terms based on
         inclusion, exclusion, required, starting and ending patterns.
        """
        if not filter_terms:
            filter_terms = self.ui_filterLine.text()
        # break up the string term based common separator characters
        terms = lists.fragment(terms=filter_terms, splits=list(' ,'),
                               clean=True)
        # group up common terms based on their starting character. We should
        # get 5 groups: includes, excludes, required, starts, ends
        groupings = lists.grouping(items=terms,
                                   searchTerms=[[t] for t in '+-!<>'])
        files = self.var_files
        if groupings:
            # if we have an extra group, it means there was no matching
            # character and we can assume those to include terms
            if len(groupings) == 6:
                groupings[0].extend(groupings.pop())
            includes, excludes, required, starts, ends = groupings
            # filter the list of files
            files = lists.filter(self.var_files, includes=includes,
                                 excludes=excludes, required=required,
                                 starts=starts, ends=ends)
        self.var_files_filtered = files
        self.ui_fileView.on_file_process(files)

    def on_file_process(self, path=None):
        """The folder path will be processed to find the full list of files
         located under that directory path. This list will be filtered to
         display the matching items

        :param path: 'str' Directory path to locate all files underneath
        """
        if not path:
            path = self.ui_pathLine.text()
        if not os.path.exists(path):
            return
        # find all the files in the directory and subdirectories
        self.var_files = paths.getPaths(paths=path, find_dirs=False)
        self.on_filter_process()

    def on_file_open(self, path):
        """Open a file in the default application.

        :param path: 'str' file path to be open in default application
        """
        os.popen(path)

    def on_directory_browse(self):
        """Bring up an explorer dialog to specify a directory to search
         for files"""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            caption="Browse for search directory")
        if path:
            self.ui_pathLine.setText(os.path.normpath(path))