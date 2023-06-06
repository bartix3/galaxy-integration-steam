# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: steammessages_clientserver.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import List

import betterproto


@dataclass
class CMsgClientRegisterAuthTicketWithCM(betterproto.Message):
    protocol_version: int = betterproto.uint32_field(1)
    ticket: bytes = betterproto.bytes_field(3)
    client_instance_id: int = betterproto.uint64_field(4)


@dataclass
class CMsgClientTicketAuthComplete(betterproto.Message):
    steam_id: float = betterproto.fixed64_field(1)
    game_id: float = betterproto.fixed64_field(2)
    estate: int = betterproto.uint32_field(3)
    eauth_session_response: int = betterproto.uint32_field(4)
    d_e_p_r_e_c_a_t_e_d_ticket: bytes = betterproto.bytes_field(5)
    ticket_crc: int = betterproto.uint32_field(6)
    ticket_sequence: int = betterproto.uint32_field(7)
    owner_steam_id: float = betterproto.fixed64_field(8)


@dataclass
class CMsgClientCMList(betterproto.Message):
    cm_addresses: List[int] = betterproto.uint32_field(1)
    cm_ports: List[int] = betterproto.uint32_field(2)
    cm_websocket_addresses: List[str] = betterproto.string_field(3)
    percent_default_to_websocket: int = betterproto.uint32_field(4)


@dataclass
class CMsgClientP2PConnectionInfo(betterproto.Message):
    steam_id_dest: float = betterproto.fixed64_field(1)
    steam_id_src: float = betterproto.fixed64_field(2)
    app_id: int = betterproto.uint32_field(3)
    candidate: bytes = betterproto.bytes_field(4)
    legacy_connection_id_src: float = betterproto.fixed64_field(5)
    rendezvous: bytes = betterproto.bytes_field(6)


@dataclass
class CMsgClientP2PConnectionFailInfo(betterproto.Message):
    steam_id_dest: float = betterproto.fixed64_field(1)
    steam_id_src: float = betterproto.fixed64_field(2)
    app_id: int = betterproto.uint32_field(3)
    ep2p_session_error: int = betterproto.uint32_field(4)
    connection_id_dest: float = betterproto.fixed64_field(5)
    close_reason: int = betterproto.uint32_field(7)
    close_message: str = betterproto.string_field(8)


@dataclass
class CMsgClientNetworkingCertRequest(betterproto.Message):
    key_data: bytes = betterproto.bytes_field(2)
    app_id: int = betterproto.uint32_field(3)


@dataclass
class CMsgClientNetworkingCertReply(betterproto.Message):
    cert: bytes = betterproto.bytes_field(4)
    ca_key_id: float = betterproto.fixed64_field(5)
    ca_signature: bytes = betterproto.bytes_field(6)


@dataclass
class CMsgClientNetworkingMobileCertRequest(betterproto.Message):
    app_id: int = betterproto.uint32_field(1)


@dataclass
class CMsgClientNetworkingMobileCertReply(betterproto.Message):
    encoded_cert: str = betterproto.string_field(1)


@dataclass
class CMsgClientGetAppOwnershipTicket(betterproto.Message):
    app_id: int = betterproto.uint32_field(1)


@dataclass
class CMsgClientGetAppOwnershipTicketResponse(betterproto.Message):
    eresult: int = betterproto.uint32_field(1)
    app_id: int = betterproto.uint32_field(2)
    ticket: bytes = betterproto.bytes_field(3)


@dataclass
class CMsgClientSessionToken(betterproto.Message):
    token: int = betterproto.uint64_field(1)


@dataclass
class CMsgClientGameConnectTokens(betterproto.Message):
    max_tokens_to_keep: int = betterproto.uint32_field(1)
    tokens: List[bytes] = betterproto.bytes_field(2)


@dataclass
class CMsgClientGamesPlayed(betterproto.Message):
    games_played: List["CMsgClientGamesPlayedGamePlayed"] = betterproto.message_field(1)
    client_os_type: int = betterproto.uint32_field(2)
    cloud_gaming_platform: int = betterproto.uint32_field(3)
    recent_reauthentication: bool = betterproto.bool_field(4)


@dataclass
class CMsgClientGamesPlayedProcessInfo(betterproto.Message):
    process_id: int = betterproto.uint32_field(1)
    process_id_parent: int = betterproto.uint32_field(2)
    parent_is_steam: bool = betterproto.bool_field(3)


@dataclass
class CMsgClientGamesPlayedGamePlayed(betterproto.Message):
    steam_id_gs: int = betterproto.uint64_field(1)
    game_id: float = betterproto.fixed64_field(2)
    deprecated_game_ip_address: int = betterproto.uint32_field(3)
    game_port: int = betterproto.uint32_field(4)
    is_secure: bool = betterproto.bool_field(5)
    token: bytes = betterproto.bytes_field(6)
    game_extra_info: str = betterproto.string_field(7)
    game_data_blob: bytes = betterproto.bytes_field(8)
    process_id: int = betterproto.uint32_field(9)
    streaming_provider_id: int = betterproto.uint32_field(10)
    game_flags: int = betterproto.uint32_field(11)
    owner_id: int = betterproto.uint32_field(12)
    vr_hmd_vendor: str = betterproto.string_field(13)
    vr_hmd_model: str = betterproto.string_field(14)
    launch_option_type: int = betterproto.uint32_field(15)
    primary_controller_type: int = betterproto.int32_field(16)
    primary_steam_controller_serial: str = betterproto.string_field(17)
    total_steam_controller_count: int = betterproto.uint32_field(18)
    total_non_steam_controller_count: int = betterproto.uint32_field(19)
    controller_workshop_file_id: int = betterproto.uint64_field(20)
    launch_source: int = betterproto.uint32_field(21)
    vr_hmd_runtime: int = betterproto.uint32_field(22)
    game_ip_address: "CMsgIPAddress" = betterproto.message_field(23)
    controller_connection_type: int = betterproto.uint32_field(24)
    game_os_platform: int = betterproto.int32_field(25)
    game_build_id: int = betterproto.uint32_field(26)
    compat_tool_id: int = betterproto.uint32_field(27)
    compat_tool_cmd: str = betterproto.string_field(28)
    compat_tool_build_id: int = betterproto.uint32_field(29)
    beta_name: str = betterproto.string_field(30)
    dlc_context: int = betterproto.uint32_field(31)
    process_id_list: List[
        "CMsgClientGamesPlayedProcessInfo"
    ] = betterproto.message_field(32)


@dataclass
class CMsgGSApprove(betterproto.Message):
    steam_id: float = betterproto.fixed64_field(1)
    owner_steam_id: float = betterproto.fixed64_field(2)


@dataclass
class CMsgGSDeny(betterproto.Message):
    steam_id: float = betterproto.fixed64_field(1)
    edeny_reason: int = betterproto.int32_field(2)
    deny_string: str = betterproto.string_field(3)


@dataclass
class CMsgGSKick(betterproto.Message):
    steam_id: float = betterproto.fixed64_field(1)
    edeny_reason: int = betterproto.int32_field(2)


@dataclass
class CMsgClientAuthList(betterproto.Message):
    tokens_left: int = betterproto.uint32_field(1)
    last_request_seq: int = betterproto.uint32_field(2)
    last_request_seq_from_server: int = betterproto.uint32_field(3)
    tickets: List["CMsgAuthTicket"] = betterproto.message_field(4)
    app_ids: List[int] = betterproto.uint32_field(5)
    message_sequence: int = betterproto.uint32_field(6)
    filtered: bool = betterproto.bool_field(7)


@dataclass
class CMsgClientAuthListAck(betterproto.Message):
    ticket_crc: List[int] = betterproto.uint32_field(1)
    app_ids: List[int] = betterproto.uint32_field(2)
    message_sequence: int = betterproto.uint32_field(3)


@dataclass
class CMsgClientLicenseList(betterproto.Message):
    eresult: int = betterproto.int32_field(1)
    licenses: List["CMsgClientLicenseListLicense"] = betterproto.message_field(2)


@dataclass
class CMsgClientLicenseListLicense(betterproto.Message):
    package_id: int = betterproto.uint32_field(1)
    time_created: float = betterproto.fixed32_field(2)
    time_next_process: float = betterproto.fixed32_field(3)
    minute_limit: int = betterproto.int32_field(4)
    minutes_used: int = betterproto.int32_field(5)
    payment_method: int = betterproto.uint32_field(6)
    flags: int = betterproto.uint32_field(7)
    purchase_country_code: str = betterproto.string_field(8)
    license_type: int = betterproto.uint32_field(9)
    territory_code: int = betterproto.int32_field(10)
    change_number: int = betterproto.int32_field(11)
    owner_id: int = betterproto.uint32_field(12)
    initial_period: int = betterproto.uint32_field(13)
    initial_time_unit: int = betterproto.uint32_field(14)
    renewal_period: int = betterproto.uint32_field(15)
    renewal_time_unit: int = betterproto.uint32_field(16)
    access_token: int = betterproto.uint64_field(17)
    master_package_id: int = betterproto.uint32_field(18)


@dataclass
class CMsgClientIsLimitedAccount(betterproto.Message):
    bis_limited_account: bool = betterproto.bool_field(1)
    bis_community_banned: bool = betterproto.bool_field(2)
    bis_locked_account: bool = betterproto.bool_field(3)
    bis_limited_account_allowed_to_invite_friends: bool = betterproto.bool_field(4)


@dataclass
class CMsgClientRequestedClientStats(betterproto.Message):
    stats_to_send: List[
        "CMsgClientRequestedClientStatsStatsToSend"
    ] = betterproto.message_field(1)


@dataclass
class CMsgClientRequestedClientStatsStatsToSend(betterproto.Message):
    client_stat: int = betterproto.uint32_field(1)
    stat_aggregate_method: int = betterproto.uint32_field(2)


@dataclass
class CMsgClientStat2(betterproto.Message):
    stat_detail: List["CMsgClientStat2StatDetail"] = betterproto.message_field(1)


@dataclass
class CMsgClientStat2StatDetail(betterproto.Message):
    client_stat: int = betterproto.uint32_field(1)
    ll_value: int = betterproto.int64_field(2)
    time_of_day: int = betterproto.uint32_field(3)
    cell_id: int = betterproto.uint32_field(4)
    depot_id: int = betterproto.uint32_field(5)
    app_id: int = betterproto.uint32_field(6)


@dataclass
class CMsgClientInviteToGame(betterproto.Message):
    steam_id_dest: float = betterproto.fixed64_field(1)
    steam_id_src: float = betterproto.fixed64_field(2)
    connect_string: str = betterproto.string_field(3)
    remote_play: str = betterproto.string_field(4)


@dataclass
class CMsgClientChatInvite(betterproto.Message):
    steam_id_invited: float = betterproto.fixed64_field(1)
    steam_id_chat: float = betterproto.fixed64_field(2)
    steam_id_patron: float = betterproto.fixed64_field(3)
    chatroom_type: int = betterproto.int32_field(4)
    steam_id_friend_chat: float = betterproto.fixed64_field(5)
    chat_name: str = betterproto.string_field(6)
    game_id: float = betterproto.fixed64_field(7)


@dataclass
class CMsgClientConnectionStats(betterproto.Message):
    stats_logon: "CMsgClientConnectionStatsStats_Logon" = betterproto.message_field(1)
    stats_vconn: "CMsgClientConnectionStatsStats_VConn" = betterproto.message_field(2)


@dataclass
class CMsgClientConnectionStatsStats_Logon(betterproto.Message):
    connect_attempts: int = betterproto.int32_field(1)
    connect_successes: int = betterproto.int32_field(2)
    connect_failures: int = betterproto.int32_field(3)
    connections_dropped: int = betterproto.int32_field(4)
    seconds_running: int = betterproto.uint32_field(5)
    msec_tologonthistime: int = betterproto.uint32_field(6)
    count_bad_cms: int = betterproto.uint32_field(7)
    no_udp_connectivity: bool = betterproto.bool_field(8)
    no_tcp_connectivity: bool = betterproto.bool_field(9)
    no_websocket_443_connectivity: bool = betterproto.bool_field(10)
    no_websocket_non_443_connectivity: bool = betterproto.bool_field(11)


@dataclass
class CMsgClientConnectionStatsStats_UDP(betterproto.Message):
    pkts_sent: int = betterproto.uint64_field(1)
    bytes_sent: int = betterproto.uint64_field(2)
    pkts_recv: int = betterproto.uint64_field(3)
    pkts_processed: int = betterproto.uint64_field(4)
    bytes_recv: int = betterproto.uint64_field(5)


@dataclass
class CMsgClientConnectionStatsStats_VConn(betterproto.Message):
    connections_udp: int = betterproto.uint32_field(1)
    connections_tcp: int = betterproto.uint32_field(2)
    stats_udp: "CMsgClientConnectionStatsStats_UDP" = betterproto.message_field(3)
    pkts_abandoned: int = betterproto.uint64_field(4)
    conn_req_received: int = betterproto.uint64_field(5)
    pkts_resent: int = betterproto.uint64_field(6)
    msgs_sent: int = betterproto.uint64_field(7)
    msgs_sent_failed: int = betterproto.uint64_field(8)
    msgs_recv: int = betterproto.uint64_field(9)
    datagrams_sent: int = betterproto.uint64_field(10)
    datagrams_recv: int = betterproto.uint64_field(11)
    bad_pkts_recv: int = betterproto.uint64_field(12)
    unknown_conn_pkts_recv: int = betterproto.uint64_field(13)
    missed_pkts_recv: int = betterproto.uint64_field(14)
    dup_pkts_recv: int = betterproto.uint64_field(15)
    failed_connect_challenges: int = betterproto.uint64_field(16)
    micro_sec_avg_latency: int = betterproto.uint32_field(17)
    micro_sec_min_latency: int = betterproto.uint32_field(18)
    micro_sec_max_latency: int = betterproto.uint32_field(19)


@dataclass
class CMsgClientServersAvailable(betterproto.Message):
    server_types_available: List[
        "CMsgClientServersAvailableServer_Types_Available"
    ] = betterproto.message_field(1)
    server_type_for_auth_services: int = betterproto.uint32_field(2)


@dataclass
class CMsgClientServersAvailableServer_Types_Available(betterproto.Message):
    server: int = betterproto.uint32_field(1)
    changed: bool = betterproto.bool_field(2)


@dataclass
class CMsgClientReportOverlayDetourFailure(betterproto.Message):
    failure_strings: List[str] = betterproto.string_field(1)


@dataclass
class CMsgClientRequestEncryptedAppTicket(betterproto.Message):
    app_id: int = betterproto.uint32_field(1)
    userdata: bytes = betterproto.bytes_field(2)


@dataclass
class CMsgClientRequestEncryptedAppTicketResponse(betterproto.Message):
    app_id: int = betterproto.uint32_field(1)
    eresult: int = betterproto.int32_field(2)
    encrypted_app_ticket: "EncryptedAppTicket" = betterproto.message_field(3)


@dataclass
class CMsgClientWalletInfoUpdate(betterproto.Message):
    has_wallet: bool = betterproto.bool_field(1)
    balance: int = betterproto.int32_field(2)
    currency: int = betterproto.int32_field(3)
    balance_delayed: int = betterproto.int32_field(4)
    balance64: int = betterproto.int64_field(5)
    balance64_delayed: int = betterproto.int64_field(6)
    realm: int = betterproto.int32_field(7)


@dataclass
class CMsgClientAMGetClanOfficers(betterproto.Message):
    steamid_clan: float = betterproto.fixed64_field(1)


@dataclass
class CMsgClientAMGetClanOfficersResponse(betterproto.Message):
    eresult: int = betterproto.int32_field(1)
    steamid_clan: float = betterproto.fixed64_field(2)
    officer_count: int = betterproto.int32_field(3)


@dataclass
class CMsgClientAMGetPersonaNameHistory(betterproto.Message):
    id_count: int = betterproto.int32_field(1)
    ids: List[
        "CMsgClientAMGetPersonaNameHistoryIdInstance"
    ] = betterproto.message_field(2)


@dataclass
class CMsgClientAMGetPersonaNameHistoryIdInstance(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)


@dataclass
class CMsgClientAMGetPersonaNameHistoryResponse(betterproto.Message):
    responses: List[
        "CMsgClientAMGetPersonaNameHistoryResponseNameTableInstance"
    ] = betterproto.message_field(2)


@dataclass
class CMsgClientAMGetPersonaNameHistoryResponseNameTableInstance(betterproto.Message):
    eresult: int = betterproto.int32_field(1)
    steamid: float = betterproto.fixed64_field(2)
    names: List[
        "CMsgClientAMGetPersonaNameHistoryResponseNameTableInstanceNameInstance"
    ] = betterproto.message_field(3)


@dataclass
class CMsgClientAMGetPersonaNameHistoryResponseNameTableInstanceNameInstance(
    betterproto.Message
):
    name_since: float = betterproto.fixed32_field(1)
    name: str = betterproto.string_field(2)


@dataclass
class CMsgClientDeregisterWithServer(betterproto.Message):
    eservertype: int = betterproto.uint32_field(1)
    app_id: int = betterproto.uint32_field(2)


@dataclass
class CMsgClientClanState(betterproto.Message):
    steamid_clan: float = betterproto.fixed64_field(1)
    clan_account_flags: int = betterproto.uint32_field(3)
    name_info: "CMsgClientClanStateNameInfo" = betterproto.message_field(4)
    user_counts: "CMsgClientClanStateUserCounts" = betterproto.message_field(5)
    events: List["CMsgClientClanStateEvent"] = betterproto.message_field(6)
    announcements: List["CMsgClientClanStateEvent"] = betterproto.message_field(7)
    chat_room_private: bool = betterproto.bool_field(8)


@dataclass
class CMsgClientClanStateNameInfo(betterproto.Message):
    clan_name: str = betterproto.string_field(1)
    sha_avatar: bytes = betterproto.bytes_field(2)


@dataclass
class CMsgClientClanStateUserCounts(betterproto.Message):
    members: int = betterproto.uint32_field(1)
    online: int = betterproto.uint32_field(2)
    chatting: int = betterproto.uint32_field(3)
    in_game: int = betterproto.uint32_field(4)
    chat_room_members: int = betterproto.uint32_field(5)


@dataclass
class CMsgClientClanStateEvent(betterproto.Message):
    gid: float = betterproto.fixed64_field(1)
    event_time: int = betterproto.uint32_field(2)
    headline: str = betterproto.string_field(3)
    game_id: float = betterproto.fixed64_field(4)
    just_posted: bool = betterproto.bool_field(5)
