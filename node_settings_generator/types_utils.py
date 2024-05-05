from typing import Dict

#types expected to be marked as read-only
READ_ONLY_TYPES = {
    "ST.BAKE_ITEMS",
    "ST.COLOR_RAMP",
    "ST.CRYPTOMATTE_ENTRIES",
    "ST.CURVE_MAPPING",
    "ST.ENUM_DEFINITION",
    "ST.FILE_SLOTS",
    "ST.IMAGE_FORMAT_SETTINGS",
    "ST.IMAGE_USER",
    "ST.LAYER_SLOTS",
    "ST.REPEAT_OUTPUT_ITEMS",
    "ST.SIM_OUTPUT_ITEMS",
    "ST.INDEX_SWITCH_ITEMS"
} 

doc_to_NTP_type_dict : Dict[str, str] = {
    "" : "",
    "bpy_prop_collection of CryptomatteEntry": "ST.CRYPTOMATTE_ENTRIES",
    "boolean" : "ST.BOOL",
    "ColorMapping" : None, # Always read-only
    "ColorRamp" : "ST.COLOR_RAMP",
    "CompositorNodeOutputFileFileSlots" : "ST.FILE_SLOTS",
    "CompositorNodeOutputFileLayerSlots" : "ST.LAYER_SLOTS",
    "CurveMapping" : "ST.CURVE_MAPPING",
    "enum" : "ST.ENUM",
    "enum set" : "ST.ENUM_SET",
    "float" : "ST.FLOAT",
    "float array of 1" : "ST.VEC1",
    "float array of 2" : "ST.VEC2",
    "float array of 3" : "ST.VEC3",
    "float array of 4" : "ST.VEC4",
    "Image" : "ST.IMAGE",
    "ImageFormatSettings" : "ST.IMAGE_FORMAT_SETTINGS",
    "ImageUser" : "ST.IMAGE_USER",
    "int" : "ST.INT",
    "Mask" : "ST.MASK",
    "Material" : "ST.MATERIAL",
    "mathutils.Color" : "ST.COLOR",
    "mathutils.Vector of 3" : "ST.VEC3",
    "MovieClip" : "ST.MOVIE_CLIP",
    "Node" : None, # (<4.2) Always used with zone inputs, need to make sure 
                   # output nodes exist. Handled separately from NTP attr system
    "NodeEnumDefinition" : "ST.ENUM_DEFINITION",
    "NodeGeometryBakeItems" : "ST.BAKE_ITEMS",
    "NodeGeometryRepeatOutputItems" : "ST.REPEAT_OUTPUT_ITEMS",
    "NodeGeometrySimulationOutputItems" : "ST.SIM_OUTPUT_ITEMS",
    "NodeIndexSwitchItems" : "ST.INDEX_SWITCH_ITEMS",
    "NodeTree" : "ST.NODE_TREE",
    "Object" : "ST.OBJECT",
    "ParticleSystem" : "ST.PARTICLE_SYSTEM",
    "PropertyGroup" : None, #Always read-only
    "RepeatItem" : None, #Always set with index
    "Scene" : "ST.SCENE",
    "SimulationStateItem" : None, #Always set with index
    "string" : "ST.STRING",
    "TexMapping" : None, #Always read-only
    "Text" : "ST.TEXT",
    "Texture" : "ST.TEXTURE",
    "VectorFont" : "ST.FONT"
}

def get_NTP_type(type_str: str) -> str:
    """
    Time complexity isn't great, might be able to optimize with 
    a trie or similar data structure
    """
    longest_prefix = ""
    for key in doc_to_NTP_type_dict.keys():
        if type_str.startswith(key) and len(key) > len(longest_prefix):
            longest_prefix = key

    if longest_prefix == "":
        print(f"Couldn't find prefix of {type_str.strip()} in dictionary")

    result = doc_to_NTP_type_dict[longest_prefix]
    
    is_readonly = "read" in type_str
    if is_readonly and result not in READ_ONLY_TYPES:
        return None
    else:
        return result