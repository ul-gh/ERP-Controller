#!/usr/bin/env python3
"""UDS Connector.

UDS Diagnostic API Component for Linux Userspace.

See documentation in README.md.

License: GPL v3
"""
import sys
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
from udsoncan.Response import Response
from udsoncan.services.TesterPresent import TesterPresent

from uds_connector.did_codecs import RawCodec
from uds_connector.python_iso_tp_client import PythonIsoTpClient

if TYPE_CHECKING:
    from udsoncan.typing import ClientConfig


if len(sys.argv) < 2:
    print("Usage: test_did [TP_ID_REQUEST TP_ID_RESPONSE] DID\n"
        + "This reads hex numbers only.\n")
    sys.exit()
elif len(sys.argv) == 2:
    # Transport protocol IDs for the EVC unit
    # In case of transport over 11-bit CAN, this is identical to the CAN IDs.
    TP_ID_EVC_REQUEST = 0x7DF
    TP_ID_EVC_RESPONSE = 0x7EC
    # Data identifier to test. Reads a hex string.
    DID = int(sys.argv[1], 16)
elif len(sys.argv) == 4:
    # Transport protocol IDs for the EVC unit
    # In case of transport over 11-bit CAN, this is identical to the CAN IDs.
    TP_ID_EVC_REQUEST = int(sys.argv[1], 16)  # pyright: ignore[reportConstantRedefinition]
    TP_ID_EVC_RESPONSE = int(sys.argv[2], 16)  # pyright: ignore[reportConstantRedefinition]
    # Data identifier to test. Reads a hex string.
    DID = int(sys.argv[3], 16)  # pyright: ignore[reportConstantRedefinition]



def print_response(response: Response | None) -> None:
    """Print the response data in a human-readable format."""
    if response is None:
        print("No response received.")
        return
    data = response.data
    if data is None:
        print("Response data is None.")
        return
    did_str: str = ":".join(f"{xx:02x}" for xx in data[0:2])
    data_str: str = ":".join(f"{xx:02x}" for xx in data[2:])
    print(
        f"Received number of bytes: {len(data)}\n",
        "Raw Response Data (First two bytes should be the request ID):\n",
        f"DID_HEX: [{did_str}] | DATA: [{data_str}]\n",
        "Data Interpreted as integer:\n",
        f"DID_INT: {int.from_bytes(data[2:])}\n",
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
            tester_present = TesterPresent().make_request()
            _ = client.send_request(tester_present)
            print("Sending request to read Data Identifier: ...")
            # Read Data By Identifier (Service 0x22).
            #response = client.read_data_by_identifier(dids_requested)
            response = client.test_data_identifier(dids_requested)  # pyright: ignore[reportUnknownVariableType, reportArgumentType]
            print_response(response)  # pyright: ignore[reportUnknownArgumentType]
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
