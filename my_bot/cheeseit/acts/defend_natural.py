from typing import Optional

from sharpy.general.extended_power import ExtendedPower
from sharpy.interfaces import ICombatManager, IZoneManager
from sharpy.interfaces.combat_manager import MoveType
from sharpy.knowledges import Knowledge
from sharpy.plans.acts import ActBase
from sc2.unit import Unit
from sc2.units import Units
from sc2 import UnitTypeId, AbilityId, Race
from sharpy.managers.core.roles import UnitTask

from typing import List
from loguru import logger

from sharpy.plans.tactics import PlanZoneDefense


class DefendNatural(ActBase):
    """
    Very old code, you probably don't want to use this for anything
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self):
        # initializing parameters of the drop (what unit are we dropping, how many. i.e. 2 archons, 2 DT, 4 zealot, etc)
        super().__init__()
        # tags to reference specific units being used in the drop

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)

    async def execute(self) -> bool:
        unit: Unit

        sls = self.cache.own(UnitTypeId.STALKER).ready
        ads = self.cache.own(UnitTypeId.ADEPT).ready
        sts = self.cache.own(UnitTypeId.SENTRY).ready
        for u in sls+ads+sts:
            self.roles.set_task(UnitTask.Defending, u)
        return True
