from pi_voice_assistant.core.state_machine import AssistantState


def test_state_names_are_stable() -> None:
    assert AssistantState.IDLE.value == "idle"
    assert AssistantState.ERROR.value == "error"
