from __future__ import annotations
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: steammessages_player.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import List

import betterproto

from .steammessages_base import EBanContentCheckResult, UserContentDescriptorPreferences
from .enums import ECommunityItemClass, ENewSteamAnnouncementState, EProfileCustomizationType


class EProfileCustomizationStyle(betterproto.Enum):
    k_EProfileCustomizationStyleDefault = 0
    k_EProfileCustomizationStyleSelected = 1
    k_EProfileCustomizationStyleRarest = 2
    k_EProfileCustomizationStyleMostRecent = 3
    k_EProfileCustomizationStyleRandom = 4
    k_EProfileCustomizationStyleHighestRated = 5


class EAgreementType(betterproto.Enum):
    k_EAgreementType_Invalid = -1
    k_EAgreementType_GlobalSSA = 0
    k_EAgreementType_ChinaSSA = 1


class ENotificationSetting(betterproto.Enum):
    k_ENotificationSettingNotifyUseDefault = 0
    k_ENotificationSettingAlways = 1
    k_ENotificationSettingNever = 2


class ETextFilterSetting(betterproto.Enum):
    k_ETextFilterSettingSteamLabOptedOut = 0
    k_ETextFilterSettingEnabled = 1
    k_ETextFilterSettingEnabledAllowProfanity = 2
    k_ETextFilterSettingDisabled = 3


@dataclass
class CPlayer_GetMutualFriendsForIncomingInvites_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_IncomingInviteMutualFriendList(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    mutual_friend_account_ids: List[int] = betterproto.uint32_field(2)


@dataclass
class CPlayer_GetMutualFriendsForIncomingInvites_Response(betterproto.Message):
    incoming_invite_mutual_friends_lists: List[
        CPlayer_IncomingInviteMutualFriendList
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetOwnedGames_Request(betterproto.Message):
    steamid: int = betterproto.uint64_field(1)
    include_appinfo: bool = betterproto.bool_field(2)
    include_played_free_games: bool = betterproto.bool_field(3)
    appids_filter: List[int] = betterproto.uint32_field(4)
    include_free_sub: bool = betterproto.bool_field(5)
    skip_unvetted_apps: bool = betterproto.bool_field(6)
    language: str = betterproto.string_field(7)
    include_extended_appinfo: bool = betterproto.bool_field(8)


@dataclass
class CPlayer_GetOwnedGames_Response(betterproto.Message):
    game_count: int = betterproto.uint32_field(1)
    games: List[CPlayer_GetOwnedGames_ResponseGame] = betterproto.message_field(2)


@dataclass
class CPlayer_GetOwnedGames_ResponseGame(betterproto.Message):
    appid: int = betterproto.int32_field(1)
    name: str = betterproto.string_field(2)
    playtime_2weeks: int = betterproto.int32_field(3)
    playtime_forever: int = betterproto.int32_field(4)
    img_icon_url: str = betterproto.string_field(5)
    has_community_visible_stats: bool = betterproto.bool_field(7)
    playtime_windows_forever: int = betterproto.int32_field(8)
    playtime_mac_forever: int = betterproto.int32_field(9)
    playtime_linux_forever: int = betterproto.int32_field(10)
    rtime_last_played: int = betterproto.uint32_field(11)
    capsule_filename: str = betterproto.string_field(12)
    sort_as: str = betterproto.string_field(13)
    has_workshop: bool = betterproto.bool_field(14)
    has_market: bool = betterproto.bool_field(15)
    has_dlc: bool = betterproto.bool_field(16)
    has_leaderboards: bool = betterproto.bool_field(17)
    content_descriptorids: List[int] = betterproto.uint32_field(18)
    playtime_disconnected: int = betterproto.int32_field(19)


@dataclass
class CPlayer_GetPlayNext_Request(betterproto.Message):
    max_age_seconds: int = betterproto.uint32_field(1)
    ignore_appids: List[int] = betterproto.uint32_field(2)


@dataclass
class CPlayer_GetPlayNext_Response(betterproto.Message):
    last_update_time: int = betterproto.uint32_field(1)
    appids: List[int] = betterproto.uint32_field(2)


@dataclass
class CPlayer_GetFriendsGameplayInfo_Request(betterproto.Message):
    appid: int = betterproto.uint32_field(1)


@dataclass
class CPlayer_GetFriendsGameplayInfo_Response(betterproto.Message):
    your_info: CPlayer_GetFriendsGameplayInfo_ResponseOwnGameplayInfo = (
        betterproto.message_field(1)
    )
    in_game: List[
        CPlayer_GetFriendsGameplayInfo_ResponseFriendsGameplayInfo
    ] = betterproto.message_field(2)
    played_recently: List[
        CPlayer_GetFriendsGameplayInfo_ResponseFriendsGameplayInfo
    ] = betterproto.message_field(3)
    played_ever: List[
        CPlayer_GetFriendsGameplayInfo_ResponseFriendsGameplayInfo
    ] = betterproto.message_field(4)
    owns: List[
        CPlayer_GetFriendsGameplayInfo_ResponseFriendsGameplayInfo
    ] = betterproto.message_field(5)
    in_wishlist: List[
        CPlayer_GetFriendsGameplayInfo_ResponseFriendsGameplayInfo
    ] = betterproto.message_field(6)


@dataclass
class CPlayer_GetFriendsGameplayInfo_ResponseFriendsGameplayInfo(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    minutes_played: int = betterproto.uint32_field(2)
    minutes_played_forever: int = betterproto.uint32_field(3)


@dataclass
class CPlayer_GetFriendsGameplayInfo_ResponseOwnGameplayInfo(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    minutes_played: int = betterproto.uint32_field(2)
    minutes_played_forever: int = betterproto.uint32_field(3)
    in_wishlist: bool = betterproto.bool_field(4)
    owned: bool = betterproto.bool_field(5)


@dataclass
class CPlayer_GetGameBadgeLevels_Request(betterproto.Message):
    appid: int = betterproto.uint32_field(1)


@dataclass
class CPlayer_GetGameBadgeLevels_Response(betterproto.Message):
    player_level: int = betterproto.uint32_field(1)
    badges: List[
        CPlayer_GetGameBadgeLevels_ResponseBadge
    ] = betterproto.message_field(2)


@dataclass
class CPlayer_GetGameBadgeLevels_ResponseBadge(betterproto.Message):
    level: int = betterproto.int32_field(1)
    series: int = betterproto.int32_field(2)
    border_color: int = betterproto.uint32_field(3)


@dataclass
class CPlayer_GetProfileBackground_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class ProfileItem(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)
    image_small: str = betterproto.string_field(2)
    image_large: str = betterproto.string_field(3)
    name: str = betterproto.string_field(4)
    item_title: str = betterproto.string_field(5)
    item_description: str = betterproto.string_field(6)
    appid: int = betterproto.uint32_field(7)
    item_type: int = betterproto.uint32_field(8)
    item_class: int = betterproto.uint32_field(9)
    movie_webm: str = betterproto.string_field(10)
    movie_mp4: str = betterproto.string_field(11)
    movie_webm_small: str = betterproto.string_field(13)
    movie_mp4_small: str = betterproto.string_field(14)
    equipped_flags: int = betterproto.uint32_field(12)
    profile_colors: List[ProfileItemProfileColor] = betterproto.message_field(15)


@dataclass
class ProfileItemProfileColor(betterproto.Message):
    style_name: str = betterproto.string_field(1)
    color: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetProfileBackground_Response(betterproto.Message):
    profile_background: ProfileItem = betterproto.message_field(1)


@dataclass
class CPlayer_SetProfileBackground_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_SetProfileBackground_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetMiniProfileBackground_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetMiniProfileBackground_Response(betterproto.Message):
    profile_background: ProfileItem = betterproto.message_field(1)


@dataclass
class CPlayer_SetMiniProfileBackground_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_SetMiniProfileBackground_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetAvatarFrame_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetAvatarFrame_Response(betterproto.Message):
    avatar_frame: ProfileItem = betterproto.message_field(1)


@dataclass
class CPlayer_SetAvatarFrame_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_SetAvatarFrame_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetAnimatedAvatar_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetAnimatedAvatar_Response(betterproto.Message):
    avatar: ProfileItem = betterproto.message_field(1)


@dataclass
class CPlayer_SetAnimatedAvatar_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_SetAnimatedAvatar_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetSteamDeckKeyboardSkin_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetSteamDeckKeyboardSkin_Response(betterproto.Message):
    steam_deck_keyboard_skin: ProfileItem = betterproto.message_field(1)


@dataclass
class CPlayer_SetSteamDeckKeyboardSkin_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_SetSteamDeckKeyboardSkin_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetProfileItemsOwned_Request(betterproto.Message):
    language: str = betterproto.string_field(1)
    filters: List[ECommunityItemClass] = betterproto.enum_field(2)


@dataclass
class CPlayer_GetProfileItemsOwned_Response(betterproto.Message):
    profile_backgrounds: List[ProfileItem] = betterproto.message_field(1)
    mini_profile_backgrounds: List[ProfileItem] = betterproto.message_field(2)
    avatar_frames: List[ProfileItem] = betterproto.message_field(3)
    animated_avatars: List[ProfileItem] = betterproto.message_field(4)
    profile_modifiers: List[ProfileItem] = betterproto.message_field(5)
    steam_deck_keyboard_skins: List[ProfileItem] = betterproto.message_field(6)
    steam_deck_startup_movies: List[ProfileItem] = betterproto.message_field(7)


@dataclass
class CPlayer_GetProfileItemsEquipped_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetProfileItemsEquipped_Response(betterproto.Message):
    profile_background: ProfileItem = betterproto.message_field(1)
    mini_profile_background: ProfileItem = betterproto.message_field(2)
    avatar_frame: ProfileItem = betterproto.message_field(3)
    animated_avatar: ProfileItem = betterproto.message_field(4)
    profile_modifier: ProfileItem = betterproto.message_field(5)
    steam_deck_keyboard_skin: ProfileItem = betterproto.message_field(6)


@dataclass
class CPlayer_SetEquippedProfileItemFlags_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)
    flags: int = betterproto.uint32_field(2)


@dataclass
class CPlayer_SetEquippedProfileItemFlags_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetEmoticonList_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_GetEmoticonList_Response(betterproto.Message):
    emoticons: List[
        CPlayer_GetEmoticonList_ResponseEmoticon
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetEmoticonList_ResponseEmoticon(betterproto.Message):
    name: str = betterproto.string_field(1)
    count: int = betterproto.int32_field(2)
    time_last_used: int = betterproto.uint32_field(3)
    use_count: int = betterproto.uint32_field(4)
    time_received: int = betterproto.uint32_field(5)
    appid: int = betterproto.uint32_field(6)


@dataclass
class CPlayer_GetTopAchievementsForGames_Request(betterproto.Message):
    steamid: int = betterproto.uint64_field(1)
    language: str = betterproto.string_field(2)
    max_achievements: int = betterproto.uint32_field(3)
    appids: List[int] = betterproto.uint32_field(4)


@dataclass
class CPlayer_GetTopAchievementsForGames_Response(betterproto.Message):
    games: List[
        CPlayer_GetTopAchievementsForGames_ResponseGame
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetTopAchievementsForGames_ResponseAchievement(betterproto.Message):
    statid: int = betterproto.uint32_field(1)
    bit: int = betterproto.uint32_field(2)
    name: str = betterproto.string_field(3)
    desc: str = betterproto.string_field(4)
    icon: str = betterproto.string_field(5)
    icon_gray: str = betterproto.string_field(6)
    hidden: bool = betterproto.bool_field(7)
    player_percent_unlocked: str = betterproto.string_field(8)


@dataclass
class CPlayer_GetTopAchievementsForGames_ResponseGame(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    total_achievements: int = betterproto.uint32_field(2)
    achievements: List[
        CPlayer_GetTopAchievementsForGames_ResponseAchievement
    ] = betterproto.message_field(3)


@dataclass
class CPlayer_GetAchievementsProgress_Request(betterproto.Message):
    steamid: int = betterproto.uint64_field(1)
    language: str = betterproto.string_field(2)
    appids: List[int] = betterproto.uint32_field(3)


@dataclass
class CPlayer_GetAchievementsProgress_Response(betterproto.Message):
    achievement_progress: List[
        CPlayer_GetAchievementsProgress_ResponseAchievementProgress
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetAchievementsProgress_ResponseAchievementProgress(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    unlocked: int = betterproto.uint32_field(2)
    total: int = betterproto.uint32_field(3)
    percentage: float = betterproto.float_field(4)
    all_unlocked: bool = betterproto.bool_field(5)
    cache_time: int = betterproto.uint32_field(6)


@dataclass
class CPlayer_GetGameAchievements_Request(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    language: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetGameAchievements_Response(betterproto.Message):
    achievements: List[
        CPlayer_GetGameAchievements_ResponseAchievement
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetGameAchievements_ResponseAchievement(betterproto.Message):
    internal_name: str = betterproto.string_field(1)
    localized_name: str = betterproto.string_field(2)
    localized_desc: str = betterproto.string_field(3)
    icon: str = betterproto.string_field(4)
    icon_gray: str = betterproto.string_field(5)
    hidden: bool = betterproto.bool_field(6)
    player_percent_unlocked: str = betterproto.string_field(7)


@dataclass
class CPlayer_GetFavoriteBadge_Request(betterproto.Message):
    steamid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_GetFavoriteBadge_Response(betterproto.Message):
    has_favorite_badge: bool = betterproto.bool_field(1)
    badgeid: int = betterproto.uint32_field(2)
    communityitemid: int = betterproto.uint64_field(3)
    item_type: int = betterproto.uint32_field(4)
    border_color: int = betterproto.uint32_field(5)
    appid: int = betterproto.uint32_field(6)
    level: int = betterproto.uint32_field(7)


@dataclass
class CPlayer_SetFavoriteBadge_Request(betterproto.Message):
    communityitemid: int = betterproto.uint64_field(1)
    badgeid: int = betterproto.uint32_field(2)


@dataclass
class CPlayer_SetFavoriteBadge_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetProfileCustomization_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    include_inactive_customizations: bool = betterproto.bool_field(2)
    include_purchased_customizations: bool = betterproto.bool_field(3)


@dataclass
class ProfileCustomizationSlot(betterproto.Message):
    slot: int = betterproto.uint32_field(1)
    appid: int = betterproto.uint32_field(2)
    publishedfileid: int = betterproto.uint64_field(3)
    item_assetid: int = betterproto.uint64_field(4)
    item_contextid: int = betterproto.uint64_field(5)
    notes: str = betterproto.string_field(6)
    title: str = betterproto.string_field(7)
    accountid: int = betterproto.uint32_field(8)
    badgeid: int = betterproto.uint32_field(9)
    border_color: int = betterproto.uint32_field(10)
    item_classid: int = betterproto.uint64_field(11)
    item_instanceid: int = betterproto.uint64_field(12)
    ban_check_result: EBanContentCheckResult = betterproto.enum_field(13)
    replay_year: int = betterproto.uint32_field(14)


@dataclass
class ProfileCustomization(betterproto.Message):
    customization_type: EProfileCustomizationType = betterproto.enum_field(1)
    large: bool = betterproto.bool_field(2)
    slots: List[ProfileCustomizationSlot] = betterproto.message_field(3)
    active: bool = betterproto.bool_field(4)
    customization_style: EProfileCustomizationStyle = betterproto.enum_field(5)
    purchaseid: int = betterproto.uint64_field(6)
    level: int = betterproto.uint32_field(7)


@dataclass
class ProfileTheme(betterproto.Message):
    theme_id: str = betterproto.string_field(1)
    title: str = betterproto.string_field(2)


@dataclass
class ProfilePreferences(betterproto.Message):
    hide_profile_awards: bool = betterproto.bool_field(1)


@dataclass
class CPlayer_GetProfileCustomization_Response(betterproto.Message):
    customizations: List[ProfileCustomization] = betterproto.message_field(1)
    slots_available: int = betterproto.uint32_field(2)
    profile_theme: ProfileTheme = betterproto.message_field(3)
    purchased_customizations: List[
        CPlayer_GetProfileCustomization_ResponsePurchasedCustomization
    ] = betterproto.message_field(4)
    profile_preferences: ProfilePreferences = betterproto.message_field(5)


@dataclass
class CPlayer_GetProfileCustomization_ResponsePurchasedCustomization(
    betterproto.Message
):
    purchaseid: int = betterproto.uint64_field(1)
    customization_type: EProfileCustomizationType = betterproto.enum_field(2)
    level: int = betterproto.uint32_field(3)


@dataclass
class CPlayer_GetPurchasedProfileCustomizations_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)


@dataclass
class CPlayer_GetPurchasedProfileCustomizations_Response(betterproto.Message):
    purchased_customizations: List[
        CPlayer_GetPurchasedProfileCustomizations_ResponsePurchasedCustomization
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetPurchasedProfileCustomizations_ResponsePurchasedCustomization(
    betterproto.Message
):
    purchaseid: int = betterproto.uint64_field(1)
    customization_type: EProfileCustomizationType = betterproto.enum_field(2)


@dataclass
class CPlayer_GetPurchasedAndUpgradedProfileCustomizations_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)


@dataclass
class CPlayer_GetPurchasedAndUpgradedProfileCustomizations_Response(
    betterproto.Message
):
    purchased_customizations: List[
        CPlayer_GetPurchasedAndUpgradedProfileCustomizations_ResponsePurchasedCustomization
    ] = betterproto.message_field(1)
    upgraded_customizations: List[
        CPlayer_GetPurchasedAndUpgradedProfileCustomizations_ResponseUpgradedCustomization
    ] = betterproto.message_field(2)


@dataclass
class CPlayer_GetPurchasedAndUpgradedProfileCustomizations_ResponsePurchasedCustomization(
    betterproto.Message
):
    customization_type: EProfileCustomizationType = betterproto.enum_field(1)
    count: int = betterproto.uint32_field(2)


@dataclass
class CPlayer_GetPurchasedAndUpgradedProfileCustomizations_ResponseUpgradedCustomization(
    betterproto.Message
):
    customization_type: EProfileCustomizationType = betterproto.enum_field(1)
    level: int = betterproto.uint32_field(2)


@dataclass
class CPlayer_GetProfileThemesAvailable_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_GetProfileThemesAvailable_Response(betterproto.Message):
    profile_themes: List[ProfileTheme] = betterproto.message_field(1)


@dataclass
class CPlayer_SetProfileTheme_Request(betterproto.Message):
    theme_id: str = betterproto.string_field(1)


@dataclass
class CPlayer_SetProfileTheme_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_SetProfilePreferences_Request(betterproto.Message):
    profile_preferences: ProfilePreferences = betterproto.message_field(1)


@dataclass
class CPlayer_SetProfilePreferences_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_PostStatusToFriends_Request(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    status_text: str = betterproto.string_field(2)


@dataclass
class CPlayer_PostStatusToFriends_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetPostedStatus_Request(betterproto.Message):
    steamid: int = betterproto.uint64_field(1)
    postid: int = betterproto.uint64_field(2)


@dataclass
class CPlayer_GetPostedStatus_Response(betterproto.Message):
    accountid: int = betterproto.uint32_field(1)
    postid: int = betterproto.uint64_field(2)
    status_text: str = betterproto.string_field(3)
    deleted: bool = betterproto.bool_field(4)
    appid: int = betterproto.uint32_field(5)


@dataclass
class CPlayer_DeletePostedStatus_Request(betterproto.Message):
    postid: int = betterproto.uint64_field(1)


@dataclass
class CPlayer_DeletePostedStatus_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetLastPlayedTimes_Request(betterproto.Message):
    min_last_played: int = betterproto.uint32_field(1)


@dataclass
class CPlayer_GetLastPlayedTimes_Response(betterproto.Message):
    games: List[CPlayer_GetLastPlayedTimes_ResponseGame] = betterproto.message_field(
        1
    )


@dataclass
class CPlayer_GetLastPlayedTimes_ResponseGame(betterproto.Message):
    appid: int = betterproto.int32_field(1)
    last_playtime: int = betterproto.uint32_field(2)
    playtime_2weeks: int = betterproto.int32_field(3)
    playtime_forever: int = betterproto.int32_field(4)
    first_playtime: int = betterproto.uint32_field(5)
    playtime_windows_forever: int = betterproto.int32_field(6)
    playtime_mac_forever: int = betterproto.int32_field(7)
    playtime_linux_forever: int = betterproto.int32_field(8)
    first_windows_playtime: int = betterproto.uint32_field(9)
    first_mac_playtime: int = betterproto.uint32_field(10)
    first_linux_playtime: int = betterproto.uint32_field(11)
    last_windows_playtime: int = betterproto.uint32_field(12)
    last_mac_playtime: int = betterproto.uint32_field(13)
    last_linux_playtime: int = betterproto.uint32_field(14)
    playtime_disconnected: int = betterproto.uint32_field(15)


@dataclass
class CPlayer_GetTimeSSAAccepted_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_GetTimeSSAAccepted_Response(betterproto.Message):
    time_ssa_accepted: int = betterproto.uint32_field(1)
    time_ssa_updated: int = betterproto.uint32_field(2)
    time_chinassa_accepted: int = betterproto.uint32_field(3)


@dataclass
class CPlayer_AcceptSSA_Request(betterproto.Message):
    agreement_type: EAgreementType = betterproto.enum_field(1)
    time_signed_utc: int = betterproto.uint32_field(2)


@dataclass
class CPlayer_AcceptSSA_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetNicknameList_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_GetNicknameList_Response(betterproto.Message):
    nicknames: List[
        CPlayer_GetNicknameList_ResponsePlayerNickname
    ] = betterproto.message_field(1)


@dataclass
class CPlayer_GetNicknameList_ResponsePlayerNickname(betterproto.Message):
    accountid: float = betterproto.fixed32_field(1)
    nickname: str = betterproto.string_field(2)


@dataclass
class CPlayer_GetPerFriendPreferences_Request(betterproto.Message):
    pass


@dataclass
class PerFriendPreferences(betterproto.Message):
    accountid: float = betterproto.fixed32_field(1)
    nickname: str = betterproto.string_field(2)
    notifications_showingame: ENotificationSetting = betterproto.enum_field(3)
    notifications_showonline: ENotificationSetting = betterproto.enum_field(4)
    notifications_showmessages: ENotificationSetting = betterproto.enum_field(5)
    sounds_showingame: ENotificationSetting = betterproto.enum_field(6)
    sounds_showonline: ENotificationSetting = betterproto.enum_field(7)
    sounds_showmessages: ENotificationSetting = betterproto.enum_field(8)
    notifications_sendmobile: ENotificationSetting = betterproto.enum_field(9)


@dataclass
class CPlayer_GetPerFriendPreferences_Response(betterproto.Message):
    preferences: List[PerFriendPreferences] = betterproto.message_field(1)


@dataclass
class CPlayer_SetPerFriendPreferences_Request(betterproto.Message):
    preferences: PerFriendPreferences = betterproto.message_field(1)


@dataclass
class CPlayer_SetPerFriendPreferences_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_AddFriend_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)


@dataclass
class CPlayer_AddFriend_Response(betterproto.Message):
    invite_sent: bool = betterproto.bool_field(1)
    friend_relationship: int = betterproto.uint32_field(2)
    result: int = betterproto.int32_field(3)


@dataclass
class CPlayer_RemoveFriend_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)


@dataclass
class CPlayer_RemoveFriend_Response(betterproto.Message):
    friend_relationship: int = betterproto.uint32_field(1)


@dataclass
class CPlayer_IgnoreFriend_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    unignore: bool = betterproto.bool_field(2)


@dataclass
class CPlayer_IgnoreFriend_Response(betterproto.Message):
    friend_relationship: int = betterproto.uint32_field(1)


@dataclass
class CPlayer_GetCommunityPreferences_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_CommunityPreferences(betterproto.Message):
    parenthesize_nicknames: bool = betterproto.bool_field(4)
    text_filter_setting: ETextFilterSetting = betterproto.enum_field(5)
    text_filter_ignore_friends: bool = betterproto.bool_field(6)
    text_filter_words_revision: int = betterproto.uint32_field(7)
    timestamp_updated: int = betterproto.uint32_field(3)


@dataclass
class CPlayer_GetCommunityPreferences_Response(betterproto.Message):
    preferences: CPlayer_CommunityPreferences = betterproto.message_field(1)
    content_descriptor_preferences: UserContentDescriptorPreferences = (
        betterproto.message_field(2)
    )


@dataclass
class CPlayer_SetCommunityPreferences_Request(betterproto.Message):
    preferences: CPlayer_CommunityPreferences = betterproto.message_field(1)


@dataclass
class CPlayer_SetCommunityPreferences_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetTextFilterWords_Request(betterproto.Message):
    pass


@dataclass
class CPlayer_TextFilterWords(betterproto.Message):
    text_filter_custom_banned_words: List[str] = betterproto.string_field(1)
    text_filter_custom_clean_words: List[str] = betterproto.string_field(2)
    text_filter_words_revision: int = betterproto.uint32_field(3)


@dataclass
class CPlayer_GetTextFilterWords_Response(betterproto.Message):
    words: CPlayer_TextFilterWords = betterproto.message_field(1)


@dataclass
class CPlayer_GetNewSteamAnnouncementState_Request(betterproto.Message):
    language: int = betterproto.int32_field(1)


@dataclass
class CPlayer_GetNewSteamAnnouncementState_Response(betterproto.Message):
    state: ENewSteamAnnouncementState = betterproto.enum_field(1)
    announcement_headline: str = betterproto.string_field(2)
    announcement_url: str = betterproto.string_field(3)
    time_posted: int = betterproto.uint32_field(4)
    announcement_gid: int = betterproto.uint64_field(5)


@dataclass
class CPlayer_UpdateSteamAnnouncementLastRead_Request(betterproto.Message):
    announcement_gid: int = betterproto.uint64_field(1)
    time_posted: int = betterproto.uint32_field(2)


@dataclass
class CPlayer_UpdateSteamAnnouncementLastRead_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_GetPrivacySettings_Request(betterproto.Message):
    pass


@dataclass
class CPrivacySettings(betterproto.Message):
    privacy_state: int = betterproto.int32_field(1)
    privacy_state_inventory: int = betterproto.int32_field(2)
    privacy_state_gifts: int = betterproto.int32_field(3)
    privacy_state_ownedgames: int = betterproto.int32_field(4)
    privacy_state_playtime: int = betterproto.int32_field(5)
    privacy_state_friendslist: int = betterproto.int32_field(6)


@dataclass
class CPlayer_GetPrivacySettings_Response(betterproto.Message):
    privacy_settings: CPrivacySettings = betterproto.message_field(1)


@dataclass
class CPlayer_GetDurationControl_Request(betterproto.Message):
    appid: int = betterproto.uint32_field(1)


@dataclass
class CPlayer_GetDurationControl_Response(betterproto.Message):
    is_enabled: bool = betterproto.bool_field(1)
    seconds: int = betterproto.int32_field(2)
    seconds_today: int = betterproto.int32_field(3)
    is_steamchina_account: bool = betterproto.bool_field(4)
    is_age_verified: bool = betterproto.bool_field(5)
    seconds_allowed_today: int = betterproto.uint32_field(6)
    age_verification_pending: bool = betterproto.bool_field(7)
    block_minors: bool = betterproto.bool_field(8)


@dataclass
class CPlayer_RecordDisconnectedPlaytime_Request(betterproto.Message):
    play_sessions: List[
        CPlayer_RecordDisconnectedPlaytime_RequestPlayHistory
    ] = betterproto.message_field(3)


@dataclass
class CPlayer_RecordDisconnectedPlaytime_RequestPlayHistory(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    session_time_start: int = betterproto.uint32_field(2)
    seconds: int = betterproto.uint32_field(3)
    offline: bool = betterproto.bool_field(4)


@dataclass
class CPlayer_RecordDisconnectedPlaytime_Response(betterproto.Message):
    pass


@dataclass
class CPlayer_LastPlayedTimes_Notification(betterproto.Message):
    games: List[CPlayer_GetLastPlayedTimes_ResponseGame] = betterproto.message_field(
        1
    )


@dataclass
class CPlayer_FriendNicknameChanged_Notification(betterproto.Message):
    accountid: float = betterproto.fixed32_field(1)
    nickname: str = betterproto.string_field(2)
    is_echo_to_self: bool = betterproto.bool_field(3)


@dataclass
class CPlayer_FriendEquippedProfileItemsChanged_Notification(betterproto.Message):
    accountid: float = betterproto.fixed32_field(1)


@dataclass
class CPlayer_NewSteamAnnouncementState_Notification(betterproto.Message):
    state: ENewSteamAnnouncementState = betterproto.enum_field(1)
    announcement_headline: str = betterproto.string_field(2)
    announcement_url: str = betterproto.string_field(3)
    time_posted: int = betterproto.uint32_field(4)
    announcement_gid: int = betterproto.uint64_field(5)


@dataclass
class CPlayer_CommunityPreferencesChanged_Notification(betterproto.Message):
    preferences: CPlayer_CommunityPreferences = betterproto.message_field(1)
    content_descriptor_preferences: UserContentDescriptorPreferences = (
        betterproto.message_field(2)
    )


@dataclass
class CPlayer_TextFilterWordsChanged_Notification(betterproto.Message):
    words: CPlayer_TextFilterWords = betterproto.message_field(1)


@dataclass
class CPlayer_PerFriendPreferencesChanged_Notification(betterproto.Message):
    accountid: float = betterproto.fixed32_field(1)
    preferences: PerFriendPreferences = betterproto.message_field(2)


@dataclass
class CPlayer_PrivacySettingsChanged_Notification(betterproto.Message):
    privacy_settings: CPrivacySettings = betterproto.message_field(1)
