# Open-RMF High-Level Stress Tests

This folder contains bash scripts for high-level integration tests of Open-RMF. Each script initializes two tiny robots, dispatches tasks via `rmf_demos_tasks`, and verifies completion.

## test_basic

```mermaid
flowchart TD
    A["Init: tinyRobot1 to tinyRobot1_charger"] --> B["Wait complete"]
    C["Init: tinyRobot2 to tinyRobot2_charger"] --> B
    B --> D["tinyRobot2 to pantry"]
    D --> E["Sleep 10s"]
    E --> F["tinyRobot1 to pantry overlapping request"]
    F --> G["Wait tinyRobot2 complete"]
    G --> H["tinyRobot2 to lounge"]
    H --> I["Wait tinyRobot2 complete"]
    I --> J["Wait tinyRobot1 complete"]
```

## test_cancellation

```mermaid
flowchart TD
    A["Init: tinyRobot1 to tinyRobot1_charger"] --> B["Wait complete"]
    C["Init: tinyRobot2 to tinyRobot2_charger"] --> B
    B --> D["tinyRobot2 to coe"]
    D --> E["tinyRobot1 to coe conflict"]
    E --> F["tinyRobot2 follow-up to tinyRobot2_charger"]
    F --> G["Sleep 6s"]
    G --> H["Cancel tinyRobot2 coe task"]
    H --> I["Wait tinyRobot1 complete"]
    I --> J["Wait tinyRobot2 complete"]
```

## test_current_waitspot

```mermaid
flowchart TD
    A["Init: tinyRobot1 to tinyRobot1_charger"] --> B["Wait complete"]
    C["Init: tinyRobot2 to tinyRobot2_charger"] --> B
    B --> D["tinyRobot1 to tinyRobot2_charger current waitspot test"]
    D --> E["Sleep 5s"]
    E --> F["tinyRobot2 to supplies to free space"]
    F --> G["Wait tinyRobot1 complete"]
    G --> H["Wait tinyRobot2 complete"]
```

## test_emergency_pullover

```mermaid
flowchart TD
    A["Init: tinyRobot1 to tinyRobot1_charger"] --> B["Wait complete"]
    C["Init: tinyRobot2 to tinyRobot2_charger"] --> B
    B --> D["tinyRobot1 patrol to hardware_2"]
    D --> E["tinyRobot2 patrol to pantry"]
    E --> F["Sleep 10s"]
    F --> G["Publish emergency_signal is_emergency=true"]
    G --> H["Sleep 20s robots park"]
    H --> I["Publish emergency_signal is_emergency=false"]
    I --> J["Wait tinyRobot1 complete"]
    J --> K["Wait tinyRobot2 complete"]
```

## test_multi_place

```mermaid
flowchart TD
    A["Init: tinyRobot1 to tinyRobot1_charger"] --> B["Wait complete"]
    C["Init: tinyRobot2 to tinyRobot2_charger"] --> B
    B --> D["tinyRobot2 to pantry"]
    D --> E["Wait tinyRobot2 complete"]
    E --> F["tinyRobot1 to lounge pantry multi-place"]
    F --> G["Wait tinyRobot1 complete should pick lounge"]
```

## test_patrol

```mermaid
flowchart TD
    A["Init: tinyRobot2 to lounge"] --> B["Wait complete"]
    C["Init: tinyRobot1 to pantry"] --> B
    B --> D["tinyRobot1 patrol tinyRobot1_charger supplies n=2"]
    D --> E["tinyRobot2 patrol supplies tinyRobot1_charger n=2 overlap"]
    E --> F["Wait tinyRobot2 complete"]
    F --> G["Wait tinyRobot1 complete"]
```

## test_swap

```mermaid
flowchart TD
    A["Init: tinyRobot1 to tinyRobot1_charger"] --> B["Wait complete"]
    C["Init: tinyRobot2 to tinyRobot2_charger"] --> B
    B --> D["tinyRobot2 to tinyRobot1_charger"]
    D --> E["tinyRobot1 to tinyRobot2_charger swap"]
    E --> F["Wait both complete"]
    F --> G["tinyRobot1 to tinyRobot1_charger"]
    G --> H["get_robot_location tinyRobot1 at supplies -B"]
    H --> I["tinyRobot2 to supplies"]
    I --> J["Wait tinyRobot2 complete"]
    J --> K["Wait tinyRobot1 complete"]
    K --> L["tinyRobot1 to supplies"]
    L --> M["tinyRobot2 to tinyRobot1_charger swap again"]
    M --> N["Wait both complete"]
```
