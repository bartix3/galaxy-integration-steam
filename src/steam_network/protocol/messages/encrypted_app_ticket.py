# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: encrypted_app_ticket.proto
# plugin: python-betterproto
from dataclasses import dataclass

import betterproto


@dataclass
class EncryptedAppTicket(betterproto.Message):
    ticket_version_no: int = betterproto.uint32_field(1)
    crc_encryptedticket: int = betterproto.uint32_field(2)
    cb_encrypteduserdata: int = betterproto.uint32_field(3)
    cb_encrypted_appownershipticket: int = betterproto.uint32_field(4)
    encrypted_ticket: bytes = betterproto.bytes_field(5)