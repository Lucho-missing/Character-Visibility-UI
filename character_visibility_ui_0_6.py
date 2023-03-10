                        
                        #|--------------------------|#
                        #|GNU GENERAL PUBLIC LICENSE|#
                        #|--------------------------|#

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty

bl_info = {
    'name': 'Character Visibility UI',
    'description': 'Create Visibility UI for your Character',
    'author': 'Lucho',
    'version': (0, 6, 0),
    'blender': (3, 3, 0),
    'warning': '',
    'tracker_url': '',
    'category': 'Rigging'
}

#------------ SIMPLE FUNCTIONS ----------------------------------------

def mod_icon(modifier):
    if modifier.type == 'PARTICLE_SYSTEM':
        return 'MOD_PARTICLES'
    if modifier.type == 'NODES':
        return 'GEOMETRY_NODES'
    
    return 'MOD_'+ modifier.type

#----------------LIST UI-----------------------------------------------

class CHVI_UL_group_items(bpy.types.UIList):
    bl_options = {"COMPACT"}

    active_index : IntProperty()
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
   
       
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            grid = layout.column()
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            grid = layout.column()

        row= grid.row()
                
        if item.show_props == False: tria_ic = "DISCLOSURE_TRI_RIGHT"
        else: tria_ic = "DISCLOSURE_TRI_DOWN"
        if index == context.active_object.data.chvi_list_index: tria_em = True
        else: tria_em = False

        row.prop(item, "show_props", text = "", icon = tria_ic, emboss = tria_em)   

        row.prop(item, "name", text = "", icon = 'FILE_FOLDER', emboss = False)   

        col = row.column()
        col.scale_x = 0.5
        col.prop(item, "super_group", text = "")            

        if item.show_props == True:
            for ite in item.items:
                row = grid.row()
                row.scale_y = 0.8
                row.separator(factor = 2)
                row.separator(factor = 2)
                if ite.is_mod == False:                
                    row.label(text = ite.mesh_p.name, icon = 'OBJECT_DATA')
                else:
                    row.label(text = ite.mod_p + ' (' + ite.mesh_p.name + ')', icon = mod_icon(ite.mesh_p.modifiers[ite.mod_p]))
                if index == context.active_object.data.chvi_list_index:
                    op = row.operator("chvi_remove.vis_item", text="", icon="PANEL_CLOSE")
                    op.index = ite.index
                    row.separator(factor = 2)
                    row.separator(factor = 2)
                    
            
        grid.separator()


#------------------- PROPERTY GROUP ----------------------------------------

class CHVI_visibility_item(bpy.types.PropertyGroup):

    mesh_p : bpy.props.PointerProperty(type = bpy.types.Object, override = {'LIBRARY_OVERRIDABLE'})

    mod_p : bpy.props.StringProperty(default = "", override = {'LIBRARY_OVERRIDABLE'})

    is_mod : BoolProperty(name = "is modifier", default= False, override = {'LIBRARY_OVERRIDABLE'})

    index : IntProperty(name = "index", default = -1, override = {'LIBRARY_OVERRIDABLE'})

#------------------------------------------------------------------------------

class CHVI_visibility_group(bpy.types.PropertyGroup):

    def has_keyframe(self,context):
        anim = context.active_object.data.animation_data
        if anim is not None and anim.action is not None:
            for fcu in anim.action.fcurves:
                print (fcu.data_path)
                print (f'{self}.rendering')
                if fcu.data_path == f'{self}.rendering':
                    return True
                    #return len(fcu.keyframe_points) > 0
        return False

    
    def viewport_toggle(self, context):  
        for item in self.items:
            if item.is_mod:
                item.mesh_p.modifiers[item.mod_p].show_viewport = not self.visibility
            else:
                item.mesh_p.hide_viewport = not self.visibility
                

    def render_toggle(self, context):  
        for item in self.items:
            if item.is_mod:
                item.mesh_p.modifiers[item.mod_p].show_render = not self.rendering
            else:
                item.mesh_p.hide_render = not self.rendering
                

    name : StringProperty(name="Group",
              description="Choose a Name for this Property Gruop",
              default="Untitled", override = {'LIBRARY_OVERRIDABLE'})

    index : IntProperty (name = "index", default = -1, override = {'LIBRARY_OVERRIDABLE'})

    show_props : BoolProperty(name="Show/Hide Properties",
              description="",
              default=True, override = {'LIBRARY_OVERRIDABLE'})

    super_group : IntProperty (name = "UI-SuperGroup", default = 0, min = 0, max = 9, override = {'LIBRARY_OVERRIDABLE'})

    # options ={"LIBRARY_EDITABLE"}, override = {'LIBRARY_OVERRIDABLE'}

    visibility : BoolProperty ( default=True, update = viewport_toggle,  override = {'LIBRARY_OVERRIDABLE'})

    rendering : BoolProperty ( default=True, update = render_toggle,  override = {'LIBRARY_OVERRIDABLE'})

    items : bpy.props.CollectionProperty(type = CHVI_visibility_item, override = {'LIBRARY_OVERRIDABLE'})

    super_groups = (0,1,2,3,4,5,6,7,8,9)

    


#-----------------------------------------------------------------------
#------------------- PREVIEW PANEL -------------------------------------
#-----------------------------------------------------------------------

class CHVI_PT_preview_panel(bpy.types.Panel):
    bl_category = "Item"
    bl_label = "Visibility UI"
    bl_idname = "CHVI_PT_preview_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(self, context):
        if context.active_object == None:
            return False
        if context.active_object.type == 'ARMATURE' and len(context.active_object.data.chvi_vis_groups) > 0 :
            return True
        else:
            return False

    def draw(self, context):
        lay = self.layout
        lay.scale_y = 0.8
        layout = lay.column()
        raw = layout.row()
        raw.operator('chvi_copy.rendering', icon ='COPYDOWN')
        raw.scale_x = 0.7
        raw.scale_y = 1.3
        raw.alignment = 'CENTER'

        for s_group in CHVI_visibility_group.super_groups:
            lay_solved = False 
            row_ahead = 0
            for group in context.active_object.data.chvi_vis_groups:
                if group.super_group == s_group:
                    if lay_solved == False:
                        tab = layout.row(align=True)
                        grid = tab.column(align=True)
                        if CHVI_OT_viewport_super_group.visibility[s_group] == True: gr_icon = 'RESTRICT_VIEW_OFF'
                        else: gr_icon = 'RESTRICT_VIEW_ON'
                        tg=grid.operator('chvi_toggle.viewport', text = "", icon = gr_icon)
                        tg.index = s_group                   
                        grid = tab.row(align=True)
                        box = grid.box()
                        col = box.column(align = True)
                        row = col.row(align = True)
                        lay_solved = True
                    if row_ahead == 3:   #ahead here
                        row = col.row(align = True)
                        row_ahead = 0
                    if group.visibility == True: vp_icon = 'RESTRICT_VIEW_OFF'
                    else: vp_icon = 'RESTRICT_VIEW_ON'
                    row.prop(group, "visibility", text = group.name, icon = vp_icon)
                    row_ahead += 1



        layout = lay.column()
        layout.separator(factor = 2)
        raw = layout.row()
        raw.operator('chvi_copy.viewport', icon = 'COPYDOWN')
        raw.scale_x = 0.7
        raw.scale_y = 1.3
        raw.alignment = 'CENTER'

        for s_group in CHVI_visibility_group.super_groups:
            lay_solved = False 
            row_ahead = 0
            for group in context.active_object.data.chvi_vis_groups:
                if group.super_group == s_group:
                    if lay_solved == False:
                        tab = layout.row(align=True)
                        grid = tab.column(align=True)
                        if CHVI_OT_render_super_group.visibility[s_group] == True: gr_icon = 'RESTRICT_RENDER_OFF'
                        else: gr_icon = 'RESTRICT_RENDER_ON'
                        tg=grid.operator('chvi_toggle.render', text = "", icon = gr_icon)
                        tg.index = s_group                        
                        grid = tab.row(align=True)
                        box = grid.box()
                        col = box.column(align = True)
                        row = col.row(align = True)
                        lay_solved = True
                    if row_ahead == 3:   #ahead here
                        row = col.row(align = True)
                        row_ahead = 0
                    if group.rendering == True: vp_icon = 'RESTRICT_RENDER_OFF'
                    else: vp_icon = 'RESTRICT_RENDER_ON'
                    row.prop(group, "rendering", text = group.name, icon = vp_icon)
                    row_ahead += 1


#----------------------------------------------------------------------
#------------------- SETUP PANEL --------------------------------------
#----------------------------------------------------------------------

class CHVI_PT_setup_panel(bpy.types.Panel):
    bl_category = "Character Visibility UI"
    bl_label = "Visibility Groups Setup"
    bl_idname = "CHVI_PT_setup_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(self, context):
        if context.active_object == None:
            return False
        if context.active_object.type == 'ARMATURE' and not context.active_object.override_library:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout

        row=layout.row()
        
        if context.scene.chvi_recursive == False:
            row.label(text="Add Single Collection:")
        else:
            row.label(text="Add Recursive Collection:")
        row.prop(context.scene, 'chvi_recursive', text ='', toggle = True)
        row.prop(context.scene, 'chvi_dummy_coll', text ="")

        col = row.column()
        op0=col.operator('chvi_add.vis_item', text = "", icon = 'ADD')
        op0.kind = 0
        try:
            op0.coll_p = context.scene.chvi_dummy_coll.name
        except AttributeError:
            col.enabled = False

        row=layout.row()
        row.label(text="Add Object:")
        row.prop(context.scene, 'chvi_dummy_obj', text ="")
        
        col = row.column()
        op2=col.operator('chvi_add.vis_item', text = "", icon = 'ADD')
        op2.kind = 2
        try:
            op2.mesh_p = context.scene.chvi_dummy_obj.name
        except AttributeError:
            col.enabled = False

        row = layout.row()
        row.label(text='Add Modifier:')
        if context.scene.chvi_dummy_obj != None:
            if len(context.scene.chvi_dummy_obj.modifiers) >0:
                box = row.box()
                for mod in context.scene.chvi_dummy_obj.modifiers:
                    roz = box.row()
                    try:
                        roz.label(text = mod.name, icon = mod_icon(mod))
                    except TypeError:
                        roz.label(text = mod.name, icon = 'QUESTION')
                    op3=roz.operator('chvi_add.vis_item', text = "", icon = 'ADD')
                    op3.kind = 3
                    op3.mesh_p = context.scene.chvi_dummy_obj.name
                    op3.mod_p = mod.name
        else:
            
            row.label(text='Select an Object')
            row.enabled = False
            
        
        layout.separator()

        row= layout.row()
        fin = row.row()
        fin.template_list("CHVI_UL_group_items", 
                        "The_List", 
                        context.active_object.data,
                        "chvi_vis_groups", 
                        context.active_object.data, 
                        "chvi_list_index")

        col = fin.column()
        col.separator(factor = 2)
        col.operator('chvi_add.vis_group', text = "", icon = 'NEWFOLDER')
        col.operator('chvi_remove.vis_group', text = "", icon = 'TRASH')

        col.separator(factor = 2)
        mov = col.operator('chvi.move_group', text = "", icon = 'TRIA_UP')
        mov.direction = 'UP'
        mov = col.operator('chvi.move_group', text = "", icon = 'TRIA_DOWN')
        mov.direction = 'DOWN'


#--------------------- ADD ITEM ----------------------------------------

class CHVI_OT_add_vis_item(bpy.types.Operator):
    bl_idname = "chvi_add.vis_item"
    bl_label = "Add Visibility Item"
    bl_description = "Create Visibility Item"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        if context.active_object.data.chvi_list_index == -1:
            return False
        return getattr(context.active_object, 'pose', None)

    mesh_p : bpy.props.StringProperty()
    coll_p : bpy.props.StringProperty()
    mod_p : bpy.props.StringProperty()

    kind : bpy.props.IntProperty(name='kind', default= -1)
#     0 : collection  | 2 : object | 3 : modifier

    def add_driver(self, context, target, prop, dataPath, is_mod = False):

        n_drive = target.driver_add(prop)
        n_var = n_drive.driver.variables.new()
        n_var.name                 = prop
        n_var.targets[0].id_type = 'ARMATURE'
        n_var.targets[0].id        = context.active_object.data
        n_var.targets[0].data_path = dataPath
        if is_mod == False:
            n_drive.driver.expression = f'1 - {n_var.name}'
        else:
            n_drive.driver.expression = n_var.name



    def execute(self, context):
        list_ =context.active_object.data.chvi_vis_groups
        ac_index = context.active_object.data.chvi_list_index       

        if self.kind == 0:
            for obj in bpy.data.collections[self.coll_p].objects:
                pr = list_[ac_index].items.add()
                pr.index = (len(list_[ac_index].items))-1
                pr.mesh_p = obj
                self.add_driver(context, obj, 'hide_viewport', list_[ac_index].path_from_id('visibility'))
                self.add_driver(context, obj, 'hide_render', list_[ac_index].path_from_id('rendering'))

            if context.scene.chvi_recursive:
                for coll in bpy.data.collections[self.coll_p].children_recursive:
                    for obj in coll.objects:
                        pr = list_[ac_index].items.add()
                        pr.index = (len(list_[ac_index].items))-1
                        pr.mesh_p = obj
                        self.add_driver(context, obj, 'hide_viewport', list_[ac_index].path_from_id('visibility'))
                        self.add_driver(context, obj, 'hide_render', list_[ac_index].path_from_id('rendering'))

        if self.kind == 2:
            pr = list_[ac_index].items.add()
            pr.index = (len(list_[ac_index].items))-1
            pr.mesh_p = bpy.data.objects[self.mesh_p]
            self.add_driver(context, bpy.data.objects[self.mesh_p], 'hide_viewport', list_[ac_index].path_from_id('visibility'))
            self.add_driver(context, bpy.data.objects[self.mesh_p], 'hide_render', list_[ac_index].path_from_id('rendering'))

        
        if self.kind == 3:
            pr = list_[ac_index].items.add()
            pr.index = (len(list_[ac_index].items))-1
            pr.mesh_p = bpy.data.objects[self.mesh_p]
            pr.is_mod = True
            pr.mod_p = self.mod_p
            self.add_driver(context, bpy.data.objects[self.mesh_p].modifiers[self.mod_p], 'show_viewport', list_[ac_index].path_from_id('visibility'), is_mod = True)
            self.add_driver(context, bpy.data.objects[self.mesh_p].modifiers[self.mod_p], 'show_render', list_[ac_index].path_from_id('rendering'), is_mod = True)
        
        return{'FINISHED'}

#--------------------- ADD GROUP ----------------------------------------

class CHVI_OT_add_vis_group(bpy.types.Operator):
    bl_idname = "chvi_add.vis_group"
    bl_label = "Add Visibility Group"
    bl_description = "Create Visibility Group"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return getattr(context.active_object, 'pose', None)

    def execute(self, context):
        gr = context.active_object.data.chvi_vis_groups.add()
        gr.index = len(context.active_object.data.chvi_vis_groups) - 1
        gr.name = f"Group #{gr.index}"
        gr.super_group = context.active_object.data.chvi_vis_groups[gr.index-1].super_group
        context.active_object.data.chvi_list_index = gr.index
        return{'FINISHED'}


#----------------- REMOVE GROUP ------------------------------------------

class CHVI_OT_remove_vis_group(bpy.types.Operator):
    bl_idname = "chvi_remove.vis_group"
    bl_label = "Remove Visibility Group"
    bl_description = "Remove Visibility Group"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        if len(context.active_object.data.chvi_vis_groups) < 1:
            return False
        return getattr(context.active_object, 'pose', None)

    def execute(self, context):
        for it in context.active_object.data.chvi_vis_groups[context.active_object.data.chvi_list_index].items:
            if it.is_mod == False:
                it.mesh_p.driver_remove('hide_viewport')
                it.mesh_p.driver_remove('hide_render')
            else:
                it.mesh_p.modifiers[it.mod_p].driver_remove('show_viewport')
                it.mesh_p.modifiers[it.mod_p].driver_remove('show_render')

        context.active_object.data.chvi_vis_groups.remove(context.active_object.data.chvi_list_index)
        context.active_object.data.chvi_list_index = min(max(0, context.active_object.data.chvi_list_index - 1), len(context.active_object.data.chvi_vis_groups) - 1)
        return{'FINISHED'}

#----------------- MOVE GROUP ------------------------------------------

class CHVI_OT_move_group(bpy.types.Operator):
    """Move a Group in the list."""

    bl_idname = "chvi.move_group"
    bl_label = "Move a Group Up/Down"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return len(context.active_object.data.chvi_vis_groups) > 1
    
    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """
        groups = context.active_object.data.chvi_vis_groups
        index = context.active_object.data.chvi_list_index
        list_length = len(groups) - 1  # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)

        context.active_object.data.chvi_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        my_list = context.active_object.data.chvi_vis_groups
        index = context.active_object.data.chvi_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        my_list.move(neighbor, index)
        self.move_index(context)

        return{'FINISHED'}


#----------------- REMOVE ITEM ------------------------------------------

class CHVI_OT_remove_vis_item(bpy.types.Operator):
    bl_idname = "chvi_remove.vis_item"
    bl_label = "Remove Visibility Item"
    bl_description = "Remove Visibility Item"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        if len(context.active_object.data.chvi_vis_groups) < 1:
            return False
        return getattr(context.active_object, 'pose', None)

    index : IntProperty(default = -1)

    def execute(self, context):
        group =  context.active_object.data.chvi_vis_groups[context.active_object.data.chvi_list_index]
        it = group.items[self.index]

        if it.is_mod == False:
            it.mesh_p.driver_remove('hide_viewport')
            it.mesh_p.driver_remove('hide_render')
        else:
            it.mesh_p.modifiers[it.mod_p].driver_remove('show_viewport')
            it.mesh_p.modifiers[it.mod_p].driver_remove('show_render')

        group.items.remove(self.index)
        for it in range(self.index, (len(group.items))):
            group.items[it].index -= 1
        return{'FINISHED'}

#----------------------- HIDE SUPERGROUP VP --------------------------------------

class CHVI_OT_viewport_super_group(bpy.types.Operator):
    bl_idname = "chvi_toggle.viewport"
    bl_label = "Viewport Hide"
    bl_description = "Hide Super Group from Viewport"
    bl_options = {'UNDO'}

    index : IntProperty(min = 0, max = 9)
    # visibility : BoolProperty (default = True)
    visibility = [True, True, True, True, True, True, True, True, True, True]

    def execute(self, context):
        self.visibility[self.index] = not self.visibility[self.index]
        for group in context.active_object.data.chvi_vis_groups:
            if self.index == group.super_group:
                group.visibility = self.visibility[self.index]

        return{'FINISHED'}

#----------------------- HIDE SUPERGROUP RENDERING --------------------------------------

class CHVI_OT_render_super_group(bpy.types.Operator):
    bl_idname = "chvi_toggle.render"
    bl_label = "Render Hide"
    bl_description = "Hide Super Group from Render"
    bl_options = {'UNDO'}

    index : IntProperty( min = 0, max = 9)

    
    visibility = [True, True, True, True, True, True, True, True, True, True]

    def execute(self, context):
        self.visibility[self.index] = not self.visibility[self.index]
        for group in context.active_object.data.chvi_vis_groups:
            if self.index == group.super_group:
                group.rendering = self.visibility[self.index]

        return{'FINISHED'}

#----------------------- COPY FROM RENDERING --------------------------------------

class CHVI_OT_copy_rendering(bpy.types.Operator):
    bl_idname = "chvi_copy.rendering"
    bl_label = "Copy from Rendering"
    bl_description = "Copy Setting Visibility from Rendering to Viewport"
    bl_options = {'UNDO'}

    def execute(self, context):
        for group in context.active_object.data.chvi_vis_groups:
            group.visibility = group.rendering
        return{'FINISHED'}
    
#----------------------- COPY FROM RENDERING --------------------------------------

class CHVI_OT_copy_viewport(bpy.types.Operator):
    bl_idname = "chvi_copy.viewport"
    bl_label = "Copy from Viewport"
    bl_description = "Copy Setting Visibility from Viewport to Rendering"
    bl_options = {'UNDO'}

    def execute(self, context):
        for group in context.active_object.data.chvi_vis_groups:
            group.rendering = group.visibility
        return{'FINISHED'}
#----------------- REGISTER ---------------------------------------------

classes = (
    CHVI_visibility_item,
    CHVI_OT_remove_vis_group,
    CHVI_PT_setup_panel,
    CHVI_visibility_group,
    CHVI_UL_group_items,
    CHVI_OT_add_vis_group,
    CHVI_OT_move_group,
    CHVI_OT_add_vis_item,
    CHVI_OT_remove_vis_item,
    CHVI_PT_preview_panel,
    CHVI_OT_viewport_super_group,
    CHVI_OT_render_super_group,
    CHVI_OT_copy_rendering,
    CHVI_OT_copy_viewport
    
    )



def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.chvi_dummy_obj = bpy.props.PointerProperty(type = bpy.types.Object, override = {'LIBRARY_OVERRIDABLE'})
    
    bpy.types.Scene.chvi_dummy_coll = bpy.props.PointerProperty(type = bpy.types.Collection, override = {'LIBRARY_OVERRIDABLE'})
    
    bpy.types.Scene.chvi_recursive = bpy.props.BoolProperty(name= 'Recursive',default = False, override = {'LIBRARY_OVERRIDABLE'})

    bpy.types.Armature.chvi_list_index = bpy.props.IntProperty(name = "Active Visibility Group", override = {'LIBRARY_OVERRIDABLE'})
    
    bpy.types.Armature.chvi_vis_groups = bpy.props.CollectionProperty(type= CHVI_visibility_group, override = {'LIBRARY_OVERRIDABLE'})

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
        
    del bpy.types.Scene.chvi_dummy_obj   
    del bpy.types.Scene.chvi_dummy_coll
    del bpy.types.Scene.chvi_recursive
    del bpy.types.Armature.chvi_list_index
    del bpy.types.Armature.chvi_vis_groups



if __name__ == "__main__":
    register()