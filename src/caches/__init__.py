"""Caches

Due to the fact that there are numerous local caches that we use, it makes sense to store these in their own directory. It also makes sense to rework them.

We now have a "Local Persistent Cache" that stores all of these. Each cache will be named in this local persistent cache, and when we write data to it, each of these will be self-contained instead of dumping it to a larger dictionary. This will prevent name conflicts. We use json serialization to store the data in each cache, but it is their responsibility to dump and load their data to/from a dictionary that we use for de/serialization.

Please Note that JSON serialization is finicky. Anything that can be considered a Key is cast to a string. This is especially painful with dictionaries. Make sure your data is properly handled. 
Tuples are also lost in the caching process (converted to list), named tuples are preferred as a result.

the local cache dict is as follows:
"Local_Cache"
{
    "Version":<version string>
    "Username":<user name string>
    "Steam_Id":<steam id for user>
    "Friends_Cache":<Friends_Cache_Object>
    "Games Cache":<GamesCache Object>
    "Package Cache":<PackageCache Object>
    ...
    "
}

"""