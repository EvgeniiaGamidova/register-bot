from aiogram.fsm.state import State, StatesGroup


class NewRequest(StatesGroup):
    object_name = State()
    address = State()
    reason = State()
    urgency = State()
    equipment = State()
    contact = State()
    phone = State()
    note = State()


class EditRequest(StatesGroup):
    waiting_for_value = State()
