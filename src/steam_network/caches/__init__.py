"""Caches

Due to the fact that there are numerous local caches that we use, it makes sense to store these in their own directory. It also makes sense to rework them.

We now have a "Local Persistent Cache" that stores all of these. Each cache will be named in this local persistent cache, and when we write data to it, each of these will be self-contained instead of dumping it to a larger dictionary. This will prevent name conflicts. The return type for each of these should be a dict, but you can do whatever you want, so long as it works and is clean.

Version is stored in the local cache along with username and steam id. These are not secure credentials and help define whose data we're storing, so they are staying. Useful if the user that logs in does not match the cache data.

the local cache dict is as follows:
"Local_Cache"
{
    "Version":<version string>
    "Username":<user name string>
    "Steam_Id":<steam id for user>
    "Friends_Cache":<Friends_Cache_Object>
    "Games Cache":<GamesCache Object>
    ...
    "
}

"""