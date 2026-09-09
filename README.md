# Open-RMF High-Level Stress Tests

This folder contains bash scripts for high-level integration tests of Open-RMF. Each script initializes two tiny robots, dispatches tasks via `rmf_demos_tasks`, and verifies completion.

## test_basic

Initializes tinyRobot1 and tinyRobot2 at their chargers, sends robot2 to pantry then overlaps robot1 to the same pantry after 10 s, then robot2 to lounge, verifying that Open-RMF resolves the first-come conflict and sequences the tasks without deadlock.

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

Initializes both robots at their chargers, creates a conflict for coe between robot2 then robot1 with a follow-up return task for robot2, cancels robot2’s coe task after 6 s and checks that cancellation frees the place for robot1 and both robots complete their remaining tasks.

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

Initializes both robots at their chargers, dispatches robot1 to tinyRobot2_charger so it can use its current location as a valid waitspot with finishing request set to nothing and supplies removed as parking, then sends robot2 to supplies to free space, verifying correct wait-spot allocation and completion.

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

Initializes both robots at their chargers, starts patrols to hardware_2 and pantry, publishes emergency_signal is_emergency=true to force parking, waits, then publishes is_emergency=false and verifies both robots resume and finish their patrol tasks.

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

Initializes both robots at their chargers, sends robot2 to pantry and waits, then dispatches robot1 to a multi-place request lounge pantry and verifies Open-RMF picks lounge because pantry is occupied by robot2.

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

Sets robot2 to lounge and robot1 to pantry, then issues overlapping patrols for both robots between tinyRobot1_charger ↔ supplies with n=2 and verifies the planner resolves the bidirectional use of shared places and both patrols complete.

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

Initializes both robots at their chargers, swaps them to each other's chargers, then later forces a position swap via charger/supplies moves using get_robot_location ... -B supplies semantics, verifying deadlock-free swapping and blocking behavior in Open-RMF.

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
