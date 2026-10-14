# Push Button LED — KiCad PCB Design

A beginner electronics project designed in **KiCad**: a push-button LED circuit with a 5 V supply input. This repository contains the editable schematic, PCB layout, project settings, a component list, and Gerber manufacturing outputs.

> **Project status:** PCB design files and Gerber outputs are included. Physical fabrication and hardware testing are not claimed here; update this section after you test the board.

## Project overview

The circuit is built around a push button and an LED. The schematic also includes resistors and a polarized capacitor. Use the schematic as the source of truth for exact connectivity and component placement.

## Tools

- KiCad — schematic capture and PCB layout
- Gerber and drill files — manufacturing output

## Repository contents

| Path | Description |
|---|---|
| `PushButtonLed.kicad_sch` | Editable circuit schematic |
| `PushButtonLed.kicad_pcb` | Editable PCB layout |
| `PushButtonLed.kicad_pro` | KiCad project settings |
| `BOM.csv` | Component list / bill of materials |
| `manufacturing/gerber/` | Gerber copper, mask, silkscreen, board outline, drill, and job files |
| `images/` | Schematic, PCB layout, and 3D-view screenshots displayed below |

## Components

See [`BOM.csv`](BOM.csv). Values and part names are copied from the supplied KiCad schematic. Confirm footprints, connector pitch, component polarity, and actual part availability before ordering or assembling.

## How to open the project

1. Install KiCad.
2. Download or clone this repository.
3. Open `PushButtonLed.kicad_pro` in KiCad.
4. Open the schematic and PCB editor to inspect the design.
5. Run the Electrical Rules Checker (ERC) and PCB Design Rules Checker (DRC). Review and resolve any issues before manufacturing.

## Manufacturing notes

The `manufacturing/gerber/` folder contains exported manufacturing files. Before sending them to a PCB manufacturer, verify the board outline, copper layers, drill file, dimensions, clearances, and manufacturing requirements. Upload only the files requested by your manufacturer.

## Project screenshots

### Circuit schematic

![Push Button LED circuit schematic](images/schematic.png)

### PCB layout

![Push Button LED PCB layout](images/pcb-layout.png)

### 3D view of the PCB

![Push Button LED PCB 3D view](images/pcb-3d-view.png)

## What I learned

- Creating a schematic in KiCad
- Assigning and checking component footprints
- Designing a PCB layout
- Exporting Gerber manufacturing files
- Preparing a design for review and fabrication

## Future improvements

- Improve the screenshots and add photos of the fabricated PCB when available.
- Fabricate the PCB and document the real assembly and test results.
- Add a short video or photos showing the circuit operating.
- Record ERC/DRC results and note any changes made after testing.

## Author

**Gurusaeth** — Electronics and Communication Engineering student.

---

If you use or adapt this project, please check the circuit and safety of your own build before applying power.
