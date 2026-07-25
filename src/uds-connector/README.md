# UDS Connector

## This is a System Testing Environment: Not Intended for Productive Use!

## UDS Diagnostic API Component for Real-Time Linux Userspace.

* Version: 0.0.1
* Author: Ulrich Lukas

Example Setup According To: python-udsoncan Project Documentation.

    homepage: https://udsoncan.readthedocs.io/en/latest/
    src: https://github.com/pylessard/python-udsoncan.git

Using python-can-isotp ISO-TP (ISO15765-2) Protocol Layer
on Top of CAN Bus PHY Layer.

    homepage: https://can-isotp.readthedocs.io/en/latest/isotp/implementation.html
    src: https://github.com/pylessard/python-can-isotp.git

Using the "Event-Loop-Driven", /Fully Async/, python-can API.

    homepage: https://python-can.readthedocs.io/en/stable/
    src: https://github.com/hardbyte/python-can

Accessing the SocketCAN API from Linux Userspace.

    homepage: https://docs.kernel.org/networking/can.html
    src: https://kernel.org

Running Linux Kernel Image is Hardware-Specific and Cryptocraphically Signed.

    homepage: https://www.raspberrypi.com/software/operating-systems/
    src: https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-06-19/

CAN Bus Hardware Driver is Mainstream Linux, Real-Time and High-Throughput Options.

    homepage: https://kernel.org
    src: https://www.kernel.org/doc/Documentation/devicetree/bindings/net/can/microchip%2Cmcp251x.txt
    src: https://github.com/andrebdo/linux-mcp2515

Compatible Hardware:

    MCP2518FD 8 MBit/s CAN FD Controller with SPI Attachment
    * 32 Bit Time Stamping
    * 32 Hardwere CAN ID Filters and Masks
    * Mixed CAN 2.0B and CAN FD Mode
    * Functional Safety Design
    homepage: https://www.microchip.com/en-us/product/mcp2518

    MCP2515 1 MBit/s CAN 2.0 EF Controller with SPI Attachment
    homepage: https://www.microchip.com/en-us/product/mcp2515

    Raspberry Pi 5
