from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import AutoPylon, ProtossUnit, RestorePower, ChronoUnit
from sharpy.plans.require import UnitExists, Gas, UnitReady, SupplyLeft, Time, Count, All, TechReady
from sharpy.plans.tactics import PlanZoneDefense, DistributeWorkers, PlanZoneGather, PlanZoneAttack, PlanFinishEnemy


class MacroStalkers(KnowledgeBot):
    def __init__(self):
        super().__init__("Sharp Spiders")

    async def create_plan(self) -> BuildOrder:
        return BuildOrder(
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 40, include_pending=True),
                skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
            ),

            SequentialList(
                Step(
                    UnitExists(UnitTypeId.PYLON, 0), GridBuilding(UnitTypeId.PYLON), skip_until=Time(16)
                ),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                BuildGas(2),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                BuildOrder(
                    GridBuilding(UnitTypeId.GATEWAY, 3),
                    Step(TechReady(UpgradeId.WARPGATERESEARCH, 1), Expand(2), skip_until=Time(122))
                ),
                Step(None, GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1), skip_until=Time(206)),
                BuildOrder(
                    GridBuilding(UnitTypeId.STARGATE, 2),
                    BuildGas(3),
                    GridBuilding(UnitTypeId.GATEWAY, 5),
                ),
                BuildOrder(
                    GridBuilding(UnitTypeId.FORGE),
                    BuildGas(4),
                ),
                Expand(3),
                Step(None, GridBuilding(UnitTypeId.GATEWAY, 7), skip_until=Time(382)),
                GridBuilding(UnitTypeId.FORGE, 2),
                BuildGas(6),
                GridBuilding(UnitTypeId.FLEETBEACON, 1),
                GridBuilding(UnitTypeId.STARGATE, 3),
                Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL1),
                Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL2),
            ),

            # Early Game Units
            BuildOrder(
                make_fighty_thing(1)
            ),

            # Mid Game Units
            BuildOrder(
                make_fighty_thing(3)
            ),

            # Generate Overall Army
            BuildOrder(
                AutoPylon(),
                make_fighty_thing(5)
            ),

            # Max Out
            BuildOrder(
                AutoPylon(),
                make_fighty_thing(7)
            ),

            # Unit Upgrades
            BuildOrder(
                Step(
                    None, ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), skip=TechReady(UpgradeId.WARPGATERESEARCH, 100), skip_until=TechReady(UpgradeId.WARPGATERESEARCH, 1)
                ),
                Step(
                    None, Tech(UpgradeId.WARPGATERESEARCH), skip_until=UnitReady(UnitTypeId.CYBERNETICSCORE)
                ),
            ),
            Step(
                UnitExists(UnitTypeId.STALKER, 4), Tech(UpgradeId.BLINKTECH), skip_until=UnitReady(UnitTypeId.TWILIGHTCOUNCIL)
            ),

            # Probe Creation
            BuildOrder(
                AutoPylon(),
                Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16), skip_until=UnitReady(UnitTypeId.NEXUS, 1)),
                Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                     skip_until=All(
                        UnitReady(UnitTypeId.NEXUS, 1), UnitReady(UnitTypeId.ASSIMILATOR, 2)
                     )),
                Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 32), skip_until=UnitReady(UnitTypeId.NEXUS, 2)),
                Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 38),
                     skip_until=All(
                        UnitReady(UnitTypeId.NEXUS, 2), UnitReady(UnitTypeId.ASSIMILATOR, 4)
                     )),
                Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 48), skip_until=UnitReady(UnitTypeId.NEXUS, 3)),
                Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 54),
                     skip_until=All(
                        UnitReady(UnitTypeId.NEXUS, 3), UnitReady(UnitTypeId.ASSIMILATOR, 6)
                     )),
            ),

            # Forge Upgrades
            SequentialList(
                # Weapons
                Step(None,
                     Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
                Step(None,
                     Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
                     skip_until=All(
                         UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                         TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, 1)
                     )),
                Step(None,
                     Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3),
                     skip_until=All(
                         UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                         TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, 1)
                     )),

                # Armor
                Step(UnitReady(UnitTypeId.FORGE, 1),
                     Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)),
                Step(None,
                     Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                     skip_until=All(
                         UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                         TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)
                     )),
                Step(None,
                     Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
                     skip_until=All(
                         UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                         TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL2, 1)
                     )),

                # Shields
                Step(UnitReady(UnitTypeId.FORGE, 1),
                     Tech(UpgradeId.PROTOSSSHIELDSLEVEL1)),
                Step(None,
                     Tech(UpgradeId.PROTOSSSHIELDSLEVEL2),
                     skip_until=All(
                         UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                         TechReady(UpgradeId.PROTOSSSHIELDSLEVEL1, 1)
                     )),
                Step(None,
                     Tech(UpgradeId.PROTOSSSHIELDSLEVEL3),
                     skip_until=All(
                         UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                         TechReady(UpgradeId.PROTOSSSHIELDSLEVEL2, 1)
                     ))
            ),

            # Overall Plan
            SequentialList(
                PlanZoneDefense(),
                RestorePower(),
                DistributeWorkers(),
                PlanZoneGather(),
                Step(UnitReady(UnitTypeId.GATEWAY, 4), PlanZoneAttack(4)),
                Step(UnitReady(UnitTypeId.STARGATE, 2), PlanZoneAttack(50),
                     skip_until=Count(5, [UnitExists(UnitTypeId.PHOENIX)])),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(MacroStalkers):
    @property
    def my_race(self):
        return Race.Protoss


def make_fighty_thing(count):
    b = BuildOrder(
    Step(
        UnitExists(UnitTypeId.GATEWAY, count), ProtossUnit(UnitTypeId.STALKER, 2 * count)
    ),

    Step(
        UnitExists(UnitTypeId.GATEWAY, count), ProtossUnit(UnitTypeId.SENTRY, 2),
        skip_until=TechReady(UpgradeId.WARPGATERESEARCH, 1)
    ),

    Step(UnitReady(UnitTypeId.STARGATE, 1), ProtossUnit(UnitTypeId.PHOENIX, count))
    )
    return b
