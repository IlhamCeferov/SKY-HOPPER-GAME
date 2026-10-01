"""Validated keyboard input helpers for the terminal interface."""


def ask_text(prompt: str, *, maximum: int = 40) -> str:
    while True:
        value = input(prompt).strip()
        if not value:
            print("Please enter a value.")
        elif len(value) > maximum:
            print(f"Please use at most {maximum} characters.")
        else:
            try:
                value.encode("latin1")
            except UnicodeEncodeError:
                print("Save names must use characters supported by the existing database.")
                continue
            return value


def ask_int(prompt: str, *, minimum: int, maximum: int) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
            if minimum <= value <= maximum:
                return value
        except ValueError:
            pass
        print(f"Enter a whole number from {minimum} to {maximum}.")


def ask_yes_no(prompt: str) -> bool:
    while True:
        value = input(f"{prompt} [y/n]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")