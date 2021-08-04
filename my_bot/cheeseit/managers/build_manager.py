from typing import Dict, Callable

from loguru import logger

from acts.void_rush import ProxyStarBattery
from managers.dynamic_build_logic import DynamicBuildLogic
from sharpy.managers.core.roles import UnitTask
from sharpy.interfaces import IBuildingSolver
from sharpy.managers import ManagerBase
from sharpy.managers.core.building_solver import WallType
from acts.proxy_warp import ProxyWarpUnit
from sharpy.plans import Step, SequentialList, StepBuildGas
from sharpy.plans.acts import ActBuilding, ActUnit, GridBuilding, Expand, BuildGas, Tech
from sharpy.plans.acts.protoss import ChronoUnit, ChronoAnyTech, AutoPylon, DefensiveCannons, ProtossUnit, ArtosisPylon, \
    ChronoTech, Archon
from sharpy.plans.protoss import BuildOrder
from sc2 import UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId

from acts.void_rush import VoidRayRush
from sharpy.plans.require import UnitExists, Supply, Minerals, UnitReady, All, TechReady, RequireCustom, Gas, SupplyType


class BuildSelector(ManagerBase):
    dyanamic_updater: DynamicBuildLogic
    building_solver: IBuildingSolver

    def __init__(self, build_name: str):
        super().__init__()
        self.builds: Dict[str, Callable[[], BuildOrder]] = {
            "void_rush": lambda: self.void_ray_build(),
            "dt_drop": lambda: self.dark_templar_build(),
            "cannon_rush": lambda: self.cannon_rush_build(),
            "macro_up": lambda: self.macro_build(),
            "zerg_def": lambda: self.zerg_defense_build(),
            "standard_opening_build": lambda: self.standard_opening_build(),
            "macro_mid_game": lambda: self.macro_mid_game(),
            "macro_no_expand_mid_game": lambda: self.macro_no_expand_mid_game()
        }
        self.phase = 0  # 0 is early, 1 is mid, 2 is late
        self.cheese = True
        self.dynamic = not build_name == "default"
        if self.dynamic:
            assert build_name in self.builds.keys()
            self.response = build_name
        else:
            self.response = "default"

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.dyanamic_updater = self.knowledge.get_required_manager(DynamicBuildLogic)
        self.building_solver = self.knowledge.get_required_manager(IBuildingSolver)

    async def update(self):
        if not self.dynamic:
            logger.info("RIP")
            return
        if self.phase == 0:
            self.response = "standard_opening_build"
            if self.cache.own(UnitTypeId.CYBERNETICSCORE):
                if self.enemy_is_cheesing():
                    self.cheese = False
                self.phase = 1
        elif self.phase == 1:
            if self.cheese:
                self.response = "void_rush"
            else:
                self.response = "macro_mid_game"
            if self.is_cheese_over():  # or is_mid_game_over() (is this needed or is macro_mid_game enough to win)
                self.phase = 2
        elif self.phase == 2:
            if self.cheese:
                self.response = "macro_no_expand_mid_game"
                self.cheese = False
            if not self.cheese and len(self.cache.own(UnitTypeId.NEXUS)) > 1:
                self.response = "macro_mid_game"

        """
        if self.response == "void_rush":
            # if conditional for we shouldnt void rush anymore, change builds

            # if opponent is zerg and we see pool built before x minutes or our stargate is dead
            # start zerg_defense_build()
            if self.ai.enemy_race == Race.Zerg:
                if 30 < self.ai.time < 240:
                    # if zerg goes pool first
                    if self.ai.enemy_race == Race.Zerg:#self.cache.enemy(UnitTypeId.SPAWNINGPOOL) and len(self.cache.enemy_townhalls) < 2:
                        logger.info("SWITCHING TO ZERG RUSH DEFENSE BUILD")
                        self.response = 'zerg_def'
                    if len(self.cache.enemy(UnitTypeId.ZERGLING)) > 8:
                        self.response = 'zerg_def'


            # if opponent is terran
            #       if bunker rush:
            #           start bunker_defense_build()

            # if rush fails
            #   macro + disruptors
            # fail defined as: any 2 of (stargate not powered, 2-3 void rays dead, < 2 voids in play, non zerg opponent has 2 bases,
            switch_toggle = 0

            for sg in self.cache.own(UnitTypeId.STARGATE):
                if not sg.is_powered:
                    switch_toggle += 1

            # change this to if we have made 3+ voids and 50% or more are dead
            if self.dyanamic_updater.get_killed_units(UnitTypeId.VOIDRAY) > 3:
                switch_toggle += 1
                if len(self.cache.own(UnitTypeId.VOIDRAY)) < 2:
                    switch_toggle += 1

            if len(self.cache.enemy_townhalls) > 1 and self.ai.enemy_race != Race.Zerg:
                switch_toggle += 1

            if switch_toggle > 2:
                self.response = "macro_up"

        if self.ai.time > 5.5 * 60:
            self.response = 'macro_up'
        """

        """
        Flow Chart:
            Standard Opening
            Scout for info
            Cheese Picker 9000
                One Base DT Adept all in
                Void Ray Proxy Rush
                Cannon Rush the natural
            If cheese failed
                Macro all-in disruptors + blink stalker
            If cheese succeeded (how do we determine this?)
                Do we have an army
                    Yes (parameters for said army?)
                        Search and destroy, maintain unit production
                    No (or not a big one)
                        Do we have production buildings?
                            No - macro all-in disruptor blink stalker
                            Yes - Search and Destroy, maintain unit production
        """

        """
        Breaking the Flow Chart Down
            Standard Opening
                14 Pylon
                16 Gate
                17 gas
                20 Cyber
            
            Scouting for Info
                Obtain the scouts unit tag to track them, when they died, etc
                    Based on info coming in, scout should be dynamically sent to different scouting locations
                        Zerg 
                            no main at natural and no pool
                                check the third for a base
                                    if no third, check near us for proxy hatch
                            pool timings calculations
                                Should be done in conjunction with the natural timings
                                f(pt, nht) -> cheese predicted
                                    pt = pool timing, nht = natural hatch timing
                        Toss
                            Just go Void Ray Rush lol
                        Terr
                            reactor on barracks? more than 1 barracks in main?
                                marines all-in predicted
                            No barracks in main
                                cheese predicted
                                    scout - if reaper, shield battery in mineral line, make stalker
                                            if marines, zealot battery at natural entrance, make stalkers
            
            Deciding on a cheese
                For now - Void Rush only
                If we are not cheesing (marine or ling rush incoming) go to "cheese failed"
                
            Did it succeed?
                Failure/success conditions
            
            Cheese Failed
                Macro stalker disruptor build
                    Two versions of the build:
                        Expand
                            This one will get used earlier in the game if we are being cheesed
                                Build:
                                    20 nexus
                                    20 2nd gas
                                    30 robo
                                    30 2 gate
                                    68 twilight
                                    72 2 gas
                                    74 blink
                                    78 nexus
                                    78 forge
                                    88 3 gate
                                    92 robo bay
                                    119 2 gas
                                Army info:
                                    can do 2 adept scout harass early game
                                    mono stalkers at 24
                                    immortals out of robo until bay is ready then disruptors (chrono robo units)
                                    at 2-3 disruptors push out and attack
                        No Expand
                            This one will get used later in the game if our cheese failed
                                Build:
                                    21 2nd gas
                                    30 robo
                                    30 2 gate
                                    35 twlight (blink asap)
                                    46 robo bay
                                Army Info
                                    mono stalkers at 24
                                    immortals out of robo until bay is ready then disruptors (chrono robo units)
                                    
            Combinding Builds:
                Standard Opening Build (exists alone)
                
                adept_harassment_scouting (idk yet)
                
                macro_blink_stalker_disruptor_expansion_build + macro_blink_stalker_disruptor_units_build
                macro_blink_stalker_disruptor_no_expand_build + macro_blink_stalker_disruptor_units_build
        """

    pass

    def is_cheese_over(self):
        stargates_killed = self.dyanamic_updater.get_killed_units(UnitTypeId.STARGATE)
        if stargates_killed > 0:
            return True
        pylons_killed = self.dyanamic_updater.get_killed_units(UnitTypeId.PYLON)
        if pylons_killed > 1:
            return True
        if self.ai.time > 4.5 * 60 and len(self.cache.own(UnitTypeId.STARGATE)) < 1:
            return True
        if self.ai.time > 6 * 60:
            return True
        return False

    def enemy_is_cheesing(self):
        if self.ai.enemy_race == Race.Zerg:
            if (len(self.cache.enemy(UnitTypeId.DRONE).ready) < 15 or len(
                    self.cache.enemy(UnitTypeId.ZERGLING)) > 5) and self.cache.enemy(UnitTypeId.SPAWNINGPOOL):
                return True
        if self.ai.enemy_race == Race.Terran:
            if 2 < len(self.cache.enemy(UnitTypeId.BARRACKS)) or len(self.cache.enemy(UnitTypeId.BARRACKS)) < 1:
                return True
        return False

    def standard_opening_build(self) -> BuildOrder:
        build_steps_chrono = [
            Step(None, ChronoTech(AbilityId.RESEARCH_WARPGATE, UnitTypeId.CYBERNETICSCORE)),
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 19),
            ),
            ChronoAnyTech(0),
        ]
        opening_buildings = [
            Step(Supply(14), GridBuilding(UnitTypeId.PYLON)),
            Step(Supply(16), GridBuilding(UnitTypeId.GATEWAY, 1)),
            Step(Supply(17), BuildGas(1)),
            Step(Supply(20), GridBuilding(UnitTypeId.CYBERNETICSCORE, 1), None, None)
        ]
        build_steps_workers = [
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 3)), ]
        opening_units = BuildOrder(ProtossUnit(UnitTypeId.ZEALOT), AutoPylon())
        return BuildOrder(opening_buildings, opening_units, build_steps_workers, build_steps_chrono)

    def macro_mid_game(self) -> BuildOrder:
        return BuildOrder(self.macro_blink_stalker_disruptor_expansion_build(),
                          self.macro_blink_stalker_disruptor_units_build())

    def macro_no_expand_mid_game(self) -> BuildOrder:
        return BuildOrder(self.macro_blink_stalker_disruptor_no_expand_build(),
                          self.macro_blink_stalker_disruptor_units_build())

    def macro_blink_stalker_disruptor_no_expand_build(self) -> BuildOrder:
        build_steps_workers = [
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 6)), ]
        buildings = [
            BuildOrder(
                Step(None, BuildGas(2)),
            ),
            BuildOrder(
                Step(None, GridBuilding(UnitTypeId.ROBOTICSFACILITY, 1)),
                Step(None, GridBuilding(UnitTypeId.GATEWAY, 3)),
            ),
            Step(None, GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)),
            Step(None, GridBuilding(UnitTypeId.ROBOTICSBAY, 1)),
            Step(Minerals(600), Expand(2)),
        ]
        pylons = BuildOrder(AutoPylon())
        tech = [Step(UnitReady(UnitTypeId.CYBERNETICSCORE), Tech(UpgradeId.WARPGATERESEARCH), None, None),
                BuildOrder(Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL), Tech(UpgradeId.BLINKTECH)),
                           Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL), Tech(UpgradeId.CHARGE),
                                skip_until=UnitExists(UnitTypeId.ZEALOT, 8))
                           ),
                Step(UnitReady(UnitTypeId.FORGE), Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)), ]
        excess_mineral_production = BuildOrder(Step(Minerals(800), GridBuilding(UnitTypeId.GATEWAY)),
                                               Step(Minerals(800), ProtossUnit(UnitTypeId.ZEALOT)))

        build_steps_chrono = [
            ChronoTech(AbilityId.RESEARCH_WARPGATE, UnitTypeId.CYBERNETICSCORE),
            ChronoUnit(UnitTypeId.DISRUPTOR, UnitTypeId.ROBOTICSFACILITY),
            ChronoUnit(UnitTypeId.COLOSSUS, UnitTypeId.ROBOTICSFACILITY),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY),
            ChronoAnyTech(0),
        ]
        return BuildOrder(build_steps_workers, buildings, pylons, tech, excess_mineral_production, build_steps_chrono)

    def macro_blink_stalker_disruptor_expansion_build(self) -> BuildOrder:
        build_steps_workers = [
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (16 * 2) + (3 * 6))),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (16 * 2) + (4 * 6)),
                 skip_until=UnitExists(UnitTypeId.NEXUS, 2, include_pending=True, include_not_ready=True)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (16 * 3) + (6 * 6)),
                 skip_until=UnitExists(UnitTypeId.NEXUS, 3, include_pending=True, include_not_ready=True)),
        ]

        buildings = [
            BuildOrder(
                Step(None, GridBuilding(UnitTypeId.GATEWAY, 2)),
                Step(None, Expand(2), skip=UnitExists(UnitTypeId.NEXUS, 2)),
                Step(None, BuildGas(2)),
            ),
            BuildOrder(
                Step(None, GridBuilding(UnitTypeId.ROBOTICSFACILITY, 1)),
                Step(None, GridBuilding(UnitTypeId.GATEWAY, 3)),
            ),
            Step(None, GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1), skip_until=All(UnitReady(UnitTypeId.GATEWAY, 3), Supply(25, SupplyType.Combat))),
            BuildGas(4),
            Step(None, GridBuilding(UnitTypeId.ROBOTICSBAY, 1), skip_until=All(UnitReady(UnitTypeId.ROBOTICSFACILITY, 1), Supply(35, SupplyType.Combat))),
            BuildOrder(
                Step(Supply(78), Expand(3)),
                Step(None, GridBuilding(UnitTypeId.ROBOTICSFACILITY, 2), skip_until=UnitExists(UnitTypeId.NEXUS, 3, include_pending=True, include_not_ready=True)),
                Step(None, GridBuilding(UnitTypeId.FORGE, 2), skip_until=UnitExists(UnitTypeId.NEXUS, 3, include_pending=True, include_not_ready=True)),
            ),
            Step(UnitExists(UnitTypeId.NEXUS, 3), GridBuilding(UnitTypeId.GATEWAY, 7), skip_until=Supply(80, SupplyType.Workers)),  # maybe this should trigger based on probe count?
            BuildGas(6)
        ]

        tech = [Step(UnitReady(UnitTypeId.CYBERNETICSCORE), Tech(UpgradeId.WARPGATERESEARCH), None, None),
                BuildOrder(Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL), Tech(UpgradeId.BLINKTECH)),
                           Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL), Tech(UpgradeId.CHARGE),
                                skip_until=UnitExists(UnitTypeId.ZEALOT, 8))
                           ),
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
                    Step(UnitReady(UnitTypeId.FORGE, 1),
                         Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                         skip_until=All(
                             UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                             TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)
                         )),
                    Step(UnitReady(UnitTypeId.FORGE, 1),
                         Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
                         skip_until=All(
                             UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                             TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)), ),
                )
                ]

        excess_mineral_production = BuildOrder(Step(Minerals(800), GridBuilding(UnitTypeId.GATEWAY)),
                                               Step(Minerals(800), ProtossUnit(UnitTypeId.ZEALOT)))

        build_steps_chrono = [
            ChronoTech(AbilityId.RESEARCH_WARPGATE, UnitTypeId.CYBERNETICSCORE),
            ChronoUnit(UnitTypeId.DISRUPTOR, UnitTypeId.ROBOTICSFACILITY),
            ChronoUnit(UnitTypeId.COLOSSUS, UnitTypeId.ROBOTICSFACILITY),
            ChronoUnit(UnitTypeId.IMMORTAL, UnitTypeId.ROBOTICSFACILITY),
            ChronoAnyTech(0),
        ]

        pylons = BuildOrder(AutoPylon())
        return BuildOrder(buildings, build_steps_workers, pylons, tech, build_steps_chrono, excess_mineral_production)

    def macro_blink_stalker_disruptor_units_build(self) -> BuildOrder:
        units = BuildOrder(
            Step(Gas(600), ProtossUnit(UnitTypeId.SENTRY)),
            ProtossUnit(UnitTypeId.OBSERVER, 1, priority=True),
            ProtossUnit(UnitTypeId.WARPPRISM, 1, priority=True),
            Step(None, ProtossUnit(UnitTypeId.ZEALOT, 1, priority=True), skip=UnitExists(UnitTypeId.NEXUS, 3)),
            ProtossUnit(UnitTypeId.COLOSSUS, 2, priority=True),
            ProtossUnit(UnitTypeId.DISRUPTOR, 3, priority=True),
            Step(None, ProtossUnit(UnitTypeId.IMMORTAL, priority=True), skip=UnitExists(UnitTypeId.ROBOTICSBAY)),
            Step(UnitExists(UnitTypeId.ROBOTICSBAY, include_pending=True), ProtossUnit(UnitTypeId.ZEALOT, 8)),
            Step(TechReady(UpgradeId.CHARGE), ProtossUnit(UnitTypeId.ZEALOT)),
            ProtossUnit(UnitTypeId.SENTRY, 1),
            ProtossUnit(UnitTypeId.STALKER),
            ProtossUnit(UnitTypeId.IMMORTAL)
        )
        return units

    async def post_update(self):
        pass

    def zerg_defense_build(self) -> BuildOrder:
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

        build_steps_chrono = [
            Step(
                None,
                ChronoUnit(UnitTypeId.ZEALOT, UnitTypeId.GATEWAY),
                skip=UnitExists(UnitTypeId.ZEALOT, 1),
            ),
            Step(
                None,
                ChronoUnit(UnitTypeId.ADEPT, UnitTypeId.GATEWAY),
                skip=UnitExists(UnitTypeId.ADEPT, 1),
            ),
            Step(
                None,
                ChronoUnit(UnitTypeId.STALKER, UnitTypeId.GATEWAY),
                skip=UnitExists(UnitTypeId.STALKER, 1),
            ),
            ChronoAnyTech(0),
        ]

        build_steps_workers = [
            Step(None, GridBuilding(UnitTypeId.NEXUS, 1), UnitExists(UnitTypeId.NEXUS, 1)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 14)),
            Step(None, None, UnitExists(UnitTypeId.PYLON, 1)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 4)),
            Step(None, GridBuilding(UnitTypeId.PYLON, 3)),
            Step(Supply(20), Expand(2)),
            BuildGas(3),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 44)),
            BuildGas(4),
            AutoPylon(),
            Step(Minerals(600), Expand(3)),
            Step(None, DefensiveCannons(1, 1, 2)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 60)),
            AutoPylon(),
        ]

        build_step_buildings = [
            Step(Supply(16), GridBuilding(UnitTypeId.GATEWAY, 1)),
            Step(Supply(20), GridBuilding(UnitTypeId.CYBERNETICSCORE, 1), None, None),
            Step(None, GridBuilding(UnitTypeId.GATEWAY, 2)),
            Step(UnitExists(UnitTypeId.CYBERNETICSCORE), Tech(UpgradeId.WARPGATERESEARCH), None, None),
            Step(None, GridBuilding(UnitTypeId.FORGE, 1)),
            Step(None, GridBuilding(UnitTypeId.GATEWAY, 3)),
            Step(None, DefensiveCannons(1, 1, 1), None, None),
            AutoPylon()
            # Step(None, GridBuilding(UnitTypeId.PHOTONCANNON))
        ]

        build_step_units = [
            Step(None, ProtossUnit(UnitTypeId.ZEALOT, 1), ),
            Step(None, ProtossUnit(UnitTypeId.ZEALOT), skip=UnitReady(UnitTypeId.CYBERNETICSCORE)),
            Step(None, ProtossUnit(UnitTypeId.ADEPT, 1)),
            Step(None, ProtossUnit(UnitTypeId.STALKER, 1)),
            Step(None, ProtossUnit(UnitTypeId.SENTRY, 2)),
            Step(None, ProtossUnit(UnitTypeId.STALKER))
        ]

        builds = [build_step_buildings, build_step_units, build_steps_chrono, build_steps_workers]
        return BuildOrder(builds)

    def bunker_defense_build(self) -> BuildOrder:
        """
        Dont proxy
        Go 2 gate
        Focus SCV
        If bunker gets completed: immortals to bunker bust
        If bunker is destroyed: group stalker zealot and go for the rax
        Once complete, switch to macro build
        """

        pass

    def void_ray_build(self) -> BuildOrder:
        build_steps_chrono = [
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 19),
                skip_until=UnitReady(UnitTypeId.PYLON),
            ),
            Step(
                None,
                ChronoUnit(UnitTypeId.VOIDRAY, UnitTypeId.STARGATE), None,
                skip_until=UnitExists(UnitTypeId.STARGATE, 1),
            ),
            ChronoAnyTech(0),
        ]

        build_steps_workers = [
            Step(None, GridBuilding(UnitTypeId.NEXUS, 1), UnitExists(UnitTypeId.NEXUS, 1)),
            # Build to 14 probes and stop until pylon is building
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 14)),
            # Step(None, None, UnitExists(UnitTypeId.PYLON, 1)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 3 + 3)),
            Step(Minerals(800), Expand(2)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (16*2) + 3 + 3)),
            BuildGas(3),
            Step(None, GridBuilding(UnitTypeId.TWILIGHTCOUNCIL)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (16*2) + (3*3))),
            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL), Tech(UpgradeId.BLINKTECH)),
            GridBuilding(UnitTypeId.GATEWAY, 5),
            BuildGas(4),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (16*2) + (3*4))),
            # GridBuilding(UnitTypeId.GATEWAY, 6),
        ]

        build_steps_buildings = [
            BuildGas(2),
            BuildOrder(
                ProxyStarBattery(),
                Step(All(UnitReady(UnitTypeId.CYBERNETICSCORE, 1)), Tech(UpgradeId.WARPGATERESEARCH)))
        ]
        """
            SequentialList(#Step(Supply(14), GridBuilding(UnitTypeId.PYLON, 1), UnitExists(UnitTypeId.PYLON, 1)),
                           #Step(Supply(16), GridBuilding(UnitTypeId.GATEWAY, 1)),
                           #StepBuildGas(1, Supply(17)),
                           #StepBuildGas(2, Supply(18),
                            #            UnitExists(UnitTypeId.PYLON, 2, include_pending=True, include_not_ready=True)),
                           #Step(Supply(18), GridBuilding(UnitTypeId.PYLON, 2)),
                           #Step(All(UnitReady(UnitTypeId.GATEWAY, 1), Supply(21)),
                           #     GridBuilding(UnitTypeId.CYBERNETICSCORE, 1)),
                
                           Step(None, ProxyStarBattery()), ),
            Step(All(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), Supply(27)), Tech(UpgradeId.WARPGATERESEARCH)),
            ArtosisPylon(2),
            AutoPylon(),
        ]"""

        build_steps_units = [
            SequentialList(Step(
                None,
                ProtossUnit(UnitTypeId.ZEALOT, 1),
                skip=UnitExists(UnitTypeId.ZEALOT, 1, include_pending=True, include_not_ready=True,
                                include_killed=True),
            ),
                Step(
                    None,
                    ProtossUnit(UnitTypeId.STALKER, 1),
                    skip=UnitExists(UnitTypeId.STALKER, 1, include_pending=True, include_not_ready=True,
                                    include_killed=True),
                ), ),
            Step(
                None,
                ProtossUnit(UnitTypeId.VOIDRAY, priority=True), None,
                skip_until=UnitExists(UnitTypeId.STARGATE, 1),
            ),
        ]
        build_steps_units_2 = [
            Step(TechReady(UpgradeId.WARPGATERESEARCH),
                 ProxyWarpUnit(UnitTypeId.STALKER), None, None),
            Step(TechReady(UpgradeId.WARPGATERESEARCH),
                 ProxyWarpUnit(UnitTypeId.ZEALOT), None, None)
        ]

        void_rush = Step(None, VoidRayRush(), None,
                         skip_until=UnitExists(UnitTypeId.STARGATE, include_pending=True, include_not_ready=True))
        pylons = BuildOrder(AutoPylon())
        return BuildOrder(
            build_steps_units,
             build_steps_units_2,
             build_steps_buildings,
             build_steps_workers,
             build_steps_chrono,
            pylons
        )

    def dark_templar_build(self) -> BuildOrder:

        build_steps_workers = [
            Step(None, GridBuilding(UnitTypeId.NEXUS, 1), UnitExists(UnitTypeId.NEXUS, 1)),
            # Build to 14 probes and stop until pylon is building
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 14)),
            Step(None, None, UnitExists(UnitTypeId.PYLON, 1)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 3 + 3)),
            Step(RequireCustom(lambda k: self.zone_manager.own_main_zone.minerals_running_low), Expand(2)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 30)),
            GridBuilding(UnitTypeId.GATEWAY, 5),
            BuildGas(3),
            GridBuilding(UnitTypeId.GATEWAY, 6),
        ]

        return BuildOrder(
            [build_steps_workers]
        )

    def cannon_rush_build(self) -> BuildOrder:

        build_steps_workers = [
            Step(None, GridBuilding(UnitTypeId.NEXUS, 1), UnitExists(UnitTypeId.NEXUS, 1)),
            # Build to 14 probes and stop until pylon is building
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 14)),
            Step(None, None, UnitExists(UnitTypeId.PYLON, 1)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 3 + 3)),
            Step(RequireCustom(lambda k: self.zone_manager.own_main_zone.minerals_running_low), Expand(2)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 30)),
            GridBuilding(UnitTypeId.GATEWAY, 5),
            BuildGas(3),
            GridBuilding(UnitTypeId.GATEWAY, 6),
        ]

        return BuildOrder(
            [build_steps_workers]
        )

    def macro_build(self):
        """
          14	  0:17	  Pylon
          16	  0:38	  Gateway
          17	  0:47	  Assimilator
          20	  1:24	  Nexus
          20	  1:34	  Cybernetics Core
          21	  1:43	  Assimilator
          21	  1:52	  Pylon
          22	  2:01	  Adept
          26	  2:16	  Twilight Council
          26	  2:21	  Warp Gate
          27	  2:31	  Stalker
          35	  3:03	  Robotics Facility
          37	  3:15	  Gateway
          37	  3:17	  Charge
          38	  3:26	  Gateway x2
          43	  3:51	  Pylon, Warp Prism
          45	  3:56	  Pylon
          46	  4:04	  Dark Shrine
          46	  4:11	  Pylon
          48	  4:23	  Zealot x4
          56	  4:27	  Assimilator x2
          58	  4:34	  Observer
          61	  4:49	  Zealot x4
          69	  5:16	  Dark Templar x4
          77	  5:24	  Nexus
          77	  5:26	  Immortal
          77	  5:42	  Forge
          83	  5:50	  Protoss Ground Weapons Level 1, Sentry x3
          91	  5:58	  Shield Battery
          94	  6:19	  Gateway x2
          94	  6:24	  Archon x2
          100	  6:32	  Immortal
          103	  6:52	  Gateway x2
          106	  6:56	  Templar Archives
          107	  7:06	  Dark Templar x2
          113	  7:14	  Assimilator x2
          113	  7:18	  Archon
          122	  7:36	  High Templar x2
          124	  7:41	  Zealot x2
        """

        build_step_buildings = [
            Step(Supply(14), GridBuilding(UnitTypeId.PYLON, 1),
                 skip=UnitExists(UnitTypeId.PYLON, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(16), GridBuilding(UnitTypeId.GATEWAY, 1),
                 skip=UnitExists(UnitTypeId.GATEWAY, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(17), BuildGas(1)),
            Step(Supply(20), GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                 skip=UnitExists(UnitTypeId.CYBERNETICSCORE, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(21), BuildGas(2)),
            Step(Supply(21), GridBuilding(UnitTypeId.PYLON, 2),
                 skip=UnitExists(UnitTypeId.PYLON, 2, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(26), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1),
                 skip=UnitExists(UnitTypeId.TWILIGHTCOUNCIL, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(34), GridBuilding(UnitTypeId.GATEWAY, 2),
                 skip=UnitExists(UnitTypeId.GATEWAY, 2, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(35), GridBuilding(UnitTypeId.ROBOTICSFACILITY, 1),
                 skip=UnitExists(UnitTypeId.ROBOTICSFACILITY, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(38), GridBuilding(UnitTypeId.GATEWAY, 4),
                 skip=UnitExists(UnitTypeId.GATEWAY, 4, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(43), GridBuilding(UnitTypeId.PYLON, 3),
                 skip=UnitExists(UnitTypeId.PYLON, 3, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(45), GridBuilding(UnitTypeId.PYLON, 4),
                 skip=UnitExists(UnitTypeId.PYLON, 4, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(46), GridBuilding(UnitTypeId.PYLON, 5),
                 skip=UnitExists(UnitTypeId.PYLON, 5, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(46), GridBuilding(UnitTypeId.TEMPLARARCHIVE, 1),
                 skip=UnitExists(UnitTypeId.TEMPLARARCHIVE, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(56), BuildGas(3), None, None),
            Step(Supply(77), GridBuilding(UnitTypeId.FORGE, 1),
                 skip=UnitExists(UnitTypeId.FORGE, 1, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(94), GridBuilding(UnitTypeId.GATEWAY, 6),
                 skip=UnitExists(UnitTypeId.GATEWAY, 6, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(103), GridBuilding(UnitTypeId.GATEWAY, 8),
                 skip=UnitExists(UnitTypeId.GATEWAY, 8, include_killed=True, include_pending=True,
                                 include_not_ready=True), skip_until=None),
            Step(Supply(113), BuildGas(5), None, None),
        ]

        build_step_buildings_alt = [AutoPylon()]

        build_steps_chrono = [
            Step(None, ChronoTech(AbilityId.RESEARCH_WARPGATE, UnitTypeId.CYBERNETICSCORE)),
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 30),
            ),
            ChronoAnyTech(0),
        ]

        build_steps_workers = [
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, 16 + 3)),
            Step(Supply(20), Expand(2)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), UnitExists(UnitTypeId.PROBE, (2 * 16) + 6)),
            Step(Supply(54), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 UnitExists(UnitTypeId.PROBE, (2 * 16) + 3 + 6)),
            Step(Supply(77), Expand(3)),
            Step(Supply(75), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 UnitExists(UnitTypeId.PROBE, (3 * 16) + 6 + 3)),
            Step(Supply(113), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 UnitExists(UnitTypeId.PROBE, (3 * 16) + 6 + 6 + 3)),
        ]

        build_step_tech = [
            Step(All(Supply(26), UnitReady(UnitTypeId.CYBERNETICSCORE)), Tech(UpgradeId.WARPGATERESEARCH)),
            Step(All(Supply(37), UnitReady(UnitTypeId.TWILIGHTCOUNCIL)), Tech(UpgradeId.CHARGE)),
            Step(All(Supply(83), UnitReady(UnitTypeId.FORGE)), Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
        ]

        build_step_units_early = [
            Step(Supply(22), ProtossUnit(UnitTypeId.ADEPT, 1)),
            Step(Supply(27), ProtossUnit(UnitTypeId.STALKER, 1)), ]

        build_step_make_army = BuildOrder(
            Step(Supply(43), ProtossUnit(UnitTypeId.WARPPRISM, 1)),
            Step(Supply(48), ProtossUnit(UnitTypeId.ZEALOT, 4)),
            Step(Supply(58), ProtossUnit(UnitTypeId.OBSERVER, 1, priority=True)),
            Step(Supply(61), ProtossUnit(UnitTypeId.ZEALOT, 8)),
            Step(Supply(69), ProtossUnit(UnitTypeId.HIGHTEMPLAR, 4)),
            Archon([UnitTypeId.HIGHTEMPLAR]),
            # Step(Supply(69), ProtossUnit(UnitTypeId.ARCHON, 2)),
            Step(Supply(77), ProtossUnit(UnitTypeId.IMMORTAL, 1)),
            Step(Supply(83), ProtossUnit(UnitTypeId.SENTRY, 3)),
            # Step(Supply(94), ProtossUnit(UnitTypeId.ARCHON, 4)),
            Step(Supply(100), ProtossUnit(UnitTypeId.IMMORTAL, 2)),
            # Step(Supply(107), ProtossUnit(UnitTypeId.ARCHON, 6)),
            Step(Supply(110), ProtossUnit(UnitTypeId.ZEALOT, 10)),
        )

        build_step_filler_units = [Step(Minerals(500), ProtossUnit(UnitTypeId.ZEALOT)),
                                   Step(Minerals(500), ProtossUnit(UnitTypeId.STALKER)),
                                   Step(Minerals(500), ProtossUnit(UnitTypeId.IMMORTAL)), ]

        return BuildOrder(
            [build_steps_workers, build_step_buildings, build_step_units_early, build_step_make_army, build_step_tech,
             build_steps_chrono, build_step_filler_units, build_step_buildings_alt]
        )
