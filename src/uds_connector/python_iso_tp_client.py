"""PythonIsoTpClient class for uds_connector."""

from typing import TYPE_CHECKING, override

import can
import isotp
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection

if TYPE_CHECKING:
    from types import TracebackType

    from can.bus import BusABC
    from can.notifier import Notifier
    from isotp.protocol import NotifierBasedCanStack
    from udsoncan.typing import ClientConfig

REQUEST_TIMEOUT: float = 1.0  # seconds


class PythonIsoTpClient(Client):
    """A UDS client that uses the PythonIsoTpConnection class for communication.

    Subclass of the udsoncan.client.Client class, providing a UDS client
    acting as a Python Context Manager.
    """

    def __init__(self, tp_address: isotp.Address, client_config: ClientConfig) -> None:
        """Initialize a new instance of the PythonIsoTpClient class.

        Args:
            tp_address (isotp.Address): The ISO-TP address to use for the connection.
            client_config (ClientConfig): The configuration for the UDS client.
        """
        self.can_bus: BusABC = can.Bus("can_spi", interface="socketcan")
        # Create udsoncan connection layer
        self.notifier: Notifier = can.Notifier(self.can_bus, listeners=[])
        # Refer to isotp documentation for full details about parameters.
        tp_params = {
            # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
            "tx_data_length": 8,
            # Minimum length of CAN messages. When different from None, messages
            # are padded to meet this length. Works with CAN 2.0 and CAN FD.
            "tx_data_min_length": 8,
            # Will pad all transmitted CAN messages with byte 0x00.
            "tx_padding": 0x00,
        }
        stack: NotifierBasedCanStack = isotp.NotifierBasedCanStack(
            bus=self.can_bus,
            notifier=self.notifier,
            address=tp_address,
            params=tp_params,
        )
        connection: PythonIsoTpConnection = PythonIsoTpConnection(isotp_layer=stack)

        super().__init__(
            conn=connection,
            config=client_config,
            request_timeout=REQUEST_TIMEOUT,
        )

    @override
    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
        """Exit the runtime context.

        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            traceback: The traceback object.
        """
        self.notifier.stop()
        self.can_bus.shutdown()
        super().__exit__(type=exc_type, value=exc_value, traceback=traceback)

