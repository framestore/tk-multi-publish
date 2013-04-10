"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import os

import tank
from tank import Hook
from tank import TankError

class PostPublishHook(Hook):
    """
    Single hook that implements post-publish functionality
    """    
    def execute(self, work_template, progress_cb, **kwargs):
        """
        Main hook entry point
        
        :work_template: template
                        This is the template defined in the config that
                        represents the current work file
                        
        :progress_cb:   Function
                        A progress callback to log progress during pre-publish.  Call:
                        
                            progress_cb(percentage, msg)
                             
                        to report progress to the UI

        :returns:       None - raise a TankError to notify the user of a problem
        """
        # get the engine name from the parent object (app/engine/etc.)
        engine_name = self.parent.engine.name
        
        # depending on engine:
        if engine_name == "tk-maya":
            self._do_maya_post_publish(work_template)
        elif engine_name == "tk-nuke":
            self._do_nuke_post_publish(work_template)
        else:
            raise TankError("Unable to perform post publish for unhandled engine %s" % engine_name)
        
    def _do_maya_post_publish(self, work_template):
        """
        Do any Maya post-publish work
        """        
        import maya.cmds as cmds
        
        # get the current scene path:
        scene_path = os.path.abspath(cmds.file(query=True, sn=True))
        
        # increment version and construct new file name:
        fields = work_template.get_fields(scene_path)
        next_version = self._get_next_work_file_version(work_template, fields)
        fields["version"] = next_version 
        new_scene_path = work_template.apply_fields(fields)
        
        # log info
        self.parent.log_debug("Version up work file %s --> %s..." % (scene_path, new_scene_path))
        
        # rename and save the file
        cmds.file(rename=new_scene_path)
        cmds.file(save=True)

    def _do_nuke_post_publish(self, work_template):
        """
        Do any nuke post-publish work
        """        
        import nuke
        
        # get the current script path:
        original_path = nuke.root().name()
        script_path = os.path.abspath(original_path.replace("/", os.path.sep))
        
        # increment version and construct new name:
        fields = work_template.get_fields(script_path)
        next_version = self._get_next_work_file_version(work_template, fields)
        fields["version"] = next_version 
        new_path = work_template.apply_fields(fields)
        
        # log info
        self.parent.log_debug("Version up work file %s --> %s..." % (script_path, new_path))

        # rename script:
        nuke.root()["name"].setValue(new_path)
    
        # update write nodes:
        write_node_app = tank.platform.current_engine().apps.get("tk-nuke-writenode")
        if write_node_app:
            self.parent.log_debug("Resetting render paths for all write nodes")
            # reset render paths for all write nodes:
            for wn in write_node_app.get_write_nodes():
                 write_node_app.reset_node_render_path(wn)
                        
        # save the script:
        nuke.scriptSaveAs(new_path)

        
    def _get_next_work_file_version(self, work_template, fields):
        """
        Find the next available version for the specified work_file
        """
        existing_versions = self.parent.tank.paths_from_template(work_template, fields, ["version"])
        version_numbers = [work_template.get_fields(v).get("version") for v in existing_versions]
        curr_v_no = fields["version"]
        max_v_no = max(version_numbers)
        return max(curr_v_no, max_v_no) + 1





        
        