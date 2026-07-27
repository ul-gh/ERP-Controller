#!/usr/bin/env python3
"""UDS Connector.

UDS Diagnostic API Component for Linux Userspace.

See documentation in README.md.

License: GPL v3
"""
import sys
import time
from typing import TYPE_CHECKING

import isotp
import udsoncan
import udsoncan.configs
from udsoncan.exceptions import (
    InvalidResponseException,
    NegativeResponseException,
    #TimeoutException,
    #UnexpectedResponseException,
)
from udsoncan.services.ReadDataByIdentifier import ReadDataByIdentifier

from uds_connector.did_codecs import Fixed16Codec, Fixed8Codec
from uds_connector.python_iso_tp_client import PythonIsoTpClient

if TYPE_CHECKING:
    from udsoncan.typing import ClientConfig

# Transport protocol IDs for the EVC unit
# In case of transport over 11-bit CAN, this is identical to the CAN IDs.
TP_ID_EVC_REQUEST = 0x7E4
TP_ID_EVC_RESPONSE = 0x7EC

# Data identifier to test. Reads a hex string.
DID = int(sys.argv[1], 16)


def print_response(response) -> None:
    hex_str: str = ":".join(f"{xx:02x}" for xx in response.data)
    print(
        f"Received number of bytes: {len(response.data)}\n",
        "Raw Response Data:\n",
        f"DID_RAW: {hex_str}\n",
        "Last two bytes Interpreted as integer:\n",
        f"DID_LAST_INT_16: {int.from_bytes(response.data[-2:], byteorder="big")}\n",
        "Last byte Interpreted as integer:\n",
        f"DID_LAST_INT_8: {int.from_bytes(response.data[-1:])}\n",
    )


def main() -> None:
    """Request the specified DIDs from ECU via UDS and publish the results."""

    dids_requested: list[int] = [
        DID,
    ]

    tp_address = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        #isotp.AddressingMode.Extended_29bits,
        # txid=0x7DF,7E0,7E4 and rxid=0x7E8,7EC are good candidates
        txid=TP_ID_EVC_REQUEST,
        rxid=TP_ID_EVC_RESPONSE,
    )

    client_config: ClientConfig = udsoncan.configs.default_client_config.copy()
    client_config["data_identifiers"] = {
        DID: RawCodec(),
    }

    with PythonIsoTpClient(tp_address, client_config) as client:
        try:
            print("Sending request to read Data Identifier: ...")
            # Read Data By Identifier (Service 0x22).
            #response = client.read_data_by_identifier(dids_requested)  # pyright: ignore[reportArgumentType, reportUnknownVariableType]
            response = client.test_data_identifier(dids_requested)
            print_response(response)
        except NegativeResponseException as e:
            print(
                "ECU rejected the request with code:",
                f"{e.response.code_name} (0x{e.response.code:02X})",
            )
        except InvalidResponseException as e:
            print(f"Received an invalid or malformed response: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
