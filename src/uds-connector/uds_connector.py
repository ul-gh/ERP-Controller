#!/usr/bin/env python3
"""UDSConnector.

UDS over Raspberry Pi Gateway Component for Real-Time Linux Userspace.

See documentation in README.md.
"""
import can
import isotp
import udsoncan
import udsoncan.configs
from udsoncan import AsciiCodec, Request
from udsoncan.services import ReadDataByIdentifier
from udsoncan.client import Client
#from udsoncan.connections import IsoTPSocketConnection
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.exceptions import (
    InvalidResponseException,
    NegativeResponseException,
    TimeoutException,
    UnexpectedResponseException,
)


def interpret_uds_response() -> None:
    # Extract Values
    v_hv = response.service_data.values[did_v_hv]
    i_bat = response.service_data.values[did_i_bat]
    soc = response.service_data.values[did_soc]

    # Print interpreted response data.
    print(
        f"V_HV: {} V\n",
        f"I_BAT: {} A\n",
        f"SOC: {} %\n"
    )


def make_uds_request():
    # HV Voltage
    did_v_hv = 0x3203
    # Battery Current
    did_i_bat = 0x3204
    # SOC
    did_soc = 0x2002

    dids_requested = [did_v_hv, did_i_bat, did_soc]

    tp_address = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        #isotp.AddressingMode.Extended_29bits,
        # txid=0x7DF,7E0,7E4 and rxid=0x7E8,7EC are good candidates
        txid=0x7E4,
        rxid=0x7EC,
    )

    config = udsoncan.configs.default_client_config.copy()
    config["data_identifiers"] = {
        did_v_hv: Fixed16Codec(0.5),
        did_i_bat: Fixed16Codec(0.25, 32768),
        did_soc: Fixed16Codec(0.02),
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
            response = client.read_data_by_identifier(dids_requested)
            
        except NegativeResponseException as e:
            print(f"ECU rejected the request with code: {e.response.code_name} (0x{e.response.code:02X})")
        except InvalidResponseException as e:
            print(f"Received an invalid or malformed response: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    make_uds_request()