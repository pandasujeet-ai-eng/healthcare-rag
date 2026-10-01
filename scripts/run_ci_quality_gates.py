from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QualityGate:
    name: str
    command: list[str]
    required: bool = True
    required_file: str | None = None


def print_header(
    title: str,
) -> None:

    print()
    print("=" * 100)
    print(title)
    print("=" * 100)
    print()


def run_gate(
    gate: QualityGate,
) -> bool:

    if gate.required_file:

        required_path = Path(
            gate.required_file
        )

        if not required_path.exists():

            if gate.required:

                print(
                    f"[FAIL] {gate.name}"
                )

                print(
                    "Required file does not exist:"
                )

                print(
                    required_path
                )

                return False

            print(
                f"[SKIP] {gate.name}"
            )

            print(
                f"Optional file not found: "
                f"{required_path}"
            )

            return True

    print_header(
        f"QUALITY GATE: {gate.name}"
    )

    print(
        "COMMAND:"
    )

    print(
        " ".join(
            gate.command
        )
    )

    print()

    completed = subprocess.run(
        gate.command,
        check=False,
        env=os.environ.copy(),
    )

    if completed.returncode == 0:

        print()
        print(
            f"[PASS] {gate.name}"
        )

        return True

    print()
    print(
        f"[FAIL] {gate.name}"
    )

    print(
        f"Exit code: "
        f"{completed.returncode}"
    )

    return False


def main() -> None:

    python = sys.executable

    gates = [
        QualityGate(
            name=(
                "Python source compilation"
            ),
            command=[
                python,
                "-m",
                "compileall",
                "-q",
                "app",
                "scripts",
                "evals",
            ],
        ),

        QualityGate(
            name=(
                "Pytest regression suite"
            ),
            command=[
                python,
                "-m",
                "pytest",
                "-ra",
            ],
        ),

        QualityGate(
            name=(
                "Resilience engineering"
            ),
            command=[
                python,
                "-m",
                "scripts.test_resilience",
            ],
            required_file=(
                "scripts/test_resilience.py"
            ),
        ),

        QualityGate(
            name=(
                "Enterprise observability"
            ),
            command=[
                python,
                "-m",
                "scripts.test_observability",
            ],
            required_file=(
                "scripts/test_observability.py"
            ),
        ),

        QualityGate(
            name=(
                "Agentic AI behavior evaluation"
            ),
            command=[
                python,
                "-m",
                "scripts.run_agentic_eval",
            ],
            required_file=(
                "scripts/run_agentic_eval.py"
            ),
        ),
    ]

    results: list[
        tuple[str, bool]
    ] = []

    for gate in gates:

        passed = run_gate(
            gate
        )

        results.append(
            (
                gate.name,
                passed,
            )
        )

        if not passed:

            print_header(
                "CI QUALITY GATE FAILED"
            )

            print(
                f"Deployment must be blocked "
                f"because this gate failed:"
            )

            print(
                gate.name
            )

            raise SystemExit(
                1
            )

    print_header(
        "CI QUALITY GATE SUMMARY"
    )

    for name, passed in results:

        status = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            f"{status:5} | {name}"
        )

    print()
    print(
        "ALL CI QUALITY GATES PASSED"
    )


if __name__ == "__main__":
    main()