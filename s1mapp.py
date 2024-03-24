'''
'''
import os
import sys
import bpy
import shutil

basepath = (os.path.dirname(os.path.join(os.getcwd(),__file__)))
# sys.path.append(os.path.join(basepath,'pymap-0.0.1-py3.10-macosx-14.3-arm64.egg'))
sys.path.append(os.path.join(basepath,'pymap-0.0.1-py3.11-macosx-14-arm64.egg'))

for req in ['proj.db','egm96_15.gtx']:
    if (not os.path.isfile(os.path.join(os.getcwd(),req))):
        shutil.copy(os.path.join(basepath,req),os.getcwd())
    
import pymap

class S1MApp():
    def __init__(self):
        self._osm_ = pymap.osm()
        self.addonName = "__bpy__"
        self.hasPreferences = False
    
    def getDataDir(self,context,report):
        addonName = self.addonName
        prefs = context.preferences.addons 
        dataDir = prefs[addonName].preferences.dataDir if addonName in prefs else None
        if dataDir:
            dataDir = os.path.realpath(bpy.path.abspath(dataDir))
        else:
            report({'INFO'}, "Data Directory not set !! Check Preferences");
        return dataDir
    
    def getMapboxToken(self,context,report):
        addonName = self.addonName
        prefs = context.preferences.addons 
        mapboxToken = prefs[addonName].preferences.mapboxAccessToken if addonName in prefs else None 
        if not mapboxToken : 
            report({'INFO'}, "Mapbox Token not set !! Check Preferences");
        return mapboxToken

    def getOSMServer(self,context,report):
        addonName = self.addonName
        prefs = context.preferences.addons 
        osmServer = prefs[addonName].preferences.osmServer if addonName in prefs else None 
        if not osmServer : 
            report({'INFO'}, "OSM Server not set !! Check Preferences");
        return osmServer

    def setPreferences(self,context,report):
        dataDir = self.getDataDir(context,report)
        mapboxToken = self.getMapboxToken(context,report)
        osmServer = self.getOSMServer(context,report)
        if (mapboxToken): self._osm_.mapbox(mapboxToken)
        if (dataDir): self._osm_.scratch(dataDir)
        if (osmServer): self._osm_.overpass_api(osmServer)
        if (not mapboxToken or not dataDir or not osmServer): return False
        self.hasPreferences = True
        return True
    
    def osmDirections(self,stLat,stLon,endLat,endLon):
        if (not self.hasPreferences) : return 
        pts = []; pts.append(f"{stLat}, {stLon}"); pts.append(f"{endLat}, {endLon}"); 
        self._osm_.directions(pts)
        self._osm_.commit()
        return self._osm_.ways()

    def osmClear(self):
        return self._osm_.clear()

if "bpy" in sys.modules:
    app = S1MApp()
