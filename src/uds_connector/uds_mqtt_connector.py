#!/usr/bin/env python3
"""UDS Connector.

UDS Diagnostic API Component for Linux Userspace.

See documentation in README.md.

Version: 0.0.0-DoesNotWorkYet
Date: 2026-07-26
Author: Ulrich Lukas
License: GPL v3
"""
import time
from typing import TYPE_CHECKING

import isotp
import udsoncan
import udsoncan.configs
from paho.mqtt import client as mqtt_client
from paho.mqtt.client import Client as MqttClient
from paho.mqtt.client import ConnectFlags
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from udsoncan.exceptions import (
    InvalidResponseException,
    NegativeResponseException,
    #TimeoutException,
    #UnexpectedResponseException,
)
from udsoncan.services.ReadDataByIdentifier import ReadDataByIdentifier

from uds_connector.did_codecs import Fixed8Codec, Fixed16Codec, RawCodec
from uds_connector.include.text_screen import TextScreen
from uds_connector.python_iso_tp_client import PythonIsoTpClient

if TYPE_CHECKING:
    from udsoncan.typing import ClientConfig


# Transport protocol IDs for the EVC unit
# In case of transport over 11-bit CAN, this is identical to the CAN IDs.
TP_ID_EVC_REQUEST = 0x7E4
TP_ID_EVC_RESPONSE = 0x7EC

# HV Voltage
DID_HV_V = 0x3203
# Charging/Discharging Current
DID_HV_A = 0x3204
# SOC
DID_SOC = 0x2002
# SOH
DID_SOH = 0x3206
# Battery Temperature
DID_BATT_TEMP = 0x2001

broker = "localhost"
port = 1883
topic = "erp/uds_push"


# For text output on the console, re-using the same screen area for each update.
screen = TextScreen()


def connect_mqtt() -> MqttClient:
    """Connect to MQTT broker and return the client object."""
    def on_connect(
        _client: MqttClient,
        _userdata: object | None,
        _flags: ConnectFlags | None,
        reason_code: ReasonCode | None,
        _properties: Properties | None,
    ) -> None:
        """Callback function for MQTT connection."""
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {reason_code}")

    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
    )
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    _ = client.connect(broker, port)
    return client


def publish(mqtt_client: MqttClient, response: ReadDataByIdentifier.InterpretedResponse) -> None:
    """Publish requested values from response object to MQTT broker."""
    values = response.service_data.values
    hv_v = values[DID_HV_V]  # pyright: ignore[reportAny]
    hv_a = values[DID_HV_A]  # pyright: ignore[reportAny]
    soc = values[DID_SOC]  # pyright: ignore[reportAny]
    soh = values[DID_SOH]  # pyright: ignore[reportAny]
    batt_temp = values[DID_BATT_TEMP]  # pyright: ignore[reportAny]
    msg = (
        '{'
        + f'"HV_V":{hv_v:0.0f},'
        + f'"HV_A":{hv_a:0.1f},'
        + f'"SOC":{soc:0.2f},'
        + f'"SOH":{soh:0.0f},'
        + f'"BATT_TEMP":{batt_temp:0.0f}'
        + '}'
    )
    result = mqtt_client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Sent `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def print_response(response: ReadDataByIdentifier.InterpretedResponse) -> None:
    """Print requested values from response object."""
    # Extract Values
    values = response.service_data.values
    hv_v = values[DID_HV_V]  # pyright: ignore[reportAny]
    hv_a = values[DID_HV_A]  # pyright: ignore[reportAny]
    soc = values[DID_SOC]  # pyright: ignore[reportAny]
    soh = values[DID_SOH]  # pyright: ignore[reportAny]
    batt_temp = values[DID_BATT_TEMP]  # pyright: ignore[reportAny]
    screen.put(
        "Interpreted Response Data:\n"
            + f"HV_V: {hv_v} V\n"
            + f"HV_A: {hv_a} A\n"
            + f"SOC: {soc} %\n"
            + f"SOH: {soh} %\n"
            + f"BATT_TEMP: {batt_temp} °C\n",
    )
    screen.refresh()


def main() -> None:
    """Request the specified DIDs from ECU via UDS and publish the results."""
    mqtt_client = connect_mqtt()
    _ = mqtt_client.loop_start()

    dids_requested: list[int] = [
        DID_HV_V,
        DID_HV_A,
        DID_SOC,
        DID_SOH,
        DID_BATT_TEMP,
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
        "default": RawCodec(),
        DID_HV_V: Fixed16Codec(0.5),
        DID_HV_A: Fixed16Codec(0.25, 32768),
        DID_SOC: Fixed16Codec(0.02),
        DID_SOH: Fixed8Codec(1.0),
        DID_BATT_TEMP: Fixed8Codec(1.0, 40),
    }

    with PythonIsoTpClient(tp_address, client_config) as client:
        try:
            while True:
                print("Sending request to read Data Identifier: ...")
                # Read Data By Identifier (Service 0x22).
                response = client.read_data_by_identifier(dids_requested)  # pyright: ignore[reportArgumentType, reportUnknownVariableType]
                print_response(response)  # pyright: ignore[reportArgumentType]
                publish(mqtt_client, response)  # pyright: ignore[reportArgumentType]
                time.sleep(0.5)
        except NegativeResponseException as e:
            print(
                "ECU rejected the request with code:",
                f"{e.response.code_name} (0x{e.response.code:02X})",
            )
        except InvalidResponseException as e:
            print(f"Received an invalid or malformed response: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"An unexpected error occurred: {e}")
        finally:
            _ = mqtt_client.loop_stop()
            _ = mqtt_client.disconnect()

if __name__ == "__main__":
    main()
