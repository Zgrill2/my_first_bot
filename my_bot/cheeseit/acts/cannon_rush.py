from typing import Optional

from sharpy.interfaces import ICombatManager, IZoneManager
from sharpy.knowledges import Knowledge
from sharpy.plans.acts import ActBase
from sc2.unit import Unit
from sc2.units import Units
from sc2 import UnitTypeId, AbilityId
from sharpy.managers.core.roles import UnitTask

from typing import List
from loguru import logger


class CannonRush(ActBase):
    """
    Very old code, you probably don't want to use this for anything
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self):
        super().__init__()

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.combat = knowledge.get_required_manager(ICombatManager)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    async def execute(self) -> bool:
        return True
