# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: steammessages_base.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import List

import betterproto


class EBanContentCheckResult(betterproto.Enum):
    k_EBanContentCheckResult_NotScanned = 0
    k_EBanContentCheckResult_Reset = 1
    k_EBanContentCheckResult_NeedsChecking = 2
    k_EBanContentCheckResult_VeryUnlikely = 5
    k_EBanContentCheckResult_Unlikely = 30
    k_EBanContentCheckResult_Possible = 50
    k_EBanContentCheckResult_Likely = 75
    k_EBanContentCheckResult_VeryLikely = 100


class EProtoClanEventType(betterproto.Enum):
    k_EClanOtherEvent = 1
    k_EClanGameEvent = 2
    k_EClanPartyEvent = 3
    k_EClanMeetingEvent = 4
    k_EClanSpecialCauseEvent = 5
    k_EClanMusicAndArtsEvent = 6
    k_EClanSportsEvent = 7
    k_EClanTripEvent = 8
    k_EClanChatEvent = 9
    k_EClanGameReleaseEvent = 10
    k_EClanBroadcastEvent = 11
    k_EClanSmallUpdateEvent = 12
    k_EClanPreAnnounceMajorUpdateEvent = 13
    k_EClanMajorUpdateEvent = 14
    k_EClanDLCReleaseEvent = 15
    k_EClanFutureReleaseEvent = 16
    k_EClanESportTournamentStreamEvent = 17
    k_EClanDevStreamEvent = 18
    k_EClanFamousStreamEvent = 19
    k_EClanGameSalesEvent = 20
    k_EClanGameItemSalesEvent = 21
    k_EClanInGameBonusXPEvent = 22
    k_EClanInGameLootEvent = 23
    k_EClanInGamePerksEvent = 24
    k_EClanInGameChallengeEvent = 25
    k_EClanInGameContestEvent = 26
    k_EClanIRLEvent = 27
    k_EClanNewsEvent = 28
    k_EClanBetaReleaseEvent = 29
    k_EClanInGameContentReleaseEvent = 30
    k_EClanFreeTrial = 31
    k_EClanSeasonRelease = 32
    k_EClanSeasonUpdate = 33
    k_EClanCrosspostEvent = 34
    k_EClanInGameEventGeneral = 35


class PartnerEventNotificationType(betterproto.Enum):
    k_EEventStart = 0
    k_EEventBroadcastStart = 1
    k_EEventMatchStart = 2
    k_EEventPartnerMaxType = 3


class CMsgProtoBufHeaderESessionDisposition(betterproto.Enum):
    k_ESessionDispositionNormal = 0
    k_ESessionDispositionDisconnect = 1


@dataclass
class CMsgIPAddress(betterproto.Message):
    v4: float = betterproto.fixed32_field(1, group="ip")
    v6: bytes = betterproto.bytes_field(2, group="ip")


@dataclass
class CMsgIPAddressBucket(betterproto.Message):
    original_ip_address: "CMsgIPAddress" = betterproto.message_field(1)
    bucket: float = betterproto.fixed64_field(2)


@dataclass
class CMsgGCRoutingProtoBufHeader(betterproto.Message):
    dst_gcid_queue: int = betterproto.uint64_field(1)
    dst_gc_dir_index: int = betterproto.uint32_field(2)


@dataclass
class CMsgProtoBufHeader(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    client_sessionid: int = betterproto.int32_field(2)
    routing_appid: int = betterproto.uint32_field(3)
    jobid_source: float = betterproto.fixed64_field(10)
    jobid_target: float = betterproto.fixed64_field(11)
    target_job_name: str = betterproto.string_field(12)
    seq_num: int = betterproto.int32_field(24)
    eresult: int = betterproto.int32_field(13)
    error_message: str = betterproto.string_field(14)
    auth_account_flags: int = betterproto.uint32_field(16)
    token_source: int = betterproto.uint32_field(22)
    admin_spoofing_user: bool = betterproto.bool_field(23)
    transport_error: int = betterproto.int32_field(17)
    messageid: int = betterproto.uint64_field(18)
    publisher_group_id: int = betterproto.uint32_field(19)
    sysid: int = betterproto.uint32_field(20)
    trace_tag: int = betterproto.uint64_field(21)
    webapi_key_id: int = betterproto.uint32_field(25)
    is_from_external_source: bool = betterproto.bool_field(26)
    forward_to_sysid: List[int] = betterproto.uint32_field(27)
    cm_sysid: int = betterproto.uint32_field(28)
    launcher_type: int = betterproto.uint32_field(31)
    realm: int = betterproto.uint32_field(32)
    timeout_ms: int = betterproto.int32_field(33)
    debug_source: str = betterproto.string_field(34)
    debug_source_string_index: int = betterproto.uint32_field(35)
    token_id: int = betterproto.uint64_field(36)
    routing_gc: "CMsgGCRoutingProtoBufHeader" = betterproto.message_field(37)
    session_disposition: "CMsgProtoBufHeaderESessionDisposition" = (
        betterproto.enum_field(38)
    )
    wg_token: str = betterproto.string_field(39)
    webui_auth_key: str = betterproto.string_field(40)
    ip: int = betterproto.uint32_field(15, group="ip_addr")
    ip_v6: bytes = betterproto.bytes_field(29, group="ip_addr")


@dataclass
class CMsgMulti(betterproto.Message):
    size_unzipped: int = betterproto.uint32_field(1)
    message_body: bytes = betterproto.bytes_field(2)


@dataclass
class CMsgProtobufWrapped(betterproto.Message):
    message_body: bytes = betterproto.bytes_field(1)


@dataclass
class CMsgAuthTicket(betterproto.Message):
    estate: int = betterproto.uint32_field(1)
    eresult: int = betterproto.uint32_field(2)
    steamid: float = betterproto.fixed64_field(3)
    gameid: float = betterproto.fixed64_field(4)
    h_steam_pipe: int = betterproto.uint32_field(5)
    ticket_crc: int = betterproto.uint32_field(6)
    ticket: bytes = betterproto.bytes_field(7)
    server_secret: bytes = betterproto.bytes_field(8)
    ticket_type: int = betterproto.uint32_field(9)


@dataclass
class CCDDBAppDetailCommon(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    name: str = betterproto.string_field(2)
    icon: str = betterproto.string_field(3)
    tool: bool = betterproto.bool_field(6)
    demo: bool = betterproto.bool_field(7)
    media: bool = betterproto.bool_field(8)
    community_visible_stats: bool = betterproto.bool_field(9)
    friendly_name: str = betterproto.string_field(10)
    propagation: str = betterproto.string_field(11)
    has_adult_content: bool = betterproto.bool_field(12)
    is_visible_in_steam_china: bool = betterproto.bool_field(13)
    app_type: int = betterproto.uint32_field(14)
    has_adult_content_sex: bool = betterproto.bool_field(15)
    has_adult_content_violence: bool = betterproto.bool_field(16)
    content_descriptorids: List[int] = betterproto.uint32_field(17)


@dataclass
class CMsgAppRights(betterproto.Message):
    edit_info: bool = betterproto.bool_field(1)
    publish: bool = betterproto.bool_field(2)
    view_error_data: bool = betterproto.bool_field(3)
    download: bool = betterproto.bool_field(4)
    upload_cdkeys: bool = betterproto.bool_field(5)
    generate_cdkeys: bool = betterproto.bool_field(6)
    view_financials: bool = betterproto.bool_field(7)
    manage_ceg: bool = betterproto.bool_field(8)
    manage_signing: bool = betterproto.bool_field(9)
    manage_cdkeys: bool = betterproto.bool_field(10)
    edit_marketing: bool = betterproto.bool_field(11)
    economy_support: bool = betterproto.bool_field(12)
    economy_support_supervisor: bool = betterproto.bool_field(13)
    manage_pricing: bool = betterproto.bool_field(14)
    broadcast_live: bool = betterproto.bool_field(15)
    view_marketing_traffic: bool = betterproto.bool_field(16)
    edit_store_display_content: bool = betterproto.bool_field(17)


@dataclass
class CCuratorPreferences(betterproto.Message):
    supported_languages: int = betterproto.uint32_field(1)
    platform_windows: bool = betterproto.bool_field(2)
    platform_mac: bool = betterproto.bool_field(3)
    platform_linux: bool = betterproto.bool_field(4)
    vr_content: bool = betterproto.bool_field(5)
    adult_content_violence: bool = betterproto.bool_field(6)
    adult_content_sex: bool = betterproto.bool_field(7)
    timestamp_updated: int = betterproto.uint32_field(8)
    tagids_curated: List[int] = betterproto.uint32_field(9)
    tagids_filtered: List[int] = betterproto.uint32_field(10)
    website_title: str = betterproto.string_field(11)
    website_url: str = betterproto.string_field(12)
    discussion_url: str = betterproto.string_field(13)
    show_broadcast: bool = betterproto.bool_field(14)


@dataclass
class CLocalizationToken(betterproto.Message):
    language: int = betterproto.uint32_field(1)
    localized_string: str = betterproto.string_field(2)


@dataclass
class CClanEventUserNewsTuple(betterproto.Message):
    clanid: int = betterproto.uint32_field(1)
    event_gid: float = betterproto.fixed64_field(2)
    announcement_gid: float = betterproto.fixed64_field(3)
    rtime_start: int = betterproto.uint32_field(4)
    rtime_end: int = betterproto.uint32_field(5)
    priority_score: int = betterproto.uint32_field(6)
    type: int = betterproto.uint32_field(7)
    clamp_range_slot: int = betterproto.uint32_field(8)
    appid: int = betterproto.uint32_field(9)
    rtime32_last_modified: int = betterproto.uint32_field(10)


@dataclass
class CClanMatchEventByRange(betterproto.Message):
    rtime_before: int = betterproto.uint32_field(1)
    rtime_after: int = betterproto.uint32_field(2)
    qualified: int = betterproto.uint32_field(3)
    events: List["CClanEventUserNewsTuple"] = betterproto.message_field(4)


@dataclass
class CCommunity_ClanAnnouncementInfo(betterproto.Message):
    gid: int = betterproto.uint64_field(1)
    clanid: int = betterproto.uint64_field(2)
    posterid: int = betterproto.uint64_field(3)
    headline: str = betterproto.string_field(4)
    posttime: int = betterproto.uint32_field(5)
    updatetime: int = betterproto.uint32_field(6)
    body: str = betterproto.string_field(7)
    commentcount: int = betterproto.int32_field(8)
    tags: List[str] = betterproto.string_field(9)
    language: int = betterproto.int32_field(10)
    hidden: bool = betterproto.bool_field(11)
    forum_topic_id: float = betterproto.fixed64_field(12)
    event_gid: float = betterproto.fixed64_field(13)
    voteupcount: int = betterproto.int32_field(14)
    votedowncount: int = betterproto.int32_field(15)
    ban_check_result: "EBanContentCheckResult" = betterproto.enum_field(16)
    banned: bool = betterproto.bool_field(17)


@dataclass
class CClanEventData(betterproto.Message):
    gid: float = betterproto.fixed64_field(1)
    clan_steamid: float = betterproto.fixed64_field(2)
    event_name: str = betterproto.string_field(3)
    event_type: "EProtoClanEventType" = betterproto.enum_field(4)
    appid: int = betterproto.uint32_field(5)
    server_address: str = betterproto.string_field(6)
    server_password: str = betterproto.string_field(7)
    rtime32_start_time: int = betterproto.uint32_field(8)
    rtime32_end_time: int = betterproto.uint32_field(9)
    comment_count: int = betterproto.int32_field(10)
    creator_steamid: float = betterproto.fixed64_field(11)
    last_update_steamid: float = betterproto.fixed64_field(12)
    event_notes: str = betterproto.string_field(13)
    jsondata: str = betterproto.string_field(14)
    announcement_body: "CCommunity_ClanAnnouncementInfo" = betterproto.message_field(15)
    published: bool = betterproto.bool_field(16)
    hidden: bool = betterproto.bool_field(17)
    rtime32_visibility_start: int = betterproto.uint32_field(18)
    rtime32_visibility_end: int = betterproto.uint32_field(19)
    broadcaster_accountid: int = betterproto.uint32_field(20)
    follower_count: int = betterproto.uint32_field(21)
    ignore_count: int = betterproto.uint32_field(22)
    forum_topic_id: float = betterproto.fixed64_field(23)
    rtime32_last_modified: int = betterproto.uint32_field(24)
    news_post_gid: float = betterproto.fixed64_field(25)
    rtime_mod_reviewed: int = betterproto.uint32_field(26)
    featured_app_tagid: int = betterproto.uint32_field(27)
    referenced_appids: List[int] = betterproto.uint32_field(28)
    build_id: int = betterproto.uint32_field(29)
    build_branch: str = betterproto.string_field(30)


@dataclass
class CBilling_Address(betterproto.Message):
    first_name: str = betterproto.string_field(1)
    last_name: str = betterproto.string_field(2)
    address1: str = betterproto.string_field(3)
    address2: str = betterproto.string_field(4)
    city: str = betterproto.string_field(5)
    us_state: str = betterproto.string_field(6)
    country_code: str = betterproto.string_field(7)
    postcode: str = betterproto.string_field(8)
    zip_plus4: int = betterproto.int32_field(9)
    phone: str = betterproto.string_field(10)


@dataclass
class CPackageReservationStatus(betterproto.Message):
    packageid: int = betterproto.uint32_field(1)
    reservation_state: int = betterproto.int32_field(2)
    queue_position: int = betterproto.int32_field(3)
    total_queue_size: int = betterproto.int32_field(4)
    reservation_country_code: str = betterproto.string_field(5)
    expired: bool = betterproto.bool_field(6)
    time_expires: int = betterproto.uint32_field(7)
    time_reserved: int = betterproto.uint32_field(8)


@dataclass
class CMsgKeyValuePair(betterproto.Message):
    name: str = betterproto.string_field(1)
    value: str = betterproto.string_field(2)


@dataclass
class CMsgKeyValueSet(betterproto.Message):
    pairs: List["CMsgKeyValuePair"] = betterproto.message_field(1)


@dataclass
class UserContentDescriptorPreferences(betterproto.Message):
    content_descriptors_to_exclude: List[
        "UserContentDescriptorPreferencesContentDescriptor"
    ] = betterproto.message_field(1)


@dataclass
class UserContentDescriptorPreferencesContentDescriptor(betterproto.Message):
    content_descriptorid: int = betterproto.uint32_field(1)
    timestamp_added: int = betterproto.uint32_field(2)
