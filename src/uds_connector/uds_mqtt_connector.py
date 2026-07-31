#!/usr/bin/env python3
"""UDS Connector.

UDS Diagnostic API Component for Linux Userspace.

See documentation in README.md.

Version: 0.0.0-DoesNotWorkYet
Date: 2026-07-26
Author: Ulrich Lukas
License: GPL v3
"""
import argparse
import logging
import threading
import time
from typing import TYPE_CHECKING, cast

import isotp
import udsoncan
import udsoncan.configs
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
from udsoncan.exceptions import (
    InvalidResponseException,
    NegativeResponseException,
    #TimeoutException,
    #UnexpectedResponseException,
)

from uds_connector.did_codecs import Fixed8Codec, Fixed16Codec, RawCodec
from uds_connector.include.text_screen import TextScreen
from uds_connector.python_iso_tp_client import PythonIsoTpClient

if TYPE_CHECKING:
    from paho.mqtt.client import Client as MqttClient
    from paho.mqtt.client import ConnectFlags, MQTTMessage
    from paho.mqtt.properties import Properties
    from paho.mqtt.reasoncodes import ReasonCode
    from udsoncan.services.ReadDataByIdentifier import ReadDataByIdentifier
    from udsoncan.typing import ClientConfig

    type InterpretedResponse = ReadDataByIdentifier.InterpretedResponse

parser = argparse.ArgumentParser(prog=__package__, description=__doc__)
_ = parser.add_argument("-v", "--verbose", action="store_true", help="Set loglevel to DEBUG")


cmdline = parser.parse_args()

logger = logging.getLogger(__name__)


if cmdline.verbose:  # pyright: ignore[reportAny]
    logger.setLevel(level=logging.DEBUG)
    SCREEN_OUTPUT_ACTIVATED = True
else:
    logger.setLevel(level=logging.INFO)
    SCREEN_OUTPUT_ACTIVATED = False  # pyright: ignore[reportConstantRedefinition]


# Transport protocol IDs for the EVC unit
# In case of transport over 11-bit CAN, this is identical to the CAN IDs.
TP_ID_EVC_REQUEST: int = 0x7E4
TP_ID_EVC_RESPONSE: int = 0x7EC

# HV Voltage
DID_HV_V: int = 0x3203
# Charging/Discharging Current
DID_HV_A: int = 0x3204
# SOC
DID_SOC: int = 0x2002
# SOH
DID_SOH: int = 0x3206
# Battery Temperature
DID_BATT_TEMP: int = 0x2001

broker: str = "localhost"
port: int = 1883
topic_push: str = "erp/uds_connector/push"
topic_subscribe: str = "erp/uds_connector/activate"


# For text output on the console, re-using the same screen area for each update.
screen = TextScreen(clear_extra_lines=2)
uds_push_activated = threading.Event()


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
            logger.info("Connected to MQTT Broker!")
        else:
            logger.error("Failed to connect, return code %d", reason_code)

    def on_message(
            _client: mqtt_client.Client,
            _userdata: object | None,
            msg: MQTTMessage,
        ) -> None:
        """Callback function for MQTT messages."""
        msg_lower: str = msg.payload.decode().lower()
        if msg_lower == "true":
            uds_push_activated.set()
            logger.info("Activating UDS push.")
        else:
            uds_push_activated.clear()
            logger.info("Deactivating UDS push.")

    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
    )
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    _ = client.connect(broker, port)
    _ = client.subscribe(topic_subscribe)
    return client


def publish(mqtt_client: MqttClient, response: InterpretedResponse) -> None:
    """Publish requested values from response object to MQTT broker."""
    values = cast("dict[int, float]", response.service_data.values)
    hv_v: float = values[DID_HV_V]
    hv_a: float = values[DID_HV_A]
    soc: float = values[DID_SOC]
    soh: float = values[DID_SOH]
    batt_temp: float = values[DID_BATT_TEMP]
    msg = (
        '{'
        + f'"HV_V":{hv_v:0.0f},'
        + f'"HV_A":{hv_a:0.1f},'
        + f'"SOC":{soc:0.2f},'
        + f'"SOH":{soh:0.0f},'
        + f'"BATT_TEMP":{batt_temp:0.0f}'
        + '}'
    )
    result = mqtt_client.publish(topic_push, msg)
    status = result[0]
    if status == 0:
        logger.debug("Sent `%s` to topic `%s`", msg, topic_push)
    else:
        logger.warning("Failed to send message to topic: %s", topic_push)


def print_response(response: InterpretedResponse) -> None:
    """Print requested values from response object."""
    # Extract Values
    values = cast("dict[int, float]", response.service_data.values)
    hv_v: float = values[DID_HV_V]
    hv_a: float = values[DID_HV_A]
    soc: float = values[DID_SOC]
    soh: float = values[DID_SOH]
    batt_temp: float = values[DID_BATT_TEMP]
    screen.put(
        "Interpreted Response Data:\n"
            + f"HV_V: {hv_v} V\n"
            + f"HV_A: {hv_a} A\n"
            + f"SOC: {soc} %\n"
            + f"SOH: {soh} %\n"
            + f"BATT_TEMP: {batt_temp} C\n",
    )
    screen.refresh()


def main() -> None:
    """Request the specified DIDs from ECU via UDS and publish the results."""
    mqtt_client: MqttClient = connect_mqtt()
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
        # txid=0x7DF,7E0,7E4 and rxid=0x7E8,7EC are also good candidates
        txid=TP_ID_EVC_REQUEST,
        rxid=TP_ID_EVC_RESPONSE,
    )

    client_config: ClientConfig = udsoncan.configs.default_client_config.copy()
    client_config["data_identifiers"] = {
        "default": RawCodec(),
        DID_HV_V: Fixed16Codec(scale=0.5),
        DID_HV_A: Fixed16Codec(scale=0.25, offset=32768),
        DID_SOC: Fixed16Codec(scale=0.02),
        DID_SOH: Fixed8Codec(scale=1.0),
        DID_BATT_TEMP: Fixed8Codec(scale=1.0, offset=40),
    }

    def do_client_run(tp_client: PythonIsoTpClient) -> None:
        """Perform a single UDS request and publish the results."""
        logger.debug("Sending request to read Data Identifier...")
        # Read Data By Identifier (Service 0x22).
        response = cast(
            "InterpretedResponse",
            tp_client.read_data_by_identifier(dids_requested),  # pyright: ignore[reportArgumentType]
        )
        if SCREEN_OUTPUT_ACTIVATED:
            print_response(response)
        publish(mqtt_client, response)

    with PythonIsoTpClient(tp_address, client_config) as tp_client:
        try:
            while True:
                if uds_push_activated.is_set():
                    do_client_run(tp_client)
                time.sleep(0.5)
        except NegativeResponseException as e:
            logger.warning(
                "ECU rejected the request with code: %s (0x%02X)",
                e.response.code_name,
                e.response.code,
            )
        except InvalidResponseException as e:
            logger.warning("Received an invalid or malformed response: %s", e)
        except Exception as e:  # noqa: BLE001
            logger.warning("An unexpected error occurred: %s", e)
        finally:
            _ = mqtt_client.loop_stop()
            _ = mqtt_client.disconnect()

if __name__ == "__main__":
    main()
