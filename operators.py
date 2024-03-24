import bpy
import os,math,webbrowser,json
from . import s1mapp as blenderApp
import numpy as np 
from scipy.spatial import Delaunay


def getImportDataTypes():
    items = [
        ("osm","Server","OpenStreetMap"),
        ("terrain","Terrain","Terrain"),
        ("overlay", "Image Overlay", "Image overlay for the terrain, e.g. satellite imagery or a map"),  # osm mapnik / mapbox streets
        ("file","File","Load an OpenStreetMap File"),
    ]
    return items

def getExportDataTypes():
    items = [
        ("xodr","Open Drive","Open Drive"),
        ("fbx","Autodesk FBX","Autodesk FBX"),
        ("usdz","Pixar USDZ","Universal Scene Description")
    ]
    return items

def del_collection(coll_name):
    if coll_name not in bpy.data.collections:  return
    coll = bpy.data.collections[coll_name]
    if (not coll): return 
    for c in coll.children:
        del_collection(c)
    bpy.data.collections.remove(coll,do_unlink=True)

def getMeshVertIndices(x,y,nx=2,ny=2):
    vert = []; indices = []
    X , Y = np.meshgrid(np.linspace(0,x,nx),np.linspace(-y/2,y/2,ny))
    # pts = np.array([[0, -y/2], [0, y/2], [x, -y/2], [x, y/2]])
    pts=np.array([X.flatten(),Y.flatten()]).T ; z = np.zeros((pts.shape[0],1)) 
    v = np.append(pts,z,axis=1); vert = list (map(tuple,v))
    tri = Delaunay(pts)
    indices = list (map(tuple,tri.simplices))
    return vert,indices

def OSM_BPY_CreatePlane(way,collection=None):
    print ("Way : %d , length, %f , nlanes : %d"%(way.id(), way.length(), way.lanes()))
    x = way.length();  y = 4. * way.lanes(); 
    nx = int (x/10) if x/10 > 2 else 2 
    ny = int (y/4) if y/4 > 2 else 2 
    vert,fac = getMeshVertIndices(x,y,nx,ny)
    pl_data = bpy.data.meshes.new(f"way_mesh_{way.id()}")
    pl_data.from_pydata(vert, [], fac)
    pl_obj = bpy.data.objects.new(f"way_road_{way.id()}", pl_data)
    pl_obj.hide_select = True
    if (collection):
        collection.objects.link(pl_obj)
    else:
        bpy.context.scene.collection.objects.link(pl_obj)
    return  pl_obj

def OSM_BPY_CurveModifier(way,pl_obj,curveobj):
    curve_modifier = pl_obj.modifiers.new(name=f"way_crv_{way.id()}_mod",type='CURVE')
    curve_modifier.object = curveobj


def OSM_BPY_CreateCurve(way,collection=None):
    coords_list = []
    for node in way.nodes():
        coords_list.append(node.xyz())
    crv = bpy.data.curves.new(f'crv_{way.id()}', 'CURVE')
    crv.dimensions = '3D'
    spline = crv.splines.new(type='NURBS')
    spline.points.add(len(coords_list)-1) 
    spline.use_endpoint_u = True
    # assign the point coordinates to the spline points
    for indx, coord in enumerate(coords_list):
        x,y,z = coord
        spline.points[indx].co = (x, y, z, 1)
    # make a new object with the curve
    obj = bpy.data.objects.new(f'way_{way.id()}', crv)
    obj.hide_render = True
    obj['way'] = way.id()
    if (collection):
        collection.objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)
    return obj


class OSM_OT_GetMapboxToken(bpy.types.Operator):
    bl_idname = "osm.get_mapbox_token"
    bl_label = ""
    bl_description = "Get Mapbox access token"
    bl_options = {'INTERNAL'}
    
    url = "https://www.mapbox.com/account/access-tokens"
    
    def execute(self, context):
        import webbrowser
        webbrowser.open_new_tab(self.url)
        return {'FINISHED'}



class OSMProperties(bpy.types.PropertyGroup):
    terrainObject: bpy.props.StringProperty(
        name = "Terrain",
        description = "Blender object for the terrain"
    )

    stLat : bpy.props.FloatProperty(
        name="st lat",
        description="Start latitude of the directions",
        precision = 4,
        min = -89.,
        max = 89.,
        default= 37.43517301818218
    )

    stLon: bpy.props.FloatProperty(
        name="st lon",
        description="Minimum longitude of the imported extent",
        precision = 4,
        min = -180.,
        max = 180.,
        default= -122.24382700003113
    )

    endLon: bpy.props.FloatProperty(
        name="end lon",
        description="Maximum longitude of the imported extent",
        precision = 4,
        min = -180.,
        max = 180.,
        default= -122.33172956217955
    )

    endLat: bpy.props.FloatProperty(
        name="end lat",
        description="End latitude of the directions",
        precision = 4,
        min = -89.,
        max = 89.,
        default= 37.50323045987249
    )

    imp_dataType: bpy.props.EnumProperty(
        name = "Data",
        items = getImportDataTypes(),
        description = "Data type for import",
        default = "osm"
    )

    exp_dataType: bpy.props.EnumProperty(
        name = "Data",
        items = getExportDataTypes(),
        description = "Data type for export",
        default = "xodr"
    )


class OSM_OT_ImportData(bpy.types.Operator):
    """Import data : OSM with / without terrain """
    bl_idname = "osm.import_data"
    bl_label = "import"
    bl_description = "Import data of the selected type (OpenStreetMap, terrain)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        a = blenderApp.app
        dataType = context.scene.osm.imp_dataType
        if (not a.setPreferences(context,self.report)):
            self.report({"ERROR"},"Set Peferences !!") 
            return {'FINISHED'}
        if dataType == "osm":
            return self.importOSM(context)
        return {'FINISHED'}

    def importOSM(self,context):
        a = blenderApp.app
        addon = context.scene.osm
        bpy.ops.object.select_all(action='DESELECT')
        osm_ways = a.osmDirections(addon.stLat,addon.stLon,addon.endLat,addon.endLon)
        osm_ways_c = bpy.data.collections.new("osm_ways")
        for way in osm_ways:
            # if (way.id() not in [27878050,27878048,619344037]): continue
            way_c = bpy.data.collections.new(f"osm_way_{way.id()}")
            curve_obj = OSM_BPY_CreateCurve(way,way_c)
            plane_obj = OSM_BPY_CreatePlane(way,way_c)
            OSM_BPY_CurveModifier(way,plane_obj,curve_obj)
            osm_ways_c.children.link(way_c)
        bpy.context.scene.collection.children.link(osm_ways_c)
        return {'FINISHED'}

class OSM_OT_ControlOverlay(bpy.types.Operator):
    bl_idname = "osm.control_overlay"
    bl_label = ""
    bl_description = "Control overlay import and display progress in the 3D View"
    bl_options = {'INTERNAL'}

    lineWidth = 80 

    def modal(self,context,event):
        if event.type == 'TIMER':
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

class OSM_OT_ExportData(bpy.types.Operator):
    """Import data : OSM with / without terrain """
    bl_idname = "osm.export_data"
    bl_label = "export"
    bl_description = "Export data of the selected type (OpenStreetMap, terrain)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        pass

class OSM_OT_SelectDirections(bpy.types.Operator):
    bl_idname = "osm.select_directions"
    bl_label = "select"
    bl_description = "Select extent for your area of interest on a geographical map"
    bl_options = {'INTERNAL'}
    
    def invoke(self, context, event):
        bl_url = "https://www.google.com/maps"
        webbrowser.open_new_tab(bl_url)
        return {'FINISHED'}

class OSM_OT_PasteDirections(bpy.types.Operator):
    bl_idname = "osm.paste_directions"
    bl_label = "paste"
    bl_description = "Paste url from google directions browser link"
    bl_options = {'INTERNAL','UNDO'}
    
    def invoke(self, context, event):
        addon = context.scene.osm 
        coords = context.window_manager.clipboard
        if not coords:
            self.report({'ERROR'}, "Nothing to paste!")
            return {'CANCELLED'}
        try:
            # parse the string from the clipboard to get coordinates of the extent
            coords = ((coords.split('dir/')[-1].split('@')[0])[:-1]).replace('/',',')
            coords = tuple( map(lambda s: float(s), coords.split(',')))
            if len(coords) != 4:
                raise ValueError
        except ValueError as error:
            self.report({'ERROR'}, "Invalid string to paste! %s"%(error))
            return {'CANCELLED'}
        addon.stLat = coords[0]
        addon.stLon = coords[1]
        addon.endLat = coords[2]
        addon.endLon = coords[3]
        
        return {'FINISHED'}

class OSM_OT_ClearDirections(bpy.types.Operator):
    bl_idname = "osm.clear_directions"
    bl_label = "clear"
    bl_description = "Clear directions on scene & internal"
    bl_options = {'INTERNAL','UNDO'}

    def invoke(self,context,event):
        app = blenderApp.app
        addon = context.scene.osm 
        collections = ['osm_ways','osm_ways.001']
        for collection in collections:
            del_collection(collection)
        app.osmClear()
        return {'FINISHED'}

class S1M_OT_sync_state(bpy.types.Operator):
    """Operator which runs itself from a timer"""
    bl_idname = "sim.sync_state_timer"
    bl_label = "Sim Sync State Timer Operator"

    _timer = None

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            # change theme color, silly!
            #update objects position based on state # below from example
            color = context.preferences.themes[0].view_3d.space.gradients.high_gradient
            color.s = 1.0
            color.h += 0.01

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class S1M_PT_OSM_panel_create(bpy.types.Panel):
    bl_idname = 'S1M_PT_OSM_panel_create'
    bl_label = 'OSM'
    bl_category = 'ADS1M'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    def draw(self,context):
        layout = self.layout
        addon = context.scene.osm
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Directions:")
        row = box.row(align=True)
        row.operator("osm.select_directions")
        row.operator("osm.paste_directions")
        row.operator("osm.clear_directions")

        row = box.row()
        row.prop(addon, "stLat")
        row.prop(addon, "stLon")
        row = box.row()
        row.prop(addon, "endLat")
        row.prop(addon, "endLon")
        box = layout.box() 
        row = box.row(align=True)
        row.prop(addon,"imp_dataType", text="")
        row.operator("osm.import_data", text="Import")
        box = layout.box() 
        row = box.row(align=True)
        row.prop(addon,"exp_dataType", text="")
        row.operator("osm.export_data", text="Export")


def register():
    bpy.types.Scene.osm = bpy.props.PointerProperty(type=OSMProperties)

def unregister():
    del bpy.types.Scene.osm
