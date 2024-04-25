# FiberPTS: Factory Production Tracking System

## Project Summary

**FiberPTS** aims to provide visibility on manufacturing operations by tracking production throughput, providing key data insights to improve labor and production efficiencies. The system utilizes Supabase, a scalable and secure backend, to manage data across various IoT devices in real-time.

Check out the demo video [here](https://www.youtube.com/watch?v=TWLcf_nFILc&ab_channel=JuanDiegoBecerra).

## Purpose, Scope, and Objectives

The **Factory Production Tracking System (FiberPTS)** leverages IoT devices equipped at various operational points within a manufacturing plant to collect real-time data through operator interactions. This data is then centralized for visualization, offering significant benefits:

- **Efficiency Optimization**: Identifying bottlenecks to accelerate production cycles.
- **Data-Driven Decision Making**: Enhancing managerial decisions with real-time accuracy.
- **Financial Accuracy**: Supporting more precise costing and financial planning.
- **Operational Planning**: Streamlining labor scheduling and deliveries.

### System Components

- **NFC Reader**: Captures data from NFC tags used by employees and for orders.
- **Touch Sensor**: Tracks completed operations done by employees.
- **Display**: Shows order and employee data, and provides interactive feedback to the operator.

## Setup Guide

### Prerequisites

- **Hardware**:
  - **NFC Reader**: PN532 NFC reader for scanning NFC tags. [Available here](https://www.amazon.com/gp/product/B0B7L47YSZ/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1)
  - **NFC Tag**: NTAG215, used for employee and order identification. [Available here](https://www.amazon.com/gp/product/B0BWDVFDTV/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1)
  - **Touch Sensor**: TTP223 Capacitive Touch Sensor for operation inputs. [Available here](https://www.amazon.com/gp/product/B07X87GX6G/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
  - **Display**: 3.2 inch TFT LCD SPI ILI9341 to display information to users. [Available here](https://www.amazon.com/gp/product/B0B1M9S9V6/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
  - **Controller Board**: [Le Potato (aml-s905x-cc)](https://libre.computer/products/aml-s905x-cc/)
    - **MicroSD Card**: SanDisk 64GB Extreme microSDXC. [Available Here](https://www.amazon.com/gp/product/B07FCMBLV6/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1)
    - **Wi-Fi Dongle**: Archer T2U Nano. [Available Here](https://www.amazon.com/gp/product/B07PB1X4CN/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1)
    - **Power Supply**: Micro USB Power Supply for Raspberry Pi 3. [Available Here](https://www.amazon.com/gp/product/B01MZX466R/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
    - **GPIO Wires**: Any Standard Female-to-Female Jumpers 
- **Operating System**: [Raspbian Bookworm ARM64 Lite (aml-s905x-cc)](https://distro.libre.computer/ci/raspbian/12/2023-10-10-raspbian-bookworm-arm64-lite%2Baml-s905x-cc.img.xz)

### Installation

#### Boot

1. **Install ISO Image**: 
   - Download the `2023-10-10-raspbian-bookworm-arm64-lite+aml-s905x-cc` [ISO image](https://distro.libre.computer/ci/raspbian/12/2023-10-10-raspbian-bookworm-arm64-lite%2Baml-s905x-cc.img.xz).
   - Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to burn the image to a microSD.
     - Select the ISO under *Operating System*.
     - Choose your USB card reader under *Storage*.
     - Click *NEXT* and select *No* for additional settings.
2. **Boot and Set Login**: Follow on-screen instructions to set a memorable login.

#### Network Setup

1. **Connect Ethernet**: Ensure your device is connected to your network via Ethernet.

#### SSH Configuration

1. **Enable SSH**:
   - `sudo systemctl enable ssh.service`
   - `sudo systemctl start ssh.service`
   - Find your IP using `hostname -I`
   - Note: If SSH fails, clear `.ssh` on your remote device and retry.
2. **Remote Access**:
   - Connect via `ssh USERNAME@HOSTNAME`

#### Repository Setup

1. **Clone the FiberPTS Repository**:
   - `sudo apt install git -y`
   - `cd /opt`
   - `sudo git clone https://github.com/NxFerrara/FiberPTS.git`
   - `cd FiberPTS`
   - `sudo git checkout <branch_name>`
2. **Environment Configuration**:
   - Manually add the `.env` file to `/opt/FiberPTS/.env`.
   - The contents of this file are available in the shared GDrive folder (omitted for security).
   - Use `sudo nano /opt/FiberPTS/.env` to create and edit the file.

#### Running Setup Scripts

1. **Initial Setup**:
   - `sudo bash scripts/setup/setup.sh --pre`
   - Reboot the device due to expected error with libretech wiring tool using ldto.
   - `sudo bash scripts/setup/setup.sh --pre`
2. **Final Setup**:
   - `sudo bash scripts/setup/setup.sh --post`

#### Validate System Operation

1. **Review Logs**:
   - Use the command `tail -f -n 100 PROJECT_DIR/FiberPTS/.app/logs/fpts.log` to read the last 100 entries in real-time.
     - The project directory is set in `paths.sh`
     - The logs should indicate the programs have begun and generates logs upon touch sensor taps and/or NFC taps

### Important Configurations For System Operation

Before running the system, ensure the following configurations are completed:
- **GPIO Configuration**: Setup the GPIO connections as detailed [here](https://github.com/NxFerrara/FiberPTS/new/main?filename=README.md#gpio-wiring-configuration).
- **Database Setup**: Configure the database tables and policies as outlined [here](https://github.com/NxFerrara/FiberPTS/new/main?filename=README.md#database-configuration).
- **System Configuration**: Modify the system configurations according to your specifications [here](https://github.com/NxFerrara/FiberPTS/new/main?filename=README.md#system-configuration)

## Configurations

### GPIO Wiring Configuration

Here is the GPIO header mapping for connecting the IoT devices:

![AML-S905X-CC-Headers (1)](https://github.com/NxFerrara/FiberPTS/assets/101071768/03d7d812-3ce5-45ec-afb1-c719288c96e1)

Follow these wiring instructions for each module:

- **Display**:
  - VCC: Pin 17
  - DIN (SDI MOSI): Pin 19
  - DO (SDO MISO): Pin 21
  - BL (LED): Pin 3
  - CLK (SCK): Pin 23
  - CS: Pin 24
  - DC: Pin 29
  - GND: Pin 30
  - RST: Pin 31

- **NFC Reader**:
  - VCC: Pin 2
  - GND: Pin 6
  - SCL: Pin 8
  - SDA: Pin 10

- **Touch Sensor**:
  - VCC: Pin 4
  - GND: Pin 25
  - I/O: Pin 32

- **Fan**:
  - VCC: Pin 1
  - GND: Pin 9

### Database Configuration

1. **Setting Up the Database**:
   - Refer to the ER Diagram to correctly configure the database schema required for FiberPTS:
 ![ER Diagram for FiberPTS](https://github.com/NxFerrara/FiberPTS/assets/101071768/d94e75f0-4255-4187-80f7-5ef7e1b03b1d)

2. **Database Policies**
   - Set up the following policies on Supabase for data security and accessibility:
     - `devices`, `employees`, `machines`, `orders`: Allow `insert`, `select`, and `update` for anonymous users.
     - `employee_tags`, `order_tag_groups`, `order_tags`: Allow `select` for anonymous users.
     - `action_tap_data`, `employee_tap_data`, `order_tap_data`: Allow `insert` and `select` for anonymous users.

3. **Database Tables Explanation**:
   - **action_tap_data**: Stores data from touch sensor taps as actions are performed.
   - **devices**: Registers each device with its specific location and associated machine.
   - **employee_tags**: Links NFC tags to employee IDs for access and operation logging.
   - **employee_tap_data**: Logs the time when employees start working on a device.
   - **employees**: Contains employee details such as UID and full name for identification.
   - **machines**: Lists machines with their specific identifiers and names for easy tracking.
   - **order_tag_groups**: Groups order tags for batch processing and management.
   - **order_tags**: Associates NFC tags with specific orders for tracking and verification.
   - **order_tap_data**: Logs when an order commences at a machine by a particular employee.
   - **orders**: Catalogues all orders handled by the system for fulfillment and tracking.

4. **.env File Configuration**:
   - Fill out the `.env` file with the necessary details:
     ```
     DATABASE_URL=your_supabase_database_url
     DATABASE_API_KEY=your_supabase_api_key
     ```
   - Ensure these values are correct to enable proper database connections.

### System Configuration

It is crucial not to change variable names in the configuration files unless they are updated across the entire codebase:
- **paths.sh**: Manages application paths and system configurations.
- **screen_config.py**: Settings for the display module.
- **touch_sensor_config.py**: Configuration parameters for the touch sensor.
- **globals.sh**: Defines global variables and settings for setup and runtime scripts.

## Documentation

For detailed documentation on the setup and maintenance of the FiberPTS system, refer to our [Confluence page](https://fiber-pts.atlassian.net/wiki/spaces/FiberPTS/pages/458982/Documentation).

### Documented Error Events

Refer to the documented error events and their resolutions here:

[IoT Device Errors Documentation](https://fiber-pts.atlassian.net/wiki/spaces/FiberPTS/pages/23035938/IoT+Device+Errors)

## Copyright Policy

### Copyright Notice

Copyright © 2024 The FiberPTS Contributors. All rights reserved.

The content, documentation, code, and related materials contained in the FiberPTS repository and its documentation are the intellectual property of the contributors to the FiberPTS project unless otherwise stated.

### Usage Rights

#### Software License

The software and the accompanying files in the FiberPTS repository are not licensed for public use and remain the exclusive property of the FiberPTS contributors. No rights to use, modify, or distribute the software are granted without explicit written consent from the project owners.

#### Documentation and Content

The documentation, images, and other non-code content provided in the FiberPTS repository are licensed under the [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License (CC BY-NC-ND 4.0)](https://creativecommons.org/licenses/by-nc-nd/4.0/). This license allows others to download the works and share them with others as long as they credit you, but they can’t change them in any way or use them commercially.

### Restrictions

The FiberPTS name, logos, and any other trademarks that identify the project are not included under the licenses granted in this policy. Unauthorized use of these trademarks is not permitted.

No automatic rights are granted. All other rights are expressly reserved by the contributors:
- The right to produce derivative works.
- The right to use the work for commercial purposes.
- The right to distribute the work.

### Governing Law

This policy and your use of this site are governed by the laws of New York, United States, without regard to its choice of law provisions.

### Changes to This Policy

The FiberPTS contributors reserve the right to revise this policy or any part of it at any time. Such revisions will be effective immediately upon notice which may be provided by any means including, but not limited to, posting the revised policy on the FiberPTS repository. It is your responsibility to review the policy periodically for any changes.

### Contact Information

For questions or concerns about this policy, please contact nxferrara1981@gmail.com.

---
**Note**: This README aims to provide a streamlined setup guide. For a complete understanding, please consult the linked documentation or directly contact the project maintainers.
