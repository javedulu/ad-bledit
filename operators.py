import bpy
import sys
import os,math,webbrowser,json
import app.blender as blenderApp
import os
basepath = (os.path.dirname(os.path.join(os.getcwd(),__file__)))
sys.path.append(os.path.join(basepath,'pymap-0.0.1-py3.10-macosx-14.3-arm64.egg'))

import pymap


def getImportDataTypes():
    items = [
        ("osm","Open Street Map","OpenStreetMap"),
        ("terrain","Terrain","Terrain"),
        ("overlay", "Image Overlay", "Image overlay for the terrain, e.g. satellite imagery or a map")
    ]
    return items

def getExportDataTypes():
    items = [
        ("xodr","Open Drive","Open Drive"),
        ("fbx","Autodesk FBX","Autodesk FBX"),
        ("usdz","Pixar USDZ","Universal Scene Description")
    ]
    return items

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

class S1M3n8Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    dataDir: bpy.props.StringProperty(
        name = '',
        subtype = 'DIR_PATH',
        description = "Directory to store downloaded OpenStreetMap and terrain files"
    )
    mapboxAccessToken: bpy.props.StringProperty(
        name = "Mapbox access token",
        description = "A string token to access overlays from Mapbox company"
    )
    osmServer: bpy.props.EnumProperty(
        name = "OSM data server",
        items = (
            ("overpass-api.de", "overpass-api.de: 8 cores, 128 GB RAM", "overpass-api.de: 8 cores, 128 GB RAM"),
            ("vk maps", "VK Maps: 56 cores, 384 GB RAM", "VK Maps: 56 cores, 384 GB RAM"),
            ("kumi.systems", "kumi.systems: 20 cores, 256 GB RAM", "kumi.systems: 20 cores, 256 GB RAM")
        ),
        description = "OSM data server if the default one is inaccessible",
        default = "overpass-api.de"
    )

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.9)
        split.prop(self, "mapboxAccessToken")
        split.operator("osm.get_mapbox_token", text="Get it!")



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
        default= 40.7463 
    )

    stLon: bpy.props.FloatProperty(
        name="st lon",
        description="Minimum longitude of the imported extent",
        precision = 4,
        min = -180.,
        max = 180.,
        default= -73.9892 
    )

    endLon: bpy.props.FloatProperty(
        name="end lon",
        description="Maximum longitude of the imported extent",
        precision = 4,
        min = -180.,
        max = 180.,
        default= -73.9812
    )

    endLat: bpy.props.FloatProperty(
        name="end lat",
        description="End latitude of the directions",
        precision = 4,
        min = -89.,
        max = 89.,
        default= 40.7523 
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
        app = blenderApp.app

class OSM_OT_ExportData(bpy.types.Operator):
    """Import data : OSM with / without terrain """
    bl_idname = "osm.export_data"
    bl_label = "export"
    bl_description = "Export data of the selected type (OpenStreetMap, terrain)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        app = blenderApp.app

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
        print (coords)
        
        addon.stLat = coords[0]
        addon.stLon = coords[1]
        addon.endLat = coords[2]
        addon.endLon = coords[3]
        
        return {'FINISHED'}

class S1M_PT_OSM_panel_create(bpy.types.Panel):
    bl_idname = 'S1M_PT_OSM_panel_create'
    bl_label = 'OSM'
    bl_category = 's1m3n8'
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