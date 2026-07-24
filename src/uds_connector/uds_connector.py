#!/usr/bin/env python3
"""UDS Connector.

UDS Diagnostic API Component for Linux Userspace.

See documentation in README.md.

License: GPL v3
"""

import can
import isotp
import udsoncan
import udsoncan.configs
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.exceptions import (
    InvalidResponseException,
    NegativeResponseException,
    #TimeoutException,
    #UnexpectedResponseException,
)
from udsoncan.services.ReadDataByIdentifier import ReadDataByIdentifier

from uds_connector.did_codecs import Fixed16Codec

# HV Voltage
DID_V_HV = 0x3203
# Battery Current
DID_I_BATT = 0x3204
# SOC
DID_SOC = 0x2002

def print_response(response: ReadDataByIdentifier.InterpretedResponse) -> None:
    """Print requested values from response object."""
    # Extract Values
    values = response.service_data.values
    v_hv = values[DID_V_HV]  # pyright: ignore[reportAny]
    i_batt = values[DID_I_BATT] # pyright: ignore[reportAny]
    soc = values[DID_SOC] # pyright: ignore[reportAny]

    print(
        "Interpreted Response Data:\n",
        f"V_HV: {v_hv} V\n",
        f"I_BATT: {i_batt} A\n",
        f"SOC: {soc} %\n",
    )


def make_uds_request() -> None:
    """Request the specified DIDs from ECU via UDS."""
    dids_requested = [
        DID_V_HV,
        DID_I_BATT,
        DID_SOC,
    ]

    tp_address = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        #isotp.AddressingMode.Extended_29bits,
        # txid=0x7DF,7E0,7E4 and rxid=0x7E8,7EC are good candidates
        txid=0x7E4,
        rxid=0x7EC,
    )

    config = udsoncan.configs.default_client_config.copy()
    config["data_identifiers"] = {
        DID_V_HV: Fixed16Codec(0.5),
        DID_I_BATT: Fixed16Codec(0.25, 32768),
        DID_SOC: Fixed16Codec(0.02),
    }

    # Create udsoncan connection layer
    bus = can.Bus("can_spi", interface="socketcan")
    notifier = can.Notifier(bus, [])
    # Refer to isotp documentation for full details about parameters.
    tp_params = {
        # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
        "tx_data_length": 8,
        # Minimum length of CAN messages. When different from None, messages are
        # padded to meet this length. Works with CAN 2.0 and CAN FD.
        "tx_data_min_length": 8,
        # Will pad all transmitted CAN messages with byte 0x00.
        "tx_padding": 0x00,
    }
    stack = isotp.NotifierBasedCanStack(
        bus,
        notifier=notifier,
        address=tp_address,
        params=tp_params,
    )
    connection = PythonIsoTpConnection(stack)

    with Client(connection, config=config, request_timeout=2.0) as client:
        try:
            print("Sending request to read Data Identifier: ...")
            # Read Data By Identifier (Service 0x22).
            response = client.read_data_by_identifier(dids_requested)  # pyright: ignore[reportArgumentType, reportUnknownVariableType]
        except NegativeResponseException as e:
            print(
                "ECU rejected the request with code:",
                f"{e.response.code_name} (0x{e.response.code:02X})",
            )
        except InvalidResponseException as e:
            print(f"Received an invalid or malformed response: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"An unexpected error occurred: {e}")
        print_response(response)  # pyright: ignore[reportArgumentType, reportPossiblyUnboundVariable]

if __name__ == "__main__":
    make_uds_request()
