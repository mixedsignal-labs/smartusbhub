"""
Unified FlexConnect test scenarios entry script.

This script provides a single entry point to run all manual
FlexConnect test scenarios that were previously split into
multiple files:

  - Scenario 2.3: Disable power-off restore, use default mode
  - Scenario 2.4: Persistence of power-off restore state
  - Scenario 3.x: Priority logic verification
  - Scenario 4:   Factory reset related scenario
  - Scenario 5:   Button power-off scenario
  - Scenario 6:   Boundary condition scenario

Each original script remains unchanged; this file simply
imports and calls their ``main()`` functions so you can
run all scenarios from one place.
"""

import sys
import os

# Add project root to path so we can import smartusbhub from any location
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import scenario entry functions from scenarios package
from .scenarios.test_scenario_2_3 import main as scenario_2_3_main
from .scenarios.test_scenario_2_4 import main as scenario_2_4_main
from .scenarios.test_scenario_3_priority import main as scenario_3_priority_main
from .scenarios.test_scenario_4_factory_reset import main as scenario_4_factory_reset_main
from .scenarios.test_scenario_5_button_poweroff import main as scenario_5_button_poweroff_main
from .scenarios.test_scenario_6_boundary import main as scenario_6_boundary_main


SCENARIOS = {
    "2.3": ("Scenario 2.3 - Disable power-off restore (use default mode)", scenario_2_3_main),
    "2.4": ("Scenario 2.4 - Power-off restore state persistence", scenario_2_4_main),
    "3": (
        "Scenario 3.x - Priority logic verification (includes 3.1 / 3.2 / 3.3 inside script)",
        scenario_3_priority_main,
    ),
    "4": ("Scenario 4 - Factory reset related scenario", scenario_4_factory_reset_main),
    "5": ("Scenario 5 - Button power-off scenario", scenario_5_button_poweroff_main),
    "6": ("Scenario 6 - Boundary condition scenario", scenario_6_boundary_main),
}


def print_menu() -> None:
    print("\n" + "=" * 70)
    print("FlexConnect manual test scenarios (single entry) / FlexConnect 手工测试场景入口")
    print("=" * 70)
    for key, (title, _) in SCENARIOS.items():
        print(f"  {key}: {title}")
    print("  a: Run ALL scenarios sequentially / 依次运行所有场景")
    print("  q: Quit / 退出")
    print("=" * 70)


def run_scenario(key: str) -> None:
    title, func = SCENARIOS[key]
    print("\n" + "-" * 70)
    print(f"Running {title}")
    print("-" * 70)
    func()
    print("\n" + "-" * 70)
    print(f"Finished {title}")
    print("-" * 70)


def main() -> None:
    while True:
        print_menu()
        choice = input("Select scenario (e.g. 2.3, 2.4, 3, 4, 5, 6, a, q): ").strip().lower()

        if choice == "q":
            print("Exit FlexConnect test scenarios.")
            break
        if choice == "a":
            # Run all scenarios in a fixed order
            for key in ["2.3", "2.4", "3", "4", "5", "6"]:
                run_scenario(key)
            continue

        # Normalize simple digit input like "3" vs "3.0"
        if choice in SCENARIOS:
            run_scenario(choice)
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()


