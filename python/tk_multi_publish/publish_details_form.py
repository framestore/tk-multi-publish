"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""

import tank
from tank.platform.qt import QtCore, QtGui

from group_header import GroupHeader
from output_item import OutputItem
from item_list import ItemList
from error_list import ErrorList

thumbnail_widget = tank.platform.import_framework("tk-framework-widget", "thumbnail_widget")
class ThumbnailWidget(thumbnail_widget.ThumbnailWidget):
    pass
        
class PublishDetailsForm(QtGui.QWidget):
    """
    Implementation of the main publish UI
    """

    # signals
    publish = QtCore.Signal()
    cancel = QtCore.Signal()
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._group_widget_info = {}
        self._tasks = []
    
        # set up the UI
        from .ui.publish_details_form import Ui_PublishDetailsForm
        self._ui = Ui_PublishDetailsForm() 
        self._ui.setupUi(self)
        
        # create vbox layout for scroll widget:
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(2,2,2,2)
        self._ui.task_scroll.widget().setLayout(layout)
        
        # hook up buttons
        self._ui.publish_btn.clicked.connect(self._on_publish)
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        
        # TODO: remove browse functionality completely from
        # widget in framework
        self._ui.thumbnail_widget.enable_fs_browse(False)
        
        self.can_change_shotgun_task = True

    @property
    def selected_tasks(self):
        return self._get_selected_tasks()

    @property
    def shotgun_task(self):
        current_index = self._ui.sg_task_combo.currentIndex()
        return self._ui.sg_task_combo.itemData(current_index) if current_index >= 0 else None
    @shotgun_task.setter
    def shotgun_task(self, value):
        self._set_current_shotgun_task(value)
        
    @property
    def comment(self):
        return self._ui.comments_edit.toPlainText().strip()
    @comment.setter
    def comment(self, value):
        self._ui.comments_edit.setPlainText(value)

    @property
    def thumbnail(self):
        return self._ui.thumbnail_widget.thumbnail
    @thumbnail.setter
    def thumbnail(self, value):
        self._ui.thumbnail_widget.thumbnail = value
        
    @property
    def can_change_shotgun_task(self):
        """
        Control if the shotgun task can be changed or not
        """
        return self._ui.sg_task_stacked_widget.currenWidget() == self._ui.sg_task_menu_page
    @can_change_shotgun_task.setter
    def can_change_shotgun_task(self, value):
        page = [self._ui.sg_task_label_page, self._ui.sg_task_menu_page][value]
        self._ui.sg_task_stacked_widget.setCurrentWidget(page)
        
        
    def set_shotgun_task_selection_enabled(self, enabled=True):
        """
        Expose ability to enable/disable the shotgun task selection
        combo box
        """
        self._ui.sg_task_combo.setEnabled(enabled)
        
    def initialize(self, tasks, sg_tasks):
        """
        Initialize UI
        """
        
        # reset UI to default state:
        self._ui.sg_task_combo.setEnabled(True)
        
        # populate shotgun task list:
        self._populate_shotgun_tasks(sg_tasks)
        
        # connect up modified signal on tasks:
        self._tasks = tasks

        # populate outputs list:
        self._populate_task_list()
        
    def _populate_shotgun_tasks(self, sg_tasks, allow_no_task = True):
        """
        Populate the shotgun task combo box with the provided
        list of shotgun tasks
        """
        current_index = self._ui.sg_task_combo.currentIndex()
        current_task = (self._ui.sg_task_combo.itemData(current_index) if current_index >= 0 else None)
        self._ui.sg_task_combo.clear()
        
        # add 'no task' task:
        if allow_no_task:
            self._ui.sg_task_combo.addItem("Do not associate this publish with a task")
            self._ui.sg_task_combo.insertSeparator(self._ui.sg_task_combo.count())
            self._ui.sg_task_combo.insertSeparator(self._ui.sg_task_combo.count())
        
        # add tasks:
        for task in sg_tasks:
            label = "%s | %s" % (task["step"]["name"], task["content"])
            self._ui.sg_task_combo.addItem(label, task)

        # reselect selected task if it is still in list:
        self._set_current_shotgun_task(current_task)
        
    def _set_current_shotgun_task(self, task):
        """
        Select the specified task in the shotgun task
        combo box
        """
        found_index = 0
        for ii in range(0, self._ui.sg_task_combo.count()):
            item_task = self._ui.sg_task_combo.itemData(ii)
            
            found = False
            if not task:
                found = not item_task
            elif item_task:
                found = task["id"] == item_task["id"]
            
            if found:
                found_index = ii
                break
            
        self._ui.sg_task_combo.setCurrentIndex(found_index)
            
    def _populate_task_list(self):
        """
        Build the main task list for selection of outputs, items, etc.
        """
        
        # clear existing widgets:
        task_scroll_widget = self._ui.task_scroll.widget()
        self._group_widget_info = {}
        #TODO
        
        # group tasks by display group:
        group_order = []
        tasks_by_group = {}
        for task in self._tasks:
            group = tasks_by_group.setdefault(task.output.display_group, dict())
            group.setdefault("outputs", set()).add(task.output)
            group.setdefault("items", set()).add(task.item)
            #group.setdefault("errors", list()).extend(task.errors)
            group.setdefault("tasks", list()).append(task)

            if not task.output.display_group in group_order:
                group_order.append(task.output.display_group)            
        
        # add widgets to scroll area:
        layout = task_scroll_widget.layout()
        for group in group_order:
            
            widget_info = {}
            
            # add header:
            header = GroupHeader(group, task_scroll_widget)
            layout.addWidget(header)
            widget_info["header"] = header
        
            # add output items:
            output_widgets = []
            for output in tasks_by_group[group]["outputs"]:
                item = OutputItem(output, task_scroll_widget)
                layout.addWidget(item)
                output_widgets.append(item)
            widget_info["output_widgets"] = output_widgets

            # add item list if more than one item:                
            if len(tasks_by_group[group]["items"]) > 1:
                item_list = ItemList(tasks_by_group[group]["items"], task_scroll_widget)
                layout.addWidget(item_list)
                widget_info["item_list"] = item_list
                
            # always add error list:
            error_list = ErrorList(tasks_by_group[group]["tasks"], task_scroll_widget)
            #error_list.setVisible(False)
            layout.addWidget(error_list)
            widget_info["error_list"] = error_list
            
            self._group_widget_info[group] = widget_info
                
        # add vertical stretch:
        layout.addStretch(1)
        
    def _get_selected_tasks(self):
        """
        Get the selected tasks from the UI
        """
        selected_tasks = []
        
        # build some indexes:
        task_index = {}
        tasks_per_output = {}
        for task in self._tasks:
            key = (task.output, task.item)
            if key in task_index.keys():
                raise "Didn't expect to find the same task in the list twice!"
            task_index[key] = task
            tasks_per_output.setdefault(task.output, list()).append(task)
        
        for info in self._group_widget_info.values():
            
            # go through output widgets
            for output_widget in info["output_widgets"]:
                if not output_widget.selected:
                    continue
                
                output = output_widget.output
                
                # go through item widgets:
                item_list = info.get("item_list")
                if item_list:
                    for item in item_list.selected_items:
                        task = task_index.get((output, item))
                        if task:
                            selected_tasks.append(task)
                else:
                    # assume all items for this output are selected:
                    tasks = tasks_per_output.get(output)
                    if tasks:
                        selected_tasks.extend(tasks)
            
        return selected_tasks
        
        
        
        
            
                    
    def _on_publish(self):
        self.publish.emit()
        
    def _on_cancel(self):
        self.cancel.emit()
        
        
        
        
        
        
        
        
        
        
        
        