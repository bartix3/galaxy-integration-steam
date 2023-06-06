# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: steammessages_auth.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import List

import betterproto


class EAuthTokenPlatformType(betterproto.Enum):
    k_EAuthTokenPlatformType_Unknown = 0
    k_EAuthTokenPlatformType_SteamClient = 1
    k_EAuthTokenPlatformType_WebBrowser = 2
    k_EAuthTokenPlatformType_MobileApp = 3


class EAuthSessionGuardType(betterproto.Enum):
    k_EAuthSessionGuardType_Unknown = 0
    k_EAuthSessionGuardType_None = 1
    k_EAuthSessionGuardType_EmailCode = 2
    k_EAuthSessionGuardType_DeviceCode = 3
    k_EAuthSessionGuardType_DeviceConfirmation = 4
    k_EAuthSessionGuardType_EmailConfirmation = 5
    k_EAuthSessionGuardType_MachineToken = 6
    k_EAuthSessionGuardType_LegacyMachineAuth = 7


class EAuthSessionSecurityHistory(betterproto.Enum):
    k_EAuthSessionSecurityHistory_Invalid = 0
    k_EAuthSessionSecurityHistory_UsedPreviously = 1
    k_EAuthSessionSecurityHistory_NoPriorHistory = 2


class ETokenRenewalType(betterproto.Enum):
    k_ETokenRenewalType_None = 0
    k_ETokenRenewalType_Allow = 1


class EAuthTokenRevokeAction(betterproto.Enum):
    k_EAuthTokenRevokeLogout = 0
    k_EAuthTokenRevokePermanent = 1
    k_EAuthTokenRevokeReplaced = 2
    k_EAuthTokenRevokeSupport = 3
    k_EAuthTokenRevokeConsume = 4
    k_EAuthTokenRevokeNonRememberedLogout = 5
    k_EAuthTokenRevokeNonRememberedPermanent = 6
    k_EAuthTokenRevokeAutomatic = 7


class EAuthTokenState(betterproto.Enum):
    k_EAuthTokenState_Invalid = 0
    k_EAuthTokenState_New = 1
    k_EAuthTokenState_Confirmed = 2
    k_EAuthTokenState_Issued = 3
    k_EAuthTokenState_Denied = 4
    k_EAuthTokenState_LoggedOut = 5
    k_EAuthTokenState_Consumed = 6
    k_EAuthTokenState_Revoked = 99


@dataclass
class CAuthentication_GetPasswordRSAPublicKey_Request(betterproto.Message):
    account_name: str = betterproto.string_field(1)


@dataclass
class CAuthentication_GetPasswordRSAPublicKey_Response(betterproto.Message):
    publickey_mod: str = betterproto.string_field(1)
    publickey_exp: str = betterproto.string_field(2)
    timestamp: int = betterproto.uint64_field(3)


@dataclass
class CAuthentication_DeviceDetails(betterproto.Message):
    device_friendly_name: str = betterproto.string_field(1)
    platform_type: "EAuthTokenPlatformType" = betterproto.enum_field(2)
    os_type: int = betterproto.int32_field(3)
    gaming_device_type: int = betterproto.uint32_field(4)
    client_count: int = betterproto.uint32_field(5)
    machine_id: bytes = betterproto.bytes_field(6)


@dataclass
class CAuthentication_BeginAuthSessionViaQR_Request(betterproto.Message):
    device_friendly_name: str = betterproto.string_field(1)
    platform_type: "EAuthTokenPlatformType" = betterproto.enum_field(2)
    device_details: "CAuthentication_DeviceDetails" = betterproto.message_field(3)
    website_id: str = betterproto.string_field(4)


@dataclass
class CAuthentication_AllowedConfirmation(betterproto.Message):
    confirmation_type: "EAuthSessionGuardType" = betterproto.enum_field(1)
    associated_message: str = betterproto.string_field(2)


@dataclass
class CAuthentication_BeginAuthSessionViaQR_Response(betterproto.Message):
    client_id: int = betterproto.uint64_field(1)
    challenge_url: str = betterproto.string_field(2)
    request_id: bytes = betterproto.bytes_field(3)
    interval: float = betterproto.float_field(4)
    allowed_confirmations: List[
        "CAuthentication_AllowedConfirmation"
    ] = betterproto.message_field(5)
    version: int = betterproto.int32_field(6)


@dataclass
class CAuthentication_BeginAuthSessionViaCredentials_Request(betterproto.Message):
    device_friendly_name: str = betterproto.string_field(1)
    account_name: str = betterproto.string_field(2)
    encrypted_password: str = betterproto.string_field(3)
    encryption_timestamp: int = betterproto.uint64_field(4)
    remember_login: bool = betterproto.bool_field(5)
    platform_type: "EAuthTokenPlatformType" = betterproto.enum_field(6)
    persistence: "ESessionPersistence" = betterproto.enum_field(7)
    website_id: str = betterproto.string_field(8)
    device_details: "CAuthentication_DeviceDetails" = betterproto.message_field(9)
    guard_data: str = betterproto.string_field(10)
    language: int = betterproto.uint32_field(11)
    qos_level: int = betterproto.int32_field(12)


@dataclass
class CAuthentication_BeginAuthSessionViaCredentials_Response(betterproto.Message):
    client_id: int = betterproto.uint64_field(1)
    request_id: bytes = betterproto.bytes_field(2)
    interval: float = betterproto.float_field(3)
    allowed_confirmations: List[
        "CAuthentication_AllowedConfirmation"
    ] = betterproto.message_field(4)
    steamid: int = betterproto.uint64_field(5)
    weak_token: str = betterproto.string_field(6)
    agreement_session_url: str = betterproto.string_field(7)
    extended_error_message: str = betterproto.string_field(8)


@dataclass
class CAuthentication_PollAuthSessionStatus_Request(betterproto.Message):
    client_id: int = betterproto.uint64_field(1)
    request_id: bytes = betterproto.bytes_field(2)
    token_to_revoke: float = betterproto.fixed64_field(3)


@dataclass
class CAuthentication_PollAuthSessionStatus_Response(betterproto.Message):
    new_client_id: int = betterproto.uint64_field(1)
    new_challenge_url: str = betterproto.string_field(2)
    refresh_token: str = betterproto.string_field(3)
    access_token: str = betterproto.string_field(4)
    had_remote_interaction: bool = betterproto.bool_field(5)
    account_name: str = betterproto.string_field(6)
    new_guard_data: str = betterproto.string_field(7)
    agreement_session_url: str = betterproto.string_field(8)


@dataclass
class CAuthentication_GetAuthSessionInfo_Request(betterproto.Message):
    client_id: int = betterproto.uint64_field(1)


@dataclass
class CAuthentication_GetAuthSessionInfo_Response(betterproto.Message):
    ip: str = betterproto.string_field(1)
    geoloc: str = betterproto.string_field(2)
    city: str = betterproto.string_field(3)
    state: str = betterproto.string_field(4)
    country: str = betterproto.string_field(5)
    platform_type: "EAuthTokenPlatformType" = betterproto.enum_field(6)
    device_friendly_name: str = betterproto.string_field(7)
    version: int = betterproto.int32_field(8)
    login_history: "EAuthSessionSecurityHistory" = betterproto.enum_field(9)
    requestor_location_mismatch: bool = betterproto.bool_field(10)
    high_usage_login: bool = betterproto.bool_field(11)
    requested_persistence: "ESessionPersistence" = betterproto.enum_field(12)


@dataclass
class CAuthentication_UpdateAuthSessionWithMobileConfirmation_Request(
    betterproto.Message
):
    version: int = betterproto.int32_field(1)
    client_id: int = betterproto.uint64_field(2)
    steamid: float = betterproto.fixed64_field(3)
    signature: bytes = betterproto.bytes_field(4)
    confirm: bool = betterproto.bool_field(5)
    persistence: "ESessionPersistence" = betterproto.enum_field(6)


@dataclass
class CAuthentication_UpdateAuthSessionWithMobileConfirmation_Response(
    betterproto.Message
):
    pass


@dataclass
class CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request(betterproto.Message):
    client_id: int = betterproto.uint64_field(1)
    steamid: float = betterproto.fixed64_field(2)
    code: str = betterproto.string_field(3)
    code_type: "EAuthSessionGuardType" = betterproto.enum_field(4)


@dataclass
class CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response(betterproto.Message):
    agreement_session_url: str = betterproto.string_field(7)


@dataclass
class CAuthentication_AccessToken_GenerateForApp_Request(betterproto.Message):
    refresh_token: str = betterproto.string_field(1)
    steamid: float = betterproto.fixed64_field(2)
    renewal_type: "ETokenRenewalType" = betterproto.enum_field(3)


@dataclass
class CAuthentication_AccessToken_GenerateForApp_Response(betterproto.Message):
    access_token: str = betterproto.string_field(1)
    refresh_token: str = betterproto.string_field(2)


@dataclass
class CAuthentication_RefreshToken_Enumerate_Request(betterproto.Message):
    pass


@dataclass
class CAuthentication_RefreshToken_Enumerate_Response(betterproto.Message):
    refresh_tokens: List[
        "CAuthentication_RefreshToken_Enumerate_ResponseRefreshTokenDescription"
    ] = betterproto.message_field(1)
    requesting_token: float = betterproto.fixed64_field(2)


@dataclass
class CAuthentication_RefreshToken_Enumerate_ResponseTokenUsageEvent(
    betterproto.Message
):
    time: int = betterproto.uint32_field(1)
    ip: "CMsgIPAddress" = betterproto.message_field(2)
    locale: str = betterproto.string_field(3)
    country: str = betterproto.string_field(4)
    state: str = betterproto.string_field(5)
    city: str = betterproto.string_field(6)


@dataclass
class CAuthentication_RefreshToken_Enumerate_ResponseRefreshTokenDescription(
    betterproto.Message
):
    token_id: float = betterproto.fixed64_field(1)
    token_description: str = betterproto.string_field(2)
    time_updated: int = betterproto.uint32_field(3)
    platform_type: "EAuthTokenPlatformType" = betterproto.enum_field(4)
    logged_in: bool = betterproto.bool_field(5)
    os_platform: int = betterproto.uint32_field(6)
    auth_type: int = betterproto.uint32_field(7)
    gaming_device_type: int = betterproto.uint32_field(8)
    first_seen: "CAuthentication_RefreshToken_Enumerate_ResponseTokenUsageEvent" = (
        betterproto.message_field(9)
    )
    last_seen: "CAuthentication_RefreshToken_Enumerate_ResponseTokenUsageEvent" = (
        betterproto.message_field(10)
    )
    os_type: int = betterproto.int32_field(11)


@dataclass
class CAuthentication_GetAuthSessionsForAccount_Request(betterproto.Message):
    pass


@dataclass
class CAuthentication_GetAuthSessionsForAccount_Response(betterproto.Message):
    client_ids: List[int] = betterproto.uint64_field(1)


@dataclass
class CAuthentication_MigrateMobileSession_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    token: str = betterproto.string_field(2)
    signature: str = betterproto.string_field(3)


@dataclass
class CAuthentication_MigrateMobileSession_Response(betterproto.Message):
    refresh_token: str = betterproto.string_field(1)
    access_token: str = betterproto.string_field(2)


@dataclass
class CAuthentication_Token_Revoke_Request(betterproto.Message):
    token: str = betterproto.string_field(1)
    revoke_action: "EAuthTokenRevokeAction" = betterproto.enum_field(2)


@dataclass
class CAuthentication_Token_Revoke_Response(betterproto.Message):
    pass


@dataclass
class CAuthentication_RefreshToken_Revoke_Request(betterproto.Message):
    token_id: float = betterproto.fixed64_field(1)
    steamid: float = betterproto.fixed64_field(2)
    revoke_action: "EAuthTokenRevokeAction" = betterproto.enum_field(3)
    signature: bytes = betterproto.bytes_field(4)


@dataclass
class CAuthentication_RefreshToken_Revoke_Response(betterproto.Message):
    pass


@dataclass
class CAuthenticationSupport_QueryRefreshTokensByAccount_Request(betterproto.Message):
    steamid: float = betterproto.fixed64_field(1)
    include_revoked_tokens: bool = betterproto.bool_field(2)


@dataclass
class CSupportRefreshTokenDescription(betterproto.Message):
    token_id: float = betterproto.fixed64_field(1)
    token_description: str = betterproto.string_field(2)
    time_updated: int = betterproto.uint32_field(3)
    platform_type: "EAuthTokenPlatformType" = betterproto.enum_field(4)
    token_state: "EAuthTokenState" = betterproto.enum_field(5)
    owner_steamid: float = betterproto.fixed64_field(6)
    os_platform: int = betterproto.uint32_field(7)
    os_type: int = betterproto.int32_field(8)
    auth_type: int = betterproto.uint32_field(9)
    gaming_device_type: int = betterproto.uint32_field(10)
    first_seen: "CSupportRefreshTokenDescriptionTokenUsageEvent" = (
        betterproto.message_field(11)
    )
    last_seen: "CSupportRefreshTokenDescriptionTokenUsageEvent" = (
        betterproto.message_field(12)
    )


@dataclass
class CSupportRefreshTokenDescriptionTokenUsageEvent(betterproto.Message):
    time: int = betterproto.uint32_field(1)
    ip: "CMsgIPAddress" = betterproto.message_field(2)
    country: str = betterproto.string_field(3)
    state: str = betterproto.string_field(4)
    city: str = betterproto.string_field(5)


@dataclass
class CAuthenticationSupport_QueryRefreshTokensByAccount_Response(betterproto.Message):
    refresh_tokens: List["CSupportRefreshTokenDescription"] = betterproto.message_field(
        1
    )
    last_token_reset: int = betterproto.int32_field(2)


@dataclass
class CAuthenticationSupport_QueryRefreshTokenByID_Request(betterproto.Message):
    token_id: float = betterproto.fixed64_field(1)


@dataclass
class CAuthenticationSupport_QueryRefreshTokenByID_Response(betterproto.Message):
    refresh_tokens: List["CSupportRefreshTokenDescription"] = betterproto.message_field(
        1
    )


@dataclass
class CAuthenticationSupport_RevokeToken_Request(betterproto.Message):
    token_id: float = betterproto.fixed64_field(1)
    steamid: float = betterproto.fixed64_field(2)


@dataclass
class CAuthenticationSupport_RevokeToken_Response(betterproto.Message):
    pass


@dataclass
class CAuthenticationSupport_GetTokenHistory_Request(betterproto.Message):
    token_id: float = betterproto.fixed64_field(1)


@dataclass
class CSupportRefreshTokenAudit(betterproto.Message):
    action: int = betterproto.int32_field(1)
    time: int = betterproto.uint32_field(2)
    ip: "CMsgIPAddress" = betterproto.message_field(3)
    actor: float = betterproto.fixed64_field(4)


@dataclass
class CAuthenticationSupport_GetTokenHistory_Response(betterproto.Message):
    history: List["CSupportRefreshTokenAudit"] = betterproto.message_field(1)


@dataclass
class CCloudGaming_CreateNonce_Request(betterproto.Message):
    platform: str = betterproto.string_field(1)
    appid: int = betterproto.uint32_field(2)


@dataclass
class CCloudGaming_CreateNonce_Response(betterproto.Message):
    nonce: str = betterproto.string_field(1)
    expiry: int = betterproto.uint32_field(2)


@dataclass
class CCloudGaming_GetTimeRemaining_Request(betterproto.Message):
    platform: str = betterproto.string_field(1)
    appid_list: List[int] = betterproto.uint32_field(2)


@dataclass
class CCloudGaming_TimeRemaining(betterproto.Message):
    appid: int = betterproto.uint32_field(1)
    minutes_remaining: int = betterproto.uint32_field(2)


@dataclass
class CCloudGaming_GetTimeRemaining_Response(betterproto.Message):
    entries: List["CCloudGaming_TimeRemaining"] = betterproto.message_field(2)
