from typing import Dict, Callable

from loguru import logger

from acts.defend_natural import DefendNatural
from acts.generic_drop import GenericWarpPrismDrop
from managers.build_manager import BuildSelector
from managers.dynamic_build_logic import DynamicBuildLogic
from sharpy.interfaces import IBuildingSolver
from sharpy.managers import ManagerBase
from sharpy.managers.core.building_solver import WallType
from sharpy.plans.protoss import *
from sc2 import UnitTypeId, Race

from acts.void_rush import VoidRayRush


class TacticsSelector(ManagerBase):
    dyanamic_updater: DynamicBuildLogic
    building_solver: IBuildingSolver
    building_selector: BuildSelector

    def __init__(self, build_name: str):
        super().__init__()
        self.tacts: Dict[str, Callable[[], BuildOrder]] = {
            "void_rush": lambda: self.void_ray_tacts(),
            "dt_drop": lambda: self.dark_templar_tacts(),
            "cannon_rush": lambda: self.cannon_rush_tacts(),
            "macro_up": lambda: self.macro_tacts(),
            "zerg_def": lambda: self.zerg_defense_tacts(),
            "standard_opening_build": lambda: self.standard_opening_build(),
            "macro_mid_game": lambda: self.macro_mid_game(),
            "macro_no_expand_mid_game": lambda : self.macro_no_expand_mid_game()
        }

        self.dynamic = not build_name == "default"
        if self.dynamic:
            assert build_name in self.tacts.keys()
            self.response = build_name
        else:
            self.response = "default"

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.dyanamic_updater = self.knowledge.get_required_manager(DynamicBuildLogic)
        self.building_solver = self.knowledge.get_required_manager(IBuildingSolver)
        self.building_selector = self.knowledge.get_required_manager(BuildSelector)

    async def update(self):
        if not self.dynamic:
            logger.info("RIP")
            return
        self.response = self.building_selector.response

    async def post_update(self):
        pass

    def standard_opening_build(self) -> BuildOrder:
        scout = DoubleAdeptScout()
        adept_harass = BuildOrder(
            [ProtossUnit(UnitTypeId.ADEPT, 2, priority=True), scout]
        )
        return BuildOrder([adept_harass])

    def macro_mid_game(self) -> BuildOrder:
        attack = PlanZoneAttack(60)
        attack.retreat_multiplier = 0.5  # All in
        scout = DoubleAdeptScout()
        adept_harass = BuildOrder(
            [ProtossUnit(UnitTypeId.ADEPT, 2, priority=True), scout]
        )
        return BuildOrder(
            [adept_harass, attack]
        )

    def macro_no_expand_mid_game(self) -> BuildOrder:
        attack = PlanZoneAttack(40)
        attack.retreat_multiplier = 0.5  # All in
        return BuildOrder(
            [attack]
        )

    def void_ray_tacts(self) -> BuildOrder:
        attack = PlanZoneAttack(30)
        attack.retreat_multiplier = 0.5
        void_rush = Step(None, VoidRayRush(), None,
                         skip_until=UnitExists(UnitTypeId.STARGATE, include_pending=True, include_not_ready=True))

        return BuildOrder([void_rush, attack])

    def zerg_defense_tacts(self) -> BuildOrder:
        """
        Dont proxy
        Full wall at natural
        Expand
        Battery behind wall
        Zealot defend
        Adept then stalker behind zealot
        Once this is complete, switch to macro build
        """
        self.building_solver.wall_type = WallType.ProtossNaturalOneUnit

        attack = PlanZoneAttack(40)
        attack.retreat_multiplier = 0.5  # All in
        return BuildOrder(
            [attack]
        )

    def bunker_defense_tacts(self) -> BuildOrder:
        """
        Dont proxy
        Go 2 gate
        Focus SCV
        If bunker gets completed: immortals to bunker bust
        If bunker is destroyed: group stalker zealot and go for the rax
        Once complete, switch to macro build
        """

        attack = PlanZoneAttack(40)
        attack.retreat_multiplier = 0.5  # All in
        return BuildOrder(
            [attack]
        )
        pass

    def dark_templar_tacts(self) -> BuildOrder:

        attack = PlanZoneAttack(30)
        attack.retreat_multiplier = 0.5  # All in
        return BuildOrder(
            [GenericWarpPrismDrop(UnitTypeId.DARKTEMPLAR, 2), attack]
        )

    def cannon_rush_tacts(self) -> BuildOrder:

        attack = PlanZoneAttack(30)
        attack.retreat_multiplier = 0.5  # All in
        return BuildOrder(
            [attack]
        )

    def macro_tacts(self):
        attack = PlanZoneAttack(60)
        attack.retreat_multiplier = 0.5  # All in

        return BuildOrder(
           [attack]
        )