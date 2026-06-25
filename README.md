# Edge Compute PLC-to-Printer Traceability Integration

A containerized Python application deployed to a Modicon M580 edge compute node that bridges a PLC and IT systems for automated, serialized label printing. Built and deployed within a 2-week project timeline at Empirical Foods.

## Proprietary Code Notice!!!!!!!!!!!!!!!!!!!

The original source code for this project was developed during my internship at Empirical Foods and is the intellectual property of the company. It cannot be shared publicly. The code included in this repository is a representative implementation written to demonstrate the architecture, patterns, and logic used — it reflects the same approach and structure without exposing any proprietary system details, tag names, IP addresses, or plant-specific configuration.


## Overview

This project closes the traceability loop between a production PLC and the plant's IT infrastructure — from PLC signal, to printed label, to database record — with no manual intervention.

The application runs on an ARM/Linux edge node co-located with the PLC, subscribes to OPC UA tags, triggers a SATO label printer via NiceLabel Automation over TCP/IP, and writes each print event back to a SQL Server database.


## Features

- OPC UA Subscriptions — Monitors serial number, heartbeat, and print-trigger tags on the PLC
- Rising-Edge Detection — Captures serial numbers on trigger signal transitions to prevent duplicate prints
- Heartbeat Handshake — Maintains synchronization between the PLC and edge node, detecting communication loss
- Label Printing — Sends TCP/IP commands to a SATO M84Pro via NiceLabel Automation for real-time, serial-number-specific label generation
- SQL Write-Back — Logs every print event to SQL Server via `pyodbc`, creating an auditable traceability record
- Docker Deployment — Environment-variable-driven configuration allows parameter changes (tags, IP addresses, DB connection strings) without rebuilding the container image
- Portainer Management — Container lifecycle managed via Portainer for easy monitoring and redeployment


## Tech Stack

- Runtime - Python 3.x (ARM/Linux) -
- Containerization - Docker, Portainer -
- PLC Communication - OPC UA (`opcua` / `asyncua`) -
- Printer Communication - TCP/IP → NiceLabel Automation -
- Database - SQL Server via `pyodbc` -
- Hardware - Modicon M580 edge compute node, SATO M84Pro -



## Configuration

All runtime parameters are injected via environment variables — no hardcoded values, no image rebuilds needed for config changes.
```
- `OPC_UA_URL` - OPC UA server endpoint on the PLC 
- `SERIAL_TAG` - Node ID for the serial number tag 
- `TRIGGER_TAG` - Node ID for the print trigger tag 
- `HEARTBEAT_TAG` - Node ID for the PLC heartbeat tag 
- `PRINTER_HOST` - IP address of NiceLabel Automation host 
- `PRINTER_PORT` - TCP port for NiceLabel 
- `DB_CONN_STR` - pyodbc connection string for SQL Server 
```


## How It Works

1. On startup, the app connects to the PLC via OPC UA and subscribes to the trigger, serial number, and heartbeat tags.
2. The heartbeat monitor runs continuously — if the PLC heartbeat stops toggling, the app raises an alert and halts printing to prevent untraced labels.
3. When a rising edge is detected on the print trigger tag, the app reads the current serial number tag value.
4. A TCP/IP message is sent to NiceLabel Automation, which generates and sends the label job to the SATO M84Pro printer.
5. On print confirmation, the app writes a record to SQL Server via `pyodbc` — timestamp, serial number, and print status.



## Deployment

```bash
# Build the image
docker build -t traceability-edge .

# Run with environment config
docker run -d \
  --restart unless-stopped \
  -e OPC_UA_URL=opc.tcp://192.168.*.*: \
  -e SERIAL_TAG=ns=2;s=Serial.Number \
  -e TRIGGER_TAG=ns=2;s=Print.Trigger \
  -e HEARTBEAT_TAG=ns=2;s=PLC.Heartbeat \
  -e PRINTER_HOST=192.168.*.* \
  -e PRINTER_PORT= \
  -e DB_CONN_STR="DRIVER={ODBC Driver 17 for SQL Server};SERVER=..." \
  traceability-edge
```

## Project Context

Company: Empirical Foods, Dakota Dunes, SD  
Timeline: June 2026 – Present  
Role: Systems Engineering Intern
