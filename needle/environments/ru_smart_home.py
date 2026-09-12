"""Умный дом: управление ограниченным набором комнат и устройств.

Замените значения Literal на комнаты и устройства, которые предоставляет ваш продукт.
Сохраняйте структуры: каждое закрытое множество — это enum, каждое число имеет границы,
и ни один корректный вызов не должен требовать значения, которое не сказал пользователь.
"""

import sys
from typing import Annotated, Literal, Optional

import needle
from needle.environments import _harness

Room = Literal["кухня", "гостиная", "спальня", "кабинет"]


@needle.tool
def control_lights(
    room: Room,
    action: Literal["включить", "выключить", "приглушить"],
    brightness_percent: Annotated[Optional[int], needle.Field(ge=0, le=100)] = None,
    color: Optional[Literal["теплый белый", "холодный белый", "красный", "зеленый", "синий"]] = None,
):
    """Включить или выключить свет в комнате, приглушить его до процента яркости или задать цвет. Запрос цвета означает включение. Никогда не используйте это для жалюзи, вентиляторов или любых других устройств.

    Args:
        room: Комната для управления.
        action: включить, выключить или приглушить.
        brightness_percent: Яркость от 0 до 100. Запрос приглушения с числом должен нести его в этом же вызове.
        color: Цвет света; включайте только когда пользователь называет один из них.
    """
    return {"ok": True, "room": room, "action": action, "brightness_percent": brightness_percent, "color": color}


@needle.tool
def set_thermostat(temperature: Annotated[int, needle.Field(ge=10, le=30)]):
    """Установить домашний термостат на целевую температуру в градусах Цельсия. Это никогда не управляет вентиляторами, светом или любым другим устройством.

    Args:
        temperature: Целевая температура в градусах Цельсия.
    """
    return {"ok": True, "temperature": temperature}


@needle.tool
def control_fan(
    room: Literal["гостиная", "спальня", "кабинет"],
    action: Literal["включить", "выключить"],
    speed: Optional[Literal["низкая", "средняя", "высокая"]] = None,
):
    """Включить или выключить вентилятор в комнате, опционально на указанной скорости. Это никогда не меняет термостат.

    Args:
        room: Комната, чьим вентилятором нужно управлять.
        action: включить или выключить.
        speed: Скорость вентилятора; включайте только если указано.
    """
    return {"ok": True, "room": room, "action": action, "speed": speed}


@needle.tool
def control_blinds(room: Room, action: Literal["открыть", "закрыть"]):
    """Открыть или закрыть оконные жалюзи в одной указанной комнате. Никогда не выбирайте комнату сами. Никогда не используйте это для света или пылесоса.

    Args:
        room: Комната, чьи жалюзи нужно двигать.
        action: открыть или закрыть.
    """
    return {"ok": True, "room": room, "action": action}


@needle.tool
def start_robot_vacuum(
    action: Literal["старт", "стоп", "на базу"],
    room: Optional[Literal["кухня", "гостиная", "спальня"]] = None,
):
    """Запустить или остановить робот-пылесос, или отправить его на базу для зарядки.

    Args:
        action: старт, стоп или на базу.
        room: Комната для уборки; включайте только при начале работы в указанной комнате.
    """
    return {"ok": True, "action": action, "room": room}


TOOLS = [control_lights, set_thermostat, control_fan, control_blinds, start_robot_vacuum]
SYSTEM = "Сопоставляйте каждое явное поддерживаемое домашнее действие ровно с одним объявленным вызовом; никогда не дублируйте действие. Не угадывайте пропущенные цели или значения. Неподдерживаемые, недействительные, неоднозначные и отрицательные запросы не возвращают вызовов."


TEST_CASES = [
    {'query': 'включи свет на кухне', 'calls': [{'name': 'control_lights', 'arguments': {'room': 'кухня', 'action': 'включить'}}], 'category': 'positive'},
    {'query': 'выключи свет в спальне', 'calls': [{'name': 'control_lights', 'arguments': {'room': 'спальня', 'action': 'выключить'}}], 'category': 'positive'},
    {'query': 'приглуши свет в гостиной до 35 процентов', 'calls': [{'name': 'control_lights', 'arguments': {'room': 'гостиная', 'action': 'приглушить', 'brightness_percent': 35}}], 'category': 'positive'},
    {'query': 'включи свет в кабинете на теплый белый', 'calls': [{'name': 'control_lights', 'arguments': {'room': 'кабинет', 'action': 'включить', 'color': 'теплый белый'}}], 'category': 'positive'},
    {'query': 'включи синий свет в спальне', 'calls': [{'name': 'control_lights', 'arguments': {'room': 'спальня', 'action': 'включить', 'color': 'синий'}}], 'category': 'positive'},
    {'query': 'поставь термостат на 22 градуса', 'calls': [{'name': 'set_thermostat', 'arguments': {'temperature': 22}}], 'category': 'positive'},
    {'query': 'нагрей дом до 24 градусов', 'calls': [{'name': 'set_thermostat', 'arguments': {'temperature': 24}}], 'category': 'positive'},
    {'query': 'охлади весь дом до 19 градусов', 'calls': [{'name': 'set_thermostat', 'arguments': {'temperature': 19}}], 'category': 'positive'},
    {'query': 'включи вентилятор в спальне', 'calls': [{'name': 'control_fan', 'arguments': {'room': 'спальня', 'action': 'включить'}}], 'category': 'positive'},
    {'query': 'выключи вентилятор в кабинете', 'calls': [{'name': 'control_fan', 'arguments': {'room': 'кабинет', 'action': 'выключить'}}], 'category': 'positive'},
    {'query': 'включи вентилятор в гостиной на высокую скорость', 'calls': [{'name': 'control_fan', 'arguments': {'room': 'гостиная', 'action': 'включить', 'speed': 'высокая'}}], 'category': 'positive'},
    {'query': 'запусти вентилятор в кабинете на низкой скорости', 'calls': [{'name': 'control_fan', 'arguments': {'room': 'кабинет', 'action': 'включить', 'speed': 'низкая'}}], 'category': 'positive'},
    {'query': 'открой жалюзи на кухне', 'calls': [{'name': 'control_blinds', 'arguments': {'room': 'кухня', 'action': 'открыть'}}], 'category': 'positive'},
    {'query': 'закрой жалюзи в гостиной', 'calls': [{'name': 'control_blinds', 'arguments': {'room': 'гостиная', 'action': 'закрыть'}}], 'category': 'positive'},
    {'query': 'открой жалюзи в спальне', 'calls': [{'name': 'control_blinds', 'arguments': {'room': 'спальня', 'action': 'открыть'}}], 'category': 'positive'},
    {'query': 'запусти робот-пылесос', 'calls': [{'name': 'start_robot_vacuum', 'arguments': {'action': 'старт'}}], 'category': 'positive'},
    {'query': 'начни пылесосить спальню', 'calls': [{'name': 'start_robot_vacuum', 'arguments': {'action': 'старт', 'room': 'спальня'}}], 'category': 'positive'},
    {'query': 'останови робот-пылесос', 'calls': [{'name': 'start_robot_vacuum', 'arguments': {'action': 'стоп'}}], 'category': 'positive'},
    {'query': 'включи свет', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'поставь термостат на что-то комфортное', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'открой жалюзи', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'включи вентилятор', 'calls': [], 'category': 'missing', 'critical': True},
    {'query': 'запри заднюю дверь', 'calls': [], 'category': 'irrelevant'},
    {'query': 'проверь, заряжается ли робот-пылесос', 'calls': [], 'category': 'irrelevant'},
    {'query': 'включи немного джаза в гостиной', 'calls': [], 'category': 'irrelevant'},
    {'query': 'не включай свет в кабинете', 'calls': [], 'category': 'negation', 'critical': True},
    {'query': 'не закрывай жалюзи в гостиной', 'calls': [], 'category': 'negation', 'critical': True},
    {'query': 'никогда не запускай пылесос, пока я на звонке', 'calls': [], 'category': 'negation', 'critical': True},
    {'query': 'приглуши свет в спальне до 150 процентов', 'calls': [], 'category': 'invalid', 'critical': True},
    {'query': 'поставь термостат на 40 градусов', 'calls': [], 'category': 'invalid', 'critical': True},
    {'query': 'выключи свет в спальне и поставь термостат на 18 градусов', 'calls': [{'name': 'control_lights', 'arguments': {'room': 'спальня', 'action': 'выключить'}}, {'name': 'set_thermostat', 'arguments': {'temperature': 18}}], 'category': 'parallel'},
    {'query': 'запусти пылесос на кухне и открой жалюзи в гостиной', 'calls': [{'name': 'start_robot_vacuum', 'arguments': {'action': 'старт', 'room': 'кухня'}}, {'name': 'control_blinds', 'arguments': {'room': 'гостиная', 'action': 'открыть'}}], 'category': 'parallel'},
]


def run_tests(min_confidence=0.0, verbose=True):
    return _harness.run_tests(sys.modules[__name__], min_confidence, verbose)


def __getattr__(name):
    if name == "agent":
        return _harness.agent_for(sys.modules[__name__])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
