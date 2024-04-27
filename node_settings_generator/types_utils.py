from typing import Dict

doc_to_NTP_type_dict : Dict[str, str] = {
    "" : "",
    "boolean" : "ST.BOOL",
    "enum" : "ST.ENUM",
    "enum set" : "ST.ENUM_SET",
    "float" : "ST.FLOAT",
    "float array of 1" : "ST.VEC1",
    "float array of 2" : "ST.VEC2",
    "float array of 3" : "ST.VEC3",
    "float array of 4" : "ST.VEC4",
    "Image" : "ST.IMAGE",
    "int" : "ST.INT",
    "Mask" : "ST.MASK",
    "Material" : "ST.MATERIAL",
    "mathutils.Color" : "ST.COLOR",
    "mathutils.Vector of 3" : "ST.VEC3",
    "MovieClip" : "ST.MOVIE_CLIP",
    "NodeTree" : "ST.NODE_TREE",
    "Object" : "ST.OBJECT",
    "ParticleSystem" : "ST.PARTICLE_SYSTEM",
    "RepeatItem" : "ST.REPEAT_ITEM",
    "Scene" : "ST.SCENE",
    "SimulationStateItem" : "ST.SIMULATION_STATE_ITEM",
    "string" : "ST.STRING",
    "Text" : "ST.TEXT",
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
    return doc_to_NTP_type_dict[longest_prefix]