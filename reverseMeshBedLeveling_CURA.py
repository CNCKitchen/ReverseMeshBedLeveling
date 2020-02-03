# Cura PostProcessingPlugin
# Author:   Stefan Hermann aka CNC Kitchen
# Date:     January 25,2020

# Description:  This plugin adds mesh bed leveling for any 3D printer without the need of a probe or a change in firmware.
#               
#               
#               

from ..Script import Script

class ReverseMeshBedLeveling(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Reverse Mesh Bed Leveling",
            "key": "ReverseMeshBedLeveling",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "extrapolate":
                {
                    "label": "Extrapolate corners?",
                    "description": "Extrapolate the leveling beyond the measured mesh",
                    "type": "bool",
                    "default_value": true
                },
                "levelingoffset":
                {
                    "label": "Leveling Offset",
                    "description": "Offset used during the measurements of the bed",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.1,
                    "minimum_value": 0.0
                },
                "LLgridpointX":
                {
                    "label": "Lower Left Grid Point - X",
                    "description": "Coordinates of lower left mesh grid point",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 20.0,
                },
                "LLgridpointY":
                {
                    "label": "Lower Left Grid Point - Y",
                    "description": "Coordinates of lower left mesh grid point",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 20.0,
                },
                "URgridpointX":
                {
                    "label": "Upper Right Grid Point - X",
                    "description": "Coordinates of upper right mesh grid point",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 20.0,
                },
                "URgridpointY":
                {
                    "label": "Upper Right Grid Point - Y",
                    "description": "Coordinates of upper right mesh grid point",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 20.0,
                },
            }
        }"""
    
    def execute(self, data):
        for layer in data:
            layer_index = data.index(layer)
            lines = layer.split("\n")
            first = True
            for line in lines:
                if first:
                    line_index = lines.index(line)
                    lines[line_index] = self.getSettingValueByKey("extrapolate") + self.getSettingValueByKey("levelingoffset") + self.getSettingValueByKey("LLgridpointX")
            final_lines = "\n".join(lines)
            data[layer_index] = final_lines
        return data