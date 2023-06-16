# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: steammessages_clientserver_friends.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import steammessages_base_pb2 as steammessages__base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(steammessages_clientserver_friends.proto\x1a\x18steammessages_base.proto\"\x8a\x01\n\x13\x43MsgClientFriendMsg\x12\x0f\n\x07steamid\x18\x01 \x01(\x06\x12\x17\n\x0f\x63hat_entry_type\x18\x02 \x01(\x05\x12\x0f\n\x07message\x18\x03 \x01(\x0c\x12 \n\x18rtime32_server_timestamp\x18\x04 \x01(\x07\x12\x16\n\x0e\x65\x63ho_to_sender\x18\x05 \x01(\x08\"\x9d\x01\n\x1b\x43MsgClientFriendMsgIncoming\x12\x14\n\x0csteamid_from\x18\x01 \x01(\x06\x12\x17\n\x0f\x63hat_entry_type\x18\x02 \x01(\x05\x12\x1c\n\x14\x66rom_limited_account\x18\x03 \x01(\x08\x12\x0f\n\x07message\x18\x04 \x01(\x0c\x12 \n\x18rtime32_server_timestamp\x18\x05 \x01(\x07\"R\n\x13\x43MsgClientAddFriend\x12\x16\n\x0esteamid_to_add\x18\x01 \x01(\x06\x12#\n\x1b\x61\x63\x63ountname_or_email_to_add\x18\x02 \x01(\t\"e\n\x1b\x43MsgClientAddFriendResponse\x12\x12\n\x07\x65result\x18\x01 \x01(\x05:\x01\x32\x12\x16\n\x0esteam_id_added\x18\x02 \x01(\x06\x12\x1a\n\x12persona_name_added\x18\x03 \x01(\t\"*\n\x16\x43MsgClientRemoveFriend\x12\x10\n\x08\x66riendid\x18\x01 \x01(\x06\"6\n\x14\x43MsgClientHideFriend\x12\x10\n\x08\x66riendid\x18\x01 \x01(\x06\x12\x0c\n\x04hide\x18\x02 \x01(\x08\"\xea\x01\n\x15\x43MsgClientFriendsList\x12\x14\n\x0c\x62incremental\x18\x01 \x01(\x08\x12.\n\x07\x66riends\x18\x02 \x03(\x0b\x32\x1d.CMsgClientFriendsList.Friend\x12\x18\n\x10max_friend_count\x18\x03 \x01(\r\x12\x1b\n\x13\x61\x63tive_friend_count\x18\x04 \x01(\r\x12\x19\n\x11\x66riends_limit_hit\x18\x05 \x01(\x08\x1a\x39\n\x06\x46riend\x12\x12\n\nulfriendid\x18\x01 \x01(\x06\x12\x1b\n\x13\x65\x66riendrelationship\x18\x02 \x01(\r\"\xc5\x02\n\x1b\x43MsgClientFriendsGroupsList\x12\x10\n\x08\x62removal\x18\x01 \x01(\x08\x12\x14\n\x0c\x62incremental\x18\x02 \x01(\x08\x12>\n\x0c\x66riendGroups\x18\x03 \x03(\x0b\x32(.CMsgClientFriendsGroupsList.FriendGroup\x12H\n\x0bmemberships\x18\x04 \x03(\x0b\x32\x33.CMsgClientFriendsGroupsList.FriendGroupsMembership\x1a\x35\n\x0b\x46riendGroup\x12\x10\n\x08nGroupID\x18\x01 \x01(\x05\x12\x14\n\x0cstrGroupName\x18\x02 \x01(\t\x1a=\n\x16\x46riendGroupsMembership\x12\x11\n\tulSteamID\x18\x01 \x01(\x06\x12\x10\n\x08nGroupID\x18\x02 \x01(\x05\"\xba\x01\n\x1c\x43MsgClientPlayerNicknameList\x12\x0f\n\x07removal\x18\x01 \x01(\x08\x12\x13\n\x0bincremental\x18\x02 \x01(\x08\x12?\n\tnicknames\x18\x03 \x03(\x0b\x32,.CMsgClientPlayerNicknameList.PlayerNickname\x1a\x33\n\x0ePlayerNickname\x12\x0f\n\x07steamid\x18\x01 \x01(\x06\x12\x10\n\x08nickname\x18\x03 \x01(\t\"@\n\x1b\x43MsgClientSetPlayerNickname\x12\x0f\n\x07steamid\x18\x01 \x01(\x06\x12\x10\n\x08nickname\x18\x02 \x01(\t\"6\n#CMsgClientSetPlayerNicknameResponse\x12\x0f\n\x07\x65result\x18\x01 \x01(\r\"O\n\x1b\x43MsgClientRequestFriendData\x12\x1f\n\x17persona_state_requested\x18\x01 \x01(\r\x12\x0f\n\x07\x66riends\x18\x02 \x03(\x06\"\xef\x01\n\x16\x43MsgClientChangeStatus\x12\x15\n\rpersona_state\x18\x01 \x01(\r\x12\x13\n\x0bplayer_name\x18\x02 \x01(\t\x12\x1e\n\x16is_auto_generated_name\x18\x03 \x01(\x08\x12\x15\n\rhigh_priority\x18\x04 \x01(\x08\x12\x1b\n\x13persona_set_by_user\x18\x05 \x01(\x08\x12\x1e\n\x13persona_state_flags\x18\x06 \x01(\r:\x01\x30\x12\x1d\n\x15need_persona_response\x18\x07 \x01(\x08\x12\x16\n\x0eis_client_idle\x18\x08 \x01(\x08\"@\n\x19\x43MsgPersonaChangeResponse\x12\x0e\n\x06result\x18\x01 \x01(\r\x12\x13\n\x0bplayer_name\x18\x02 \x01(\t\"\xa0\x08\n\x16\x43MsgClientPersonaState\x12\x14\n\x0cstatus_flags\x18\x01 \x01(\r\x12/\n\x07\x66riends\x18\x02 \x03(\x0b\x32\x1e.CMsgClientPersonaState.Friend\x1a\xbe\x07\n\x06\x46riend\x12\x10\n\x08\x66riendid\x18\x01 \x01(\x06\x12\x15\n\rpersona_state\x18\x02 \x01(\r\x12\x1a\n\x12game_played_app_id\x18\x03 \x01(\r\x12\x16\n\x0egame_server_ip\x18\x04 \x01(\r\x12\x18\n\x10game_server_port\x18\x05 \x01(\r\x12\x1b\n\x13persona_state_flags\x18\x06 \x01(\r\x12 \n\x18online_session_instances\x18\x07 \x01(\r\x12\x1b\n\x13persona_set_by_user\x18\n \x01(\x08\x12\x13\n\x0bplayer_name\x18\x0f \x01(\t\x12\x12\n\nquery_port\x18\x14 \x01(\r\x12\x16\n\x0esteamid_source\x18\x19 \x01(\x06\x12\x13\n\x0b\x61vatar_hash\x18\x1f \x01(\x0c\x12\x13\n\x0blast_logoff\x18- \x01(\r\x12\x12\n\nlast_logon\x18. \x01(\r\x12\x18\n\x10last_seen_online\x18/ \x01(\r\x12\x11\n\tclan_rank\x18\x32 \x01(\r\x12\x11\n\tgame_name\x18\x37 \x01(\t\x12\x0e\n\x06gameid\x18\x38 \x01(\x06\x12\x16\n\x0egame_data_blob\x18< \x01(\x0c\x12:\n\tclan_data\x18@ \x01(\x0b\x32\'.CMsgClientPersonaState.Friend.ClanData\x12\x10\n\x08\x63lan_tag\x18\x41 \x01(\t\x12\x38\n\rrich_presence\x18G \x03(\x0b\x32!.CMsgClientPersonaState.Friend.KV\x12\x14\n\x0c\x62roadcast_id\x18H \x01(\x06\x12\x15\n\rgame_lobby_id\x18I \x01(\x06\x12$\n\x1cwatching_broadcast_accountid\x18J \x01(\r\x12 \n\x18watching_broadcast_appid\x18K \x01(\r\x12\"\n\x1awatching_broadcast_viewers\x18L \x01(\r\x12 \n\x18watching_broadcast_title\x18M \x01(\t\x12\x1b\n\x13is_community_banned\x18N \x01(\x08\x12\"\n\x1aplayer_name_pending_review\x18O \x01(\x08\x12\x1d\n\x15\x61vatar_pending_review\x18P \x01(\x08\x1a\x35\n\x08\x43lanData\x12\x12\n\nogg_app_id\x18\x01 \x01(\r\x12\x15\n\rchat_group_id\x18\x02 \x01(\x04\x1a \n\x02KV\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\"5\n\x1b\x43MsgClientFriendProfileInfo\x12\x16\n\x0esteamid_friend\x18\x01 \x01(\x06\"\xda\x01\n#CMsgClientFriendProfileInfoResponse\x12\x12\n\x07\x65result\x18\x01 \x01(\x05:\x01\x32\x12\x16\n\x0esteamid_friend\x18\x02 \x01(\x06\x12\x14\n\x0ctime_created\x18\x03 \x01(\r\x12\x11\n\treal_name\x18\x04 \x01(\t\x12\x11\n\tcity_name\x18\x05 \x01(\t\x12\x12\n\nstate_name\x18\x06 \x01(\t\x12\x14\n\x0c\x63ountry_name\x18\x07 \x01(\t\x12\x10\n\x08headline\x18\x08 \x01(\t\x12\x0f\n\x07summary\x18\t \x01(\t\"[\n\x1c\x43MsgClientCreateFriendsGroup\x12\x0f\n\x07steamid\x18\x01 \x01(\x06\x12\x11\n\tgroupname\x18\x02 \x01(\t\x12\x17\n\x0fsteamid_friends\x18\x03 \x03(\x06\"H\n$CMsgClientCreateFriendsGroupResponse\x12\x0f\n\x07\x65result\x18\x01 \x01(\r\x12\x0f\n\x07groupid\x18\x02 \x01(\x05\"@\n\x1c\x43MsgClientDeleteFriendsGroup\x12\x0f\n\x07steamid\x18\x01 \x01(\x06\x12\x0f\n\x07groupid\x18\x02 \x01(\x05\"7\n$CMsgClientDeleteFriendsGroupResponse\x12\x0f\n\x07\x65result\x18\x01 \x01(\r\"\x82\x01\n\x1c\x43MsgClientManageFriendsGroup\x12\x0f\n\x07groupid\x18\x01 \x01(\x05\x12\x11\n\tgroupname\x18\x02 \x01(\t\x12\x1d\n\x15steamid_friends_added\x18\x03 \x03(\x06\x12\x1f\n\x17steamid_friends_removed\x18\x04 \x03(\x06\"7\n$CMsgClientManageFriendsGroupResponse\x12\x0f\n\x07\x65result\x18\x01 \x01(\r\"B\n\x1a\x43MsgClientAddFriendToGroup\x12\x0f\n\x07groupid\x18\x01 \x01(\x05\x12\x13\n\x0bsteamiduser\x18\x02 \x01(\x06\"5\n\"CMsgClientAddFriendToGroupResponse\x12\x0f\n\x07\x65result\x18\x01 \x01(\r\"G\n\x1f\x43MsgClientRemoveFriendFromGroup\x12\x0f\n\x07groupid\x18\x01 \x01(\x05\x12\x13\n\x0bsteamiduser\x18\x02 \x01(\x06\":\n\'CMsgClientRemoveFriendFromGroupResponse\x12\x0f\n\x07\x65result\x18\x01 \x01(\r\"\x1b\n\x19\x43MsgClientGetEmoticonList\"\x87\x04\n\x16\x43MsgClientEmoticonList\x12\x33\n\temoticons\x18\x01 \x03(\x0b\x32 .CMsgClientEmoticonList.Emoticon\x12\x31\n\x08stickers\x18\x02 \x03(\x0b\x32\x1f.CMsgClientEmoticonList.Sticker\x12/\n\x07\x65\x66\x66\x65\x63ts\x18\x03 \x03(\x0b\x32\x1e.CMsgClientEmoticonList.Effect\x1ax\n\x08\x45moticon\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\x12\x16\n\x0etime_last_used\x18\x03 \x01(\r\x12\x11\n\tuse_count\x18\x04 \x01(\r\x12\x15\n\rtime_received\x18\x05 \x01(\r\x12\r\n\x05\x61ppid\x18\x06 \x01(\r\x1aw\n\x07Sticker\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\x12\x15\n\rtime_received\x18\x03 \x01(\r\x12\r\n\x05\x61ppid\x18\x04 \x01(\r\x12\x16\n\x0etime_last_used\x18\x05 \x01(\r\x12\x11\n\tuse_count\x18\x06 \x01(\r\x1a\x61\n\x06\x45\x66\x66\x65\x63t\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\x12\x15\n\rtime_received\x18\x03 \x01(\r\x12\x14\n\x0cinfinite_use\x18\x04 \x01(\x08\x12\r\n\x05\x61ppid\x18\x05 \x01(\rB\x05H\x01\x90\x01\x00')



_CMSGCLIENTFRIENDMSG = DESCRIPTOR.message_types_by_name['CMsgClientFriendMsg']
_CMSGCLIENTFRIENDMSGINCOMING = DESCRIPTOR.message_types_by_name['CMsgClientFriendMsgIncoming']
_CMSGCLIENTADDFRIEND = DESCRIPTOR.message_types_by_name['CMsgClientAddFriend']
_CMSGCLIENTADDFRIENDRESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientAddFriendResponse']
_CMSGCLIENTREMOVEFRIEND = DESCRIPTOR.message_types_by_name['CMsgClientRemoveFriend']
_CMSGCLIENTHIDEFRIEND = DESCRIPTOR.message_types_by_name['CMsgClientHideFriend']
_CMSGCLIENTFRIENDSLIST = DESCRIPTOR.message_types_by_name['CMsgClientFriendsList']
_CMSGCLIENTFRIENDSLIST_FRIEND = _CMSGCLIENTFRIENDSLIST.nested_types_by_name['Friend']
_CMSGCLIENTFRIENDSGROUPSLIST = DESCRIPTOR.message_types_by_name['CMsgClientFriendsGroupsList']
_CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUP = _CMSGCLIENTFRIENDSGROUPSLIST.nested_types_by_name['FriendGroup']
_CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUPSMEMBERSHIP = _CMSGCLIENTFRIENDSGROUPSLIST.nested_types_by_name['FriendGroupsMembership']
_CMSGCLIENTPLAYERNICKNAMELIST = DESCRIPTOR.message_types_by_name['CMsgClientPlayerNicknameList']
_CMSGCLIENTPLAYERNICKNAMELIST_PLAYERNICKNAME = _CMSGCLIENTPLAYERNICKNAMELIST.nested_types_by_name['PlayerNickname']
_CMSGCLIENTSETPLAYERNICKNAME = DESCRIPTOR.message_types_by_name['CMsgClientSetPlayerNickname']
_CMSGCLIENTSETPLAYERNICKNAMERESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientSetPlayerNicknameResponse']
_CMSGCLIENTREQUESTFRIENDDATA = DESCRIPTOR.message_types_by_name['CMsgClientRequestFriendData']
_CMSGCLIENTCHANGESTATUS = DESCRIPTOR.message_types_by_name['CMsgClientChangeStatus']
_CMSGPERSONACHANGERESPONSE = DESCRIPTOR.message_types_by_name['CMsgPersonaChangeResponse']
_CMSGCLIENTPERSONASTATE = DESCRIPTOR.message_types_by_name['CMsgClientPersonaState']
_CMSGCLIENTPERSONASTATE_FRIEND = _CMSGCLIENTPERSONASTATE.nested_types_by_name['Friend']
_CMSGCLIENTPERSONASTATE_FRIEND_CLANDATA = _CMSGCLIENTPERSONASTATE_FRIEND.nested_types_by_name['ClanData']
_CMSGCLIENTPERSONASTATE_FRIEND_KV = _CMSGCLIENTPERSONASTATE_FRIEND.nested_types_by_name['KV']
_CMSGCLIENTFRIENDPROFILEINFO = DESCRIPTOR.message_types_by_name['CMsgClientFriendProfileInfo']
_CMSGCLIENTFRIENDPROFILEINFORESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientFriendProfileInfoResponse']
_CMSGCLIENTCREATEFRIENDSGROUP = DESCRIPTOR.message_types_by_name['CMsgClientCreateFriendsGroup']
_CMSGCLIENTCREATEFRIENDSGROUPRESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientCreateFriendsGroupResponse']
_CMSGCLIENTDELETEFRIENDSGROUP = DESCRIPTOR.message_types_by_name['CMsgClientDeleteFriendsGroup']
_CMSGCLIENTDELETEFRIENDSGROUPRESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientDeleteFriendsGroupResponse']
_CMSGCLIENTMANAGEFRIENDSGROUP = DESCRIPTOR.message_types_by_name['CMsgClientManageFriendsGroup']
_CMSGCLIENTMANAGEFRIENDSGROUPRESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientManageFriendsGroupResponse']
_CMSGCLIENTADDFRIENDTOGROUP = DESCRIPTOR.message_types_by_name['CMsgClientAddFriendToGroup']
_CMSGCLIENTADDFRIENDTOGROUPRESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientAddFriendToGroupResponse']
_CMSGCLIENTREMOVEFRIENDFROMGROUP = DESCRIPTOR.message_types_by_name['CMsgClientRemoveFriendFromGroup']
_CMSGCLIENTREMOVEFRIENDFROMGROUPRESPONSE = DESCRIPTOR.message_types_by_name['CMsgClientRemoveFriendFromGroupResponse']
_CMSGCLIENTGETEMOTICONLIST = DESCRIPTOR.message_types_by_name['CMsgClientGetEmoticonList']
_CMSGCLIENTEMOTICONLIST = DESCRIPTOR.message_types_by_name['CMsgClientEmoticonList']
_CMSGCLIENTEMOTICONLIST_EMOTICON = _CMSGCLIENTEMOTICONLIST.nested_types_by_name['Emoticon']
_CMSGCLIENTEMOTICONLIST_STICKER = _CMSGCLIENTEMOTICONLIST.nested_types_by_name['Sticker']
_CMSGCLIENTEMOTICONLIST_EFFECT = _CMSGCLIENTEMOTICONLIST.nested_types_by_name['Effect']
CMsgClientFriendMsg = _reflection.GeneratedProtocolMessageType('CMsgClientFriendMsg', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTFRIENDMSG,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientFriendMsg)
  })
_sym_db.RegisterMessage(CMsgClientFriendMsg)

CMsgClientFriendMsgIncoming = _reflection.GeneratedProtocolMessageType('CMsgClientFriendMsgIncoming', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTFRIENDMSGINCOMING,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientFriendMsgIncoming)
  })
_sym_db.RegisterMessage(CMsgClientFriendMsgIncoming)

CMsgClientAddFriend = _reflection.GeneratedProtocolMessageType('CMsgClientAddFriend', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTADDFRIEND,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientAddFriend)
  })
_sym_db.RegisterMessage(CMsgClientAddFriend)

CMsgClientAddFriendResponse = _reflection.GeneratedProtocolMessageType('CMsgClientAddFriendResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTADDFRIENDRESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientAddFriendResponse)
  })
_sym_db.RegisterMessage(CMsgClientAddFriendResponse)

CMsgClientRemoveFriend = _reflection.GeneratedProtocolMessageType('CMsgClientRemoveFriend', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTREMOVEFRIEND,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientRemoveFriend)
  })
_sym_db.RegisterMessage(CMsgClientRemoveFriend)

CMsgClientHideFriend = _reflection.GeneratedProtocolMessageType('CMsgClientHideFriend', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTHIDEFRIEND,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientHideFriend)
  })
_sym_db.RegisterMessage(CMsgClientHideFriend)

CMsgClientFriendsList = _reflection.GeneratedProtocolMessageType('CMsgClientFriendsList', (_message.Message,), {

  'Friend' : _reflection.GeneratedProtocolMessageType('Friend', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTFRIENDSLIST_FRIEND,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientFriendsList.Friend)
    })
  ,
  'DESCRIPTOR' : _CMSGCLIENTFRIENDSLIST,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientFriendsList)
  })
_sym_db.RegisterMessage(CMsgClientFriendsList)
_sym_db.RegisterMessage(CMsgClientFriendsList.Friend)

CMsgClientFriendsGroupsList = _reflection.GeneratedProtocolMessageType('CMsgClientFriendsGroupsList', (_message.Message,), {

  'FriendGroup' : _reflection.GeneratedProtocolMessageType('FriendGroup', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUP,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientFriendsGroupsList.FriendGroup)
    })
  ,

  'FriendGroupsMembership' : _reflection.GeneratedProtocolMessageType('FriendGroupsMembership', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUPSMEMBERSHIP,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientFriendsGroupsList.FriendGroupsMembership)
    })
  ,
  'DESCRIPTOR' : _CMSGCLIENTFRIENDSGROUPSLIST,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientFriendsGroupsList)
  })
_sym_db.RegisterMessage(CMsgClientFriendsGroupsList)
_sym_db.RegisterMessage(CMsgClientFriendsGroupsList.FriendGroup)
_sym_db.RegisterMessage(CMsgClientFriendsGroupsList.FriendGroupsMembership)

CMsgClientPlayerNicknameList = _reflection.GeneratedProtocolMessageType('CMsgClientPlayerNicknameList', (_message.Message,), {

  'PlayerNickname' : _reflection.GeneratedProtocolMessageType('PlayerNickname', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTPLAYERNICKNAMELIST_PLAYERNICKNAME,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientPlayerNicknameList.PlayerNickname)
    })
  ,
  'DESCRIPTOR' : _CMSGCLIENTPLAYERNICKNAMELIST,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientPlayerNicknameList)
  })
_sym_db.RegisterMessage(CMsgClientPlayerNicknameList)
_sym_db.RegisterMessage(CMsgClientPlayerNicknameList.PlayerNickname)

CMsgClientSetPlayerNickname = _reflection.GeneratedProtocolMessageType('CMsgClientSetPlayerNickname', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTSETPLAYERNICKNAME,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientSetPlayerNickname)
  })
_sym_db.RegisterMessage(CMsgClientSetPlayerNickname)

CMsgClientSetPlayerNicknameResponse = _reflection.GeneratedProtocolMessageType('CMsgClientSetPlayerNicknameResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTSETPLAYERNICKNAMERESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientSetPlayerNicknameResponse)
  })
_sym_db.RegisterMessage(CMsgClientSetPlayerNicknameResponse)

CMsgClientRequestFriendData = _reflection.GeneratedProtocolMessageType('CMsgClientRequestFriendData', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTREQUESTFRIENDDATA,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientRequestFriendData)
  })
_sym_db.RegisterMessage(CMsgClientRequestFriendData)

CMsgClientChangeStatus = _reflection.GeneratedProtocolMessageType('CMsgClientChangeStatus', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTCHANGESTATUS,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientChangeStatus)
  })
_sym_db.RegisterMessage(CMsgClientChangeStatus)

CMsgPersonaChangeResponse = _reflection.GeneratedProtocolMessageType('CMsgPersonaChangeResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGPERSONACHANGERESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgPersonaChangeResponse)
  })
_sym_db.RegisterMessage(CMsgPersonaChangeResponse)

CMsgClientPersonaState = _reflection.GeneratedProtocolMessageType('CMsgClientPersonaState', (_message.Message,), {

  'Friend' : _reflection.GeneratedProtocolMessageType('Friend', (_message.Message,), {

    'ClanData' : _reflection.GeneratedProtocolMessageType('ClanData', (_message.Message,), {
      'DESCRIPTOR' : _CMSGCLIENTPERSONASTATE_FRIEND_CLANDATA,
      '__module__' : 'steammessages_clientserver_friends_pb2'
      # @@protoc_insertion_point(class_scope:CMsgClientPersonaState.Friend.ClanData)
      })
    ,

    'KV' : _reflection.GeneratedProtocolMessageType('KV', (_message.Message,), {
      'DESCRIPTOR' : _CMSGCLIENTPERSONASTATE_FRIEND_KV,
      '__module__' : 'steammessages_clientserver_friends_pb2'
      # @@protoc_insertion_point(class_scope:CMsgClientPersonaState.Friend.KV)
      })
    ,
    'DESCRIPTOR' : _CMSGCLIENTPERSONASTATE_FRIEND,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientPersonaState.Friend)
    })
  ,
  'DESCRIPTOR' : _CMSGCLIENTPERSONASTATE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientPersonaState)
  })
_sym_db.RegisterMessage(CMsgClientPersonaState)
_sym_db.RegisterMessage(CMsgClientPersonaState.Friend)
_sym_db.RegisterMessage(CMsgClientPersonaState.Friend.ClanData)
_sym_db.RegisterMessage(CMsgClientPersonaState.Friend.KV)

CMsgClientFriendProfileInfo = _reflection.GeneratedProtocolMessageType('CMsgClientFriendProfileInfo', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTFRIENDPROFILEINFO,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientFriendProfileInfo)
  })
_sym_db.RegisterMessage(CMsgClientFriendProfileInfo)

CMsgClientFriendProfileInfoResponse = _reflection.GeneratedProtocolMessageType('CMsgClientFriendProfileInfoResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTFRIENDPROFILEINFORESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientFriendProfileInfoResponse)
  })
_sym_db.RegisterMessage(CMsgClientFriendProfileInfoResponse)

CMsgClientCreateFriendsGroup = _reflection.GeneratedProtocolMessageType('CMsgClientCreateFriendsGroup', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTCREATEFRIENDSGROUP,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientCreateFriendsGroup)
  })
_sym_db.RegisterMessage(CMsgClientCreateFriendsGroup)

CMsgClientCreateFriendsGroupResponse = _reflection.GeneratedProtocolMessageType('CMsgClientCreateFriendsGroupResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTCREATEFRIENDSGROUPRESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientCreateFriendsGroupResponse)
  })
_sym_db.RegisterMessage(CMsgClientCreateFriendsGroupResponse)

CMsgClientDeleteFriendsGroup = _reflection.GeneratedProtocolMessageType('CMsgClientDeleteFriendsGroup', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTDELETEFRIENDSGROUP,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientDeleteFriendsGroup)
  })
_sym_db.RegisterMessage(CMsgClientDeleteFriendsGroup)

CMsgClientDeleteFriendsGroupResponse = _reflection.GeneratedProtocolMessageType('CMsgClientDeleteFriendsGroupResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTDELETEFRIENDSGROUPRESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientDeleteFriendsGroupResponse)
  })
_sym_db.RegisterMessage(CMsgClientDeleteFriendsGroupResponse)

CMsgClientManageFriendsGroup = _reflection.GeneratedProtocolMessageType('CMsgClientManageFriendsGroup', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTMANAGEFRIENDSGROUP,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientManageFriendsGroup)
  })
_sym_db.RegisterMessage(CMsgClientManageFriendsGroup)

CMsgClientManageFriendsGroupResponse = _reflection.GeneratedProtocolMessageType('CMsgClientManageFriendsGroupResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTMANAGEFRIENDSGROUPRESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientManageFriendsGroupResponse)
  })
_sym_db.RegisterMessage(CMsgClientManageFriendsGroupResponse)

CMsgClientAddFriendToGroup = _reflection.GeneratedProtocolMessageType('CMsgClientAddFriendToGroup', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTADDFRIENDTOGROUP,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientAddFriendToGroup)
  })
_sym_db.RegisterMessage(CMsgClientAddFriendToGroup)

CMsgClientAddFriendToGroupResponse = _reflection.GeneratedProtocolMessageType('CMsgClientAddFriendToGroupResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTADDFRIENDTOGROUPRESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientAddFriendToGroupResponse)
  })
_sym_db.RegisterMessage(CMsgClientAddFriendToGroupResponse)

CMsgClientRemoveFriendFromGroup = _reflection.GeneratedProtocolMessageType('CMsgClientRemoveFriendFromGroup', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTREMOVEFRIENDFROMGROUP,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientRemoveFriendFromGroup)
  })
_sym_db.RegisterMessage(CMsgClientRemoveFriendFromGroup)

CMsgClientRemoveFriendFromGroupResponse = _reflection.GeneratedProtocolMessageType('CMsgClientRemoveFriendFromGroupResponse', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTREMOVEFRIENDFROMGROUPRESPONSE,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientRemoveFriendFromGroupResponse)
  })
_sym_db.RegisterMessage(CMsgClientRemoveFriendFromGroupResponse)

CMsgClientGetEmoticonList = _reflection.GeneratedProtocolMessageType('CMsgClientGetEmoticonList', (_message.Message,), {
  'DESCRIPTOR' : _CMSGCLIENTGETEMOTICONLIST,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientGetEmoticonList)
  })
_sym_db.RegisterMessage(CMsgClientGetEmoticonList)

CMsgClientEmoticonList = _reflection.GeneratedProtocolMessageType('CMsgClientEmoticonList', (_message.Message,), {

  'Emoticon' : _reflection.GeneratedProtocolMessageType('Emoticon', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTEMOTICONLIST_EMOTICON,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientEmoticonList.Emoticon)
    })
  ,

  'Sticker' : _reflection.GeneratedProtocolMessageType('Sticker', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTEMOTICONLIST_STICKER,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientEmoticonList.Sticker)
    })
  ,

  'Effect' : _reflection.GeneratedProtocolMessageType('Effect', (_message.Message,), {
    'DESCRIPTOR' : _CMSGCLIENTEMOTICONLIST_EFFECT,
    '__module__' : 'steammessages_clientserver_friends_pb2'
    # @@protoc_insertion_point(class_scope:CMsgClientEmoticonList.Effect)
    })
  ,
  'DESCRIPTOR' : _CMSGCLIENTEMOTICONLIST,
  '__module__' : 'steammessages_clientserver_friends_pb2'
  # @@protoc_insertion_point(class_scope:CMsgClientEmoticonList)
  })
_sym_db.RegisterMessage(CMsgClientEmoticonList)
_sym_db.RegisterMessage(CMsgClientEmoticonList.Emoticon)
_sym_db.RegisterMessage(CMsgClientEmoticonList.Sticker)
_sym_db.RegisterMessage(CMsgClientEmoticonList.Effect)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'H\001\220\001\000'
  _CMSGCLIENTFRIENDMSG._serialized_start=71
  _CMSGCLIENTFRIENDMSG._serialized_end=209
  _CMSGCLIENTFRIENDMSGINCOMING._serialized_start=212
  _CMSGCLIENTFRIENDMSGINCOMING._serialized_end=369
  _CMSGCLIENTADDFRIEND._serialized_start=371
  _CMSGCLIENTADDFRIEND._serialized_end=453
  _CMSGCLIENTADDFRIENDRESPONSE._serialized_start=455
  _CMSGCLIENTADDFRIENDRESPONSE._serialized_end=556
  _CMSGCLIENTREMOVEFRIEND._serialized_start=558
  _CMSGCLIENTREMOVEFRIEND._serialized_end=600
  _CMSGCLIENTHIDEFRIEND._serialized_start=602
  _CMSGCLIENTHIDEFRIEND._serialized_end=656
  _CMSGCLIENTFRIENDSLIST._serialized_start=659
  _CMSGCLIENTFRIENDSLIST._serialized_end=893
  _CMSGCLIENTFRIENDSLIST_FRIEND._serialized_start=836
  _CMSGCLIENTFRIENDSLIST_FRIEND._serialized_end=893
  _CMSGCLIENTFRIENDSGROUPSLIST._serialized_start=896
  _CMSGCLIENTFRIENDSGROUPSLIST._serialized_end=1221
  _CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUP._serialized_start=1105
  _CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUP._serialized_end=1158
  _CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUPSMEMBERSHIP._serialized_start=1160
  _CMSGCLIENTFRIENDSGROUPSLIST_FRIENDGROUPSMEMBERSHIP._serialized_end=1221
  _CMSGCLIENTPLAYERNICKNAMELIST._serialized_start=1224
  _CMSGCLIENTPLAYERNICKNAMELIST._serialized_end=1410
  _CMSGCLIENTPLAYERNICKNAMELIST_PLAYERNICKNAME._serialized_start=1359
  _CMSGCLIENTPLAYERNICKNAMELIST_PLAYERNICKNAME._serialized_end=1410
  _CMSGCLIENTSETPLAYERNICKNAME._serialized_start=1412
  _CMSGCLIENTSETPLAYERNICKNAME._serialized_end=1476
  _CMSGCLIENTSETPLAYERNICKNAMERESPONSE._serialized_start=1478
  _CMSGCLIENTSETPLAYERNICKNAMERESPONSE._serialized_end=1532
  _CMSGCLIENTREQUESTFRIENDDATA._serialized_start=1534
  _CMSGCLIENTREQUESTFRIENDDATA._serialized_end=1613
  _CMSGCLIENTCHANGESTATUS._serialized_start=1616
  _CMSGCLIENTCHANGESTATUS._serialized_end=1855
  _CMSGPERSONACHANGERESPONSE._serialized_start=1857
  _CMSGPERSONACHANGERESPONSE._serialized_end=1921
  _CMSGCLIENTPERSONASTATE._serialized_start=1924
  _CMSGCLIENTPERSONASTATE._serialized_end=2980
  _CMSGCLIENTPERSONASTATE_FRIEND._serialized_start=2022
  _CMSGCLIENTPERSONASTATE_FRIEND._serialized_end=2980
  _CMSGCLIENTPERSONASTATE_FRIEND_CLANDATA._serialized_start=2893
  _CMSGCLIENTPERSONASTATE_FRIEND_CLANDATA._serialized_end=2946
  _CMSGCLIENTPERSONASTATE_FRIEND_KV._serialized_start=2948
  _CMSGCLIENTPERSONASTATE_FRIEND_KV._serialized_end=2980
  _CMSGCLIENTFRIENDPROFILEINFO._serialized_start=2982
  _CMSGCLIENTFRIENDPROFILEINFO._serialized_end=3035
  _CMSGCLIENTFRIENDPROFILEINFORESPONSE._serialized_start=3038
  _CMSGCLIENTFRIENDPROFILEINFORESPONSE._serialized_end=3256
  _CMSGCLIENTCREATEFRIENDSGROUP._serialized_start=3258
  _CMSGCLIENTCREATEFRIENDSGROUP._serialized_end=3349
  _CMSGCLIENTCREATEFRIENDSGROUPRESPONSE._serialized_start=3351
  _CMSGCLIENTCREATEFRIENDSGROUPRESPONSE._serialized_end=3423
  _CMSGCLIENTDELETEFRIENDSGROUP._serialized_start=3425
  _CMSGCLIENTDELETEFRIENDSGROUP._serialized_end=3489
  _CMSGCLIENTDELETEFRIENDSGROUPRESPONSE._serialized_start=3491
  _CMSGCLIENTDELETEFRIENDSGROUPRESPONSE._serialized_end=3546
  _CMSGCLIENTMANAGEFRIENDSGROUP._serialized_start=3549
  _CMSGCLIENTMANAGEFRIENDSGROUP._serialized_end=3679
  _CMSGCLIENTMANAGEFRIENDSGROUPRESPONSE._serialized_start=3681
  _CMSGCLIENTMANAGEFRIENDSGROUPRESPONSE._serialized_end=3736
  _CMSGCLIENTADDFRIENDTOGROUP._serialized_start=3738
  _CMSGCLIENTADDFRIENDTOGROUP._serialized_end=3804
  _CMSGCLIENTADDFRIENDTOGROUPRESPONSE._serialized_start=3806
  _CMSGCLIENTADDFRIENDTOGROUPRESPONSE._serialized_end=3859
  _CMSGCLIENTREMOVEFRIENDFROMGROUP._serialized_start=3861
  _CMSGCLIENTREMOVEFRIENDFROMGROUP._serialized_end=3932
  _CMSGCLIENTREMOVEFRIENDFROMGROUPRESPONSE._serialized_start=3934
  _CMSGCLIENTREMOVEFRIENDFROMGROUPRESPONSE._serialized_end=3992
  _CMSGCLIENTGETEMOTICONLIST._serialized_start=3994
  _CMSGCLIENTGETEMOTICONLIST._serialized_end=4021
  _CMSGCLIENTEMOTICONLIST._serialized_start=4024
  _CMSGCLIENTEMOTICONLIST._serialized_end=4543
  _CMSGCLIENTEMOTICONLIST_EMOTICON._serialized_start=4203
  _CMSGCLIENTEMOTICONLIST_EMOTICON._serialized_end=4323
  _CMSGCLIENTEMOTICONLIST_STICKER._serialized_start=4325
  _CMSGCLIENTEMOTICONLIST_STICKER._serialized_end=4444
  _CMSGCLIENTEMOTICONLIST_EFFECT._serialized_start=4446
  _CMSGCLIENTEMOTICONLIST_EFFECT._serialized_end=4543
# @@protoc_insertion_point(module_scope)