from typing import List, Dict, Callable, Set, Iterator, Tuple

from re import Match, findall, sub, MULTILINE, search
#three steps to get this shit: 
#1: read original proto, get imports.
#2: read compiled proto, get missing references
#   a: find all forward references.
#   b: find all classes defined. difference on the set of forward references and defined classes. 
#3: for all imports (compiled form): 
#   a: get all classes defined. difference on the set of set from 2b and this result. 

PROTO_RESERVED_REGEX = "(?:optional|repeated)\s+\w+\s+(?:bytes|str)\s*="
FIND_RESERVED_WORDS_REGEX = "(bytes|str)\s*:\s*(\w+|List\[\s*\w+\s*\])\s*="

def _check_for_depedencies_or_reserved_variables(file_name:str) -> Tuple[List[str], bool]:
    """
    
    """
    with open(file_name, "r") as file:
        data = file.read()
        matches: List[Match[str]] = findall("^\s*import\s*\"([\w]+)\.proto\"\s*;", data, MULTILINE)
        matches_2 = [match.group(0) for match in matches]
        hasReserved: bool = search(PROTO_RESERVED_REGEX, data) is not None
        return matches_2, hasReserved


def _retrieve_classes(file_data:str) -> Set[str]:
    matches: List[Match] = findall("^\s*(?:class|enum)\s+(\w+)\s*\(", file_data, MULTILINE)
    return set(map(lambda x: x.group(0), matches))

def _retrieve_forward_references(file_data : str) -> Set[str]:
    matches : Set[str] = set(map(lambda x: x.group(0), findall(':\s*(?:List\s*\[\s*\r?\n?\s*|)"(\w+)"', file_data, MULTILINE))) #removes dupes during set cast. 
    return matches
        
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

    print("Cleaning up " + file_name)

    #any deps in the original proto mean we need to modify the file.
    deps, hasReservedWord = _check_for_depedencies_or_reserved_variables(proto_file_name)

    #we need to clean up the file anyway to update it to python 3.7 syntax.

    #get all the classes in the compiled file, if not done already. cache the results. 
    with open(compiled_file_name, "r+") as compiled_file:
        compiled_data = compiled_file.read()

        forward_references = _retrieve_forward_references(compiled_data)
        needs_cleanup: bool = len(forward_references) > 0
        if (len(deps) > 0):
            if not (file_name in cached_lookup):
                cached_lookup[file_name] = _retrieve_classes(compiled_data)

            import_strings : List[str] = []
            
            forward_references -= cached_lookup[file_name]
            #loop through all imported classes  
            iterList : Iterator[str] = iter(deps)
            item = next(iterList, None)
            while len(forward_references) > 0 and item is not None:
                print("searching for a reference in " + item)
                if not (item in cached_lookup):
                    item_compiled = convert_to_compiled_file_name(item)
                    with open(item_compiled, "r") as item_file:
                        item_data = item_file.read()
                        cached_lookup[item] = _retrieve_classes(item_data)

                item_classes = cached_lookup[item]
                found_references = list(forward_references.intersection(item_classes))
                found_references.sort()
                forward_references -= item_classes
                if (len(found_references) > 0):
                    import_strings.append("from ." + item + " import " + ", ".join(found_references))

                item = next(iterList, None)

            if len(import_strings) > 0:
                replace_string = "import betterproto\n\n" + "\n".join(import_strings)
                #print("Replace String " + replace_string)
                compiled_data = compiled_data.replace("import betterproto", replace_string)

        if (hasReservedWord):
            #fix issue with bytes or str in the protobuf variable definition
            compiled_data = sub(FIND_RESERVED_WORDS_REGEX, r"\1_: \2 =", compiled_data)


        if (needs_cleanup):
            compiled_data = "from __future__ import annotations\n" + compiled_data
            compiled_data = sub(r':\s*(List\s*\[\s*\r?\n?\s*|)"(\w+)"', r": \1\2", compiled_data)
            pass

        #print(compiled_data)
        compiled_file.seek(0)
        compiled_file.write(compiled_data)
        compiled_file.truncate()  # cut off the rest of the content to protect from weird errors when the new content is shorter than the old content

def cleanup_all_dependencies(all_files: List[str], convert_to_proto_file_name : Callable[[str], str], convert_to_compiled_file_name: Callable[[str], str]):
    cache : Dict[str, Set[str]] = {}
    for file in all_files:
        _cleanup_dependencies(file, convert_to_proto_file_name, convert_to_compiled_file_name, cache)



