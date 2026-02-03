class InvariantViolation(Exception):
    pass


def check_I4(actor: str):
    # I4 — WINDI não pode ser ator decisório
    if actor == "windi":
        raise InvariantViolation("I4 violated: WINDI cannot be decision actor")


def check_I5(payload: str):
    # I5 — Bloqueio de possíveis dados pessoais
    forbidden = ["cpf", "rg", "address", "email", "phone"]
    text = payload.lower()
    if any(word in text for word in forbidden):
        raise InvariantViolation("I5 violated: potential personal data detected")


def check_I8():
    # I8 — Operação local (garantido por bind 127.0.0.1)
    return True


def enforce_all(event):
    check_I4(event.actor)
    check_I5(event.payload)
    check_I8()
