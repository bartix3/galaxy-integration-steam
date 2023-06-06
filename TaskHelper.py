from functools import cache
from typing import NamedTuple, Optional, List, Dict, Callable, Set, Iterator
from itertools import groupby
from importlib import import_module
from inspect import getmembers, isclass

import re
from re import Match
import os

#three steps to get this shit: 
#1: read original proto, get imports.
#2: read compiled proto, get missing references
#   a: find all forward references.
#   b: find all classes defined. difference on the set of forward references and defined classes. 
#3: for all imports (compiled form): 
#   a: get all classes defined. difference on the set of set from 2b and this result. 
def _retrieve_dependencies(file_name:str) -> List[str]:
    """
    for a file, return all <x> (as a string) in "import <x>" statements that we care about.
    """
    with open(file_name, "r") as file:
        data = file.read()
        matches: List[Match] = re.findall("^\s*import (\w+\.proto)", data)
        return list(map(lambda x: x.group(1), matches))

def _retrieve_classes(file_name:str) -> Set[str]:
    inspect_class = import_module(file_name)
    return set(map(lambda x,_: x, getmembers(inspect_class, isclass)))
        
def _retrieve_forward_references(file_data : str) -> Set[str]:
    matches: List[Match] = re.findall(":\s*\"(\w+)\"\s*=", file_data)
    return set(map(lambda x: x.group(1), matches))
        
def _cleanup_dependencies(file_name: str, convert_to_proto_file_name : Callable[[str], str], convert_to_compiled_file_name: Callable[[str], str], cached_lookup: Dict[str, Set[str]]):
    """Clean up the dependencies in a compiled proto file so that they reference properly.

    BetterProto loses import statements when converting the .proto to .py There's undoubtedly a patch somewhere but it's easier to install the existing version than a patched one, so i'll just fix it manually.
    This function adds "from <x> import <y>" statements to the compiled protos (.py), using the original .proto as a guide.
    If a proto definition tells us we need to import another file, we generate a list of all references to other classes in our compiled version.
    Some of these will refer to stuff defined in that compiled file, so we eliminate those. the rest are imports, so we search \
    through all of our imports until we find the classes we are missing. These are saved and convert to the "from <x> import <y,z...> strings.
    The compiled file is then updated so these are part of the code. 

    file_name (string): the name of the proto file we are working on
    convert_to_proto_file_name: function(string) -> string: takes the name of a proto file and appends the path to it so that we can open the corresponding proto file
    convert_to_compiled_file_name: function(string) -> string: takes the name of a proto file and appends the path to it so that we can open the corresponding compiled file
    cached_lookup: Dictionary[string, List[string]]: maps a file name to the names of all the classes the compiled proto with that file name. This makes it so we don't need to  
    """
    proto_file_name = convert_to_proto_file_name(file_name)
    compiled_file_name = convert_to_compiled_file_name(file_name)

    #if the proto file has any import statements
    deps = _retrieve_dependencies(proto_file_name)
    if (len(deps) > 0):
        #get all the classes in the compiled file, if not done already. cache the results. 
        if not (file_name in cached_lookup):
            cached_lookup[file_name] = _retrieve_classes(compiled_file_name)
        
        with open(compiled_file_name, "r+") as compiled_file:
            import_strings : List[str] = []

            compiled_data = compiled_file.read()
            forward_references = _retrieve_forward_references(compiled_data)
            forward_references -= cached_lookup[file_name]
            #loop through all imported classes  
            iterList : Iterator[str] = iter(deps)
            item = next(iterList, None)
            while len(forward_references) > 0 and item is not None:
                if not (item in cached_lookup):
                    item_compiled = convert_to_compiled_file_name(item)
                    cached_lookup[item] = _retrieve_classes(item_compiled)

                item_classes = cached_lookup[item]
                found_references = forward_references.intersection(item_classes)
                forward_references -= item_classes
                
                import_strings.append("from " + item + " import " + ", ".join(found_references))

                item = next(iterList, None)

            if (len(import_strings) > 0):
                replace_string = "import betterproto" + os.linesep + "from typing import TYPE_CHECKING" + os.linesep + \
                                 "if TYPE_CHECKING:" + os.linesep + "    " + (os.linesep + "    ").join(import_strings)
                compiled_data.replace("import betterproto", replace_string)
                compiled_file.write(compiled_data)

def cleanup_all_dependencies(all_files: List[str], convert_to_proto_file_name : Callable[[str], str], convert_to_compiled_file_name: Callable[[str], str]):
    cache : Dict[str, List[str]] = {}
    for file in all_files:
        _cleanup_dependencies(file, convert_to_proto_file_name, convert_to_compiled_file_name, cache)



