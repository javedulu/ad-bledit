# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "ads1m",
    "author" : "Javed Shaik <javedulu@gmail.com>",
    "description" : "Autonmous Driving Simulation",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View 3D > Sidebar > \"ads1m\" tab",
    "tracker_url": "https://github.com/javedulu/ad-bledit/issues",
    "doc_url": "https://github.com/javedulu/ad-bledit/blob/main/README.md",
    "warning" : "",
    "category" : "ADAS/AD"
}

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

from . import s1mapp as blenderApp



class S1m3n8Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    dataDir: bpy.props.StringProperty(
        name = '',
        subtype = 'DIR_PATH',
        description = "Directory to store downloaded OpenStreetMap and terrain files",
        default = "/tmp/"
    )
    mapboxAccessToken: bpy.props.StringProperty(
        name = "Mapbox Token",
        description = "A string token to access directions from Mapbox company",
        default = ""
    )
    osmServer: bpy.props.EnumProperty(
        name = "OSM data server",
        items = (
            ("overpass-api.de", "overpass-api.de: 8 cores, 128 GB RAM", "overpass-api.de: 8 cores, 128 GB RAM"),
            ("maps.mail.ru/osm/tools/overpass", "VK Maps: 56 cores, 384 GB RAM", "VK Maps: 56 cores, 384 GB RAM"),
            ("overpass.kumi.systems", "kumi.systems: 20 cores, 256 GB RAM", "kumi.systems: 20 cores, 256 GB RAM")
        ),
        description = "OSM data server if the default one is inaccessible",
        default = "overpass-api.de"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Directory to store downloaded OpenStreetMap and terrain files:")
        layout.prop(self, "dataDir")
        split = layout.split(factor=0.9)
        split.prop(self, "mapboxAccessToken")
        split.operator("osm.get_mapbox_token", text="Link !")
        layout.prop(self, "osmServer")

blenderApp.app.addonName = S1m3n8Preferences.bl_idname

from . import auto_load

auto_load.init()


def register():
    bpy.utils.register_class(S1m3n8Preferences)
    auto_load.register()

def unregister():
    bpy.utils.unregister_class(S1m3n8Preferences)
    auto_load.unregister()
