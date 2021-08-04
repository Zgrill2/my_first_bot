from typing import Optional, List

from acts.defend_natural import DefendNatural
from managers.build_manager import BuildSelector
from managers.dynamic_build_logic import DynamicBuildLogic
from sharpy.managers import ManagerBase
from sharpy.managers.core.building_solver import WallType
from sharpy.knowledges import KnowledgeBot
from sharpy.plans.protoss import *
from sc2 import UnitTypeId, Race
from managers.tactics_manager import TacticsSelector


class CheeseIt(KnowledgeBot, ):
    dyanamic_updater: DynamicBuildLogic

    def __init__(self, build_name: str = "default"):
        super().__init__("Z's Cheese")
        self.build_name = build_name
        self.build_selector = BuildSelector(build_name)
        self.tactics_selector = TacticsSelector(build_name)
        self.dyanamic_updater = DynamicBuildLogic()

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        return [self.build_selector, self.tactics_selector, self.dyanamic_updater]

    async def create_plan(self) -> BuildOrder:
        builds = []
        for key, build_order_call in self.build_selector.builds.items():
            builds.append(Step(None, build_order_call(),
                               skip_until=lambda k, key=key: self.build_selector.response == key))
        tacts = []
        for key, build_order_call in self.tactics_selector.tacts.items():
            tacts.append(Step(None, build_order_call(),
                               skip_until=lambda k, key=key: self.tactics_selector.response == key))

        self.building_solver.wall_type = WallType.ProtossNaturalOneUnit

        attack = PlanZoneAttack(60)
        attack.retreat_multiplier = 0.5  # All in

        # scout main base
        scout = Step(None, WorkerScout(), None,
                     skip_until=UnitExists(UnitTypeId.PYLON, include_pending=True, include_not_ready=True))

        tactics = [
            BuildOrder(
            PlanCancelBuilding(),
            PlanZoneDefense(),
            RestorePower(),
            DistributeWorkers(),
            SpeedMining(),
            scout,
            PlanZoneGather(),)
            #attack,
            #PlanFinishEnemy()
        ]
        tactics += tacts
        tactics.append(PlanFinishEnemy())
        return BuildOrder(builds, tactics)


class LadderBot(CheeseIt):
    @property
    def my_race(self):
        return Race.Protoss
