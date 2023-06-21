""" Plugin.py

Contains the main functionality needed to integrate this plugin. the entry point from GOG is start_and_run_plugin but it can be run from main for testing.

CHANGELOG: 6/17/2023:
stripped down and re-implemented a barebones version of the plugin. For example, Tick no longer checks the local store for newly installed games. Removed all calls to backend steam network, this now uses
a dedicated "controller". For review purposes, you can think of the "controller" as a new steam network backend, without the interface cloak and dagger. any Steam-API related functionality is passed to the controller.
Any local lookups about the user's system (launch games, install size, etc) are handled here and are largely unchanged. 


"""



import platform
import asyncio
import logging
import traceback
import sys
import webbrowser
import subprocess
import time
import vdf

from typing import Dict, List, Any, AsyncGenerator, Union, Optional


from galaxy.api.types import Game, Subscription, SubscriptionGame, Achievement, NextStep, Authentication, GameTime, UserPresence, GameLibrarySettings, UserInfo, SubscriptionDiscovery
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform


from .version import __version__
from .steam_network.steam_network_controller import SteamNetworkController
from .client import local_games_list, get_library_folders, StateFlags, get_state_changes, get_client_executable, load_vdf, get_app_manifests, app_id_from_manifest_path
from uri_scheme_handler import is_uri_handler_installed

logger = logging.getLogger(__name__)

FAMILY_SHARE = "Steam Family Share"

def is_windows():
    return platform.system().lower() == "windows"


class SteamPlugin(Plugin):
    """Class that implements the steam plugin in a way that GOG Galaxy recognizes.

    Functionality is implemented by implementing abstract functions defined in the Plugin class from the galaxy api.
    Functionality that requires communication with Steam is handled by a dedicated SteamNetworkController instance within this class. 
    Functionality that interacts with the user's operating system, such as install size, launching a game, etc are handled in this class directly. 

    Background tasks are responsible for obtaining and caching information that GOG Galaxy Client will use in the future, but is not currently requesting. Steam occasionally gives us updates without us asking for them.
    """
    def __init__(self, reader, writer, token):
        super().__init__(Platform.Steam, __version__, reader, writer, token)
        self._controller = SteamNetworkController()

    #features are normally auto-detected. Since we only support one form of login, we can allow this behavior. 

    #region startup, login, and shutdown

    def handshake_complete(self):
        """ Called when the handshake between GOG Galaxy Client and this plugin has completed. 

        This means that GOG Galaxy Client recognizes our plugin and is communicating with us.
        Any initialization required on the client that is necessary for the plugin to work is now complete.
        This means things like the persistent cache are now available to us.
        """
        self._controller.handshake_complete()
    
    async def authenticate(self, stored_credentials : Dict[str, Any] = None) -> Union[Authentication, NextStep]:
        """ Called when the plugin attempts to log the user in. This occurs at the start, after the handshake.
 
        stored_credentials are a mapping of a name to data of any type that were saved from previous session(s)
        Returns either an Authentication object, which represents a successfuly login (from stored credentials) \
or a NextStep object, which tells GOG to display a webpage with the information necessary to get further login information from the user.
        """
        return await self._controller.authenticate(stored_credentials)

    async def pass_login_credentials(self, _ : str, credentials: Dict[str, str], cookies : List[Dict[str, str]]):
        """ Called when a webpage generated from a NextStep object completes.
        
        this function contains an unused string that is deprecated. it's value is not defined. 
        credentials contain the URL Parameters obtained from the end uri that caused the webpage to complete as a tuple of name and value.
        cookies is a list of cookies that may have been saved and available to the end uri. A cookie is a collection of tuples of name and value.

        Returns either an Authentication object, which represents a successfuly login or a NextStep object, \
with a new webpage to display, in the event the user improperly input their information, or needs to provide additional information such as 2FA.

        This function may be called multiple times when the user is logging in, depending on 2FA or failed login attempts.
        """
        await self._controller.pass_login_credentials(self, credentials, cookies)

    async def shutdown(self):
        """Called when GOG Galaxy Client is shutdown or the plugin is disconnected by the user. 
        """
        await self._controller.shutdown()
        pass

    #endregion End startup, login, and shutdown. 
    #region owned games and subscriptions
    async def get_owned_games(self) -> List[Game]:
        """ Get a list of games the user currently owns. Passed to controller.

        This is not a generator, i'm not sure why.
        """
        return await self._controller.get_owned_games()

    async def get_subscriptions(self) -> List[Subscription]:
        """ Get a list of subscriptions sources the user currently subscribes to. This is not the games themselves. 

        This is just the steam family share as far as i can tell. 
        """
        return [Subscription(FAMILY_SHARE, True, None, SubscriptionDiscovery.AUTOMATIC)] #defaults to you have it, even if it's no games.
        #return [Subscription(FAMILY_SHARE, None, None, SubscriptionDiscovery.AUTOMATIC)] #legal but i have no idea what happens. 


    async def prepare_subscription_games_context(self, subscription_names: List[str]) -> None:
        """ Start a batch process to get all subscription games for the list of available subscription sources.

        For Steam, there is only one source of subscriptions: Steam Family Share. This is the only one we need to process.
        Steam has one call that obtains all games at once, whether they are owned or subscription; however, it does tell us which a given game is.
        Preparing for subscription games will also begin preparing for owned games, and vice versa. \
If preparations for one of these functions has been started when the other is called, this call will have no effect.
        """
        if ("Steam Family Share" in subscription_names):
            await self._controller.prepare_family_share()

    #note to self, raise StopIterator to kill a generator. StopAsyncIterator is the async equivalent. there is no "yield break" in python.
    
    async def get_subscription_games(self, subscription_name: str, _: None) -> AsyncGenerator[List[SubscriptionGame], None]:
        """ Get a list of games asynchronously that the user has subscribed to.
        
        If the string is not "Steam Family Share" this value will return nothing. Context is unused. 
        """
        if (subscription_name != FAMILY_SHARE):
            raise StopAsyncIteration
        else:
            #can i just return the async generator itself? idk. so i'll just do this.
            async for item in self._controller.get_family_share_games():
                await item

    def subscription_games_import_complete(self):
        """ Updates all the imported games so they are written to the database cache.

        This is called after all subscription games are successfully imported. 
        """
        self._controller.subscription_games_import_complete()

    #endregion
    #region Achievements

    #as of this writing, there is no way to batch import achievements for multiple games. so this function does not add any functionality and actually bottlenecks the code. 
    #this is therefore unused. Should this ever change, the logic can be optimized by retrieving that info here and then caching it so the get_unlocked_achievements does not do anything.
    #async def prepare_achievements_context(self, game_ids: List[str]) -> Any:

    #as of this writing, prepare_achievements_context is not overridden and therefore returns None. That result is then passed in here, so the value here is also None.
    async def get_unlocked_achievements(self, game_id: str, _: None) -> List[Achievement]:
        """Get the unlocked achievements for the provided game id. 

        Games are imported one at a time because a batch import does not exist. Context is therefore None here. 
        """
        return await self._controller.get_unlocked_achievements(int(game_id))


    def achievements_import_complete(self):
        """Called when get_unlocked_achievements has been called on all game_ids. 
        """
        self._controller.achievements_import_complete()
    #endregion
    #region Play Time
    async def prepare_game_times_context(self, game_ids: List[str]) -> None:
        await self._controller.prepare_game_times_context(map(lambda x:int(x), game_ids))

    async def get_game_time(self, game_id: str, _: None) -> GameTime:
        return await self._controller.get_game_time(int(game_id))

    def game_times_import_complete(self):
        self._controller.game_times_import_complete()
    #endregion
    #region User-defined settings applied to their games
    async def prepare_game_library_settings_context(self, game_ids: List[str]) -> None:
        await self._controller.begin_get_tags_hidden_etc(map(lambda x: int(x), game_ids))

    async def get_game_library_settings(self, game_id: str, _: None) -> GameLibrarySettings:
        return await self.get_tags_hidden_etc(int(game_id))

    def game_library_settings_import_complete(self):
        self._controller.tags_hidden_etc_import_complete()
    #endregion
    #region friend info
    async def get_friends(self) -> List[UserInfo]:
        return await self._controller.get_friends()

    async def prepare_user_presence_context(self, user_ids: List[str]) -> None:
        await self._controller.prepare_user_presence(self, map(lambda x: int(x), user_ids))

    async def get_user_presence(self, user_id: str, _: None) -> UserPresence:
        return await self._controller.get_user_presence(int(user_id))

    def user_presence_import_complete(self):
        self._controller.user_presence_import_complete()
    #endregion
    
    def tick(self):
        self._controller.tick()
        pass

    #region get info about and/or update games on local system:

    async def get_local_games(self):
        #i do not understand why this was run in executor (it's not going to increase performance afaik) but i'm leaving it in as a comment if i'm wrong.
        #loop = asyncio.get_running_loop()
        #self._local_games_cache = await loop.run_in_executor(None, local_games_list)
        self._local_games_cache = local_games_list()
        return self._local_games_cache

    @staticmethod
    def _steam_command(command, game_id):
        if game_id == "499450": #witcher 3 hack?
            game_id = "292030"
        if is_uri_handler_installed("steam"):
            webbrowser.open("steam://{}/{}".format(command, game_id))
        else:
            webbrowser.open("https://store.steampowered.com/about/")

    async def install_game(self, game_id: str):
        """ installs the steam game with the given steam id.
        """
        SteamPlugin._steam_command("install", game_id)

    async def uninstall_game(self, game_id: str):
        """ Uninstalls the steam game with the given steam id.
        """
        
        SteamPlugin._steam_command("uninstall", game_id)

    async def launch_game(self, game_id: str):
        """ Launches the steam game with the given steam id.
        """
        
        SteamPlugin._steam_command("launch", game_id)

    @staticmethod
    def _parallel_get_size(id : str, manifest_path : str) -> Optional[int]:
        with open(manifest_path, encoding="utf-8", errors="replace") as vdf_file:
            data = vdf.loads()

    async def _parallel_prep_local_size(game_ids: List[str]) -> Dict[str, Optional[int]]:



    async def prepare_local_size_context(self, game_ids: List[str]) -> Dict[str, str]:
        library_folders = get_library_folders()
        app_manifests = list(get_app_manifests(library_folders))
        return {app_id_from_manifest_path(path): path for path in app_manifests}
        

    async def get_local_size(self, game_id: str, context: Dict[str, str]) -> Optional[int]:
        """ Returns the amount of space, in bytes, the game specificed by the game_id takes up on user storage. If it cannot be determined, returns None.
        """
        try:
            manifest_path = context[game_id]
        except KeyError:  # not installed
            return 0
        try:
            manifest = load_vdf(manifest_path)
            app_state = manifest["AppState"]
            state_flags = StateFlags(int(app_state["StateFlags"]))
            if StateFlags.FullyInstalled in state_flags:
                return int(app_state["SizeOnDisk"])
            else:  # as SizeOnDisk is 0
                return int(app_state["BytesDownloaded"])
        except Exception as e:
            logger.warning("Cannot parse SizeOnDisk in %s: %r", manifest_path, e)
            return None
    #endregion get info about and/or update games on local system:

    #region launching/closing games.

    async def shutdown_platform_client(self) -> None:
        """
        Shuts down the steam client. Steam Client launches automatically when a game is started due to DRM, but can be optionally closed on game exit, depending on user settings.

        This is called by the GOG Galaxy client. 
        """
        launch_debounce_time = 30
        if time.time() < self._last_launch + launch_debounce_time:
            # workaround for quickly closed game (Steam sometimes dumps false positive just after a launch)
            logging.info("Ignoring shutdown request because game was launched a moment ago")
            return
        if is_windows():
            exe = get_client_executable()
            if exe is None:
                return
            cmd = '"{}" -shutdown -silent'.format(exe)
        else:
            cmd = "osascript -e 'quit app \"Steam\"'"
        logger.debug("Running command '%s'", cmd)
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        await process.communicate()
    #endregion

def main():
    """ Program entry point. starts the entire plugin. 
    
    Usually not necessary because we are a plugin, but useful for testing
    """
    create_and_run_plugin(SteamPlugin, sys.argv)

#subprocessess check. clever! necessary for parallel processing on windows since it doesn't have "fork"
if __name__ == "__main__":
    main()