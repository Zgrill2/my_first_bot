from sharpy.interfaces.combat_manager import MoveType
from managers.proxy_manager import ProxySolver

from sharpy.interfaces import ICombatManager, IZoneManager
from sc2.unit import Unit
from math import floor

from sharpy.interfaces import IGatherPointSolver

from sharpy.managers.core.roles import UnitTask
from sharpy.managers.core.grids import BuildGrid, GridArea

from sharpy.plans.acts import *
from sharpy.knowledges import Knowledge

from sc2 import UnitTypeId
from sc2.position import Point2


class ProxyStarBattery(ActBase):
    gather_point_solver: IGatherPointSolver

    def __init__(self):
        super().__init__()
        self.started_worker_defense = False
        self.all_out_started = False
        self.proxy_worker_tag = None
        self.init_proxy = False
        self.completed = False
        self.gather_point: Point2
        self.proxy_location: Point2
        self.solver = ProxySolver()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.gather_point_solver = knowledge.get_required_manager(IGatherPointSolver)

        self.proxy_location = self.calc_proxy_location()

        self.solver.grid = BuildGrid(self.knowledge)

        center = Point2((floor(self.proxy_location.x), floor(self.proxy_location.y)))
        x_range = range(-18, 18)
        y_range = range(-18, 18)

        for x in x_range:
            for y in y_range:
                pos = Point2((x + center.x, y + center.y))
                area: GridArea = self.solver.grid[pos]

                if area is None:
                    continue

                self.solver.massive_grid(pos)
        if self.knowledge.debug:
            self.solver.grid.save("proxy.bmp")
        self.gather_point = self.pather.find_path(self.proxy_location, self.zone_manager.enemy_start_location, 8)
        self.solver.buildings2x2.sort(key=lambda x: self.proxy_location.distance_to(x))
        self.solver.buildings3x3.sort(key=lambda x: self.proxy_location.distance_to(x))

    async def build_order(self):
        count = self.cache.own(UnitTypeId.GATEWAY).amount
        if count >= 1:
            if self.proxy_worker_tag:
                worker = self.get_worker()
                self.roles.clear_task(worker)
                self.proxy_worker_tag = None
            return

        if not self.ai.structures(UnitTypeId.NEXUS).ready.exists:
            # Nexus down, no build order to use.
            return

        if count < 2:
            await self.worker_micro()

    async def worker_micro(self):
        worker = self.get_worker()
        if not worker:
            return
        self.roles.set_task(UnitTask.Reserved, worker)
        if not self.has_build_order(worker):

            if self.ai.can_afford(UnitTypeId.PYLON):

                count = self.get_count(UnitTypeId.PYLON, include_pending=True)
                if count < 3:
                    for point in self.solver.buildings2x2:
                        if not self.ai.structures.closer_than(1, point):
                            if worker.build(UnitTypeId.PYLON, point):
                                break  # success

            if self.cache.own(UnitTypeId.PYLON).ready:
                count = self.get_count(UnitTypeId.STARGATE, include_pending=True)
                if count < 1 and self.ai.can_afford(UnitTypeId.STARGATE):
                    matrix = self.ai.state.psionic_matrix
                    for point in self.solver.buildings3x3:
                        if not self.ai.structures.closer_than(1, point) and matrix.covers(point):
                            if worker.build(UnitTypeId.STARGATE, point):
                                break  # success
            if self.cache.own(UnitTypeId.PYLON).ready and self.cache.own(UnitTypeId.STARGATE):
                count = self.get_count(UnitTypeId.SHIELDBATTERY, include_pending=True)
                if count < 2 and self.ai.can_afford(UnitTypeId.SHIELDBATTERY):
                    matrix = self.ai.state.psionic_matrix
                    for point in self.solver.buildings3x3:
                        if not self.ai.structures.closer_than(1, point) and matrix.covers(point):
                            if worker.build(UnitTypeId.SHIELDBATTERY, point):
                                break  # success
            if self.cache.own(UnitTypeId.PYLON).ready and self.cache.own(UnitTypeId.STARGATE).ready:
                gw = self.get_count(UnitTypeId.GATEWAY)
                if gw < 3 and self.ai.can_afford(UnitTypeId.GATEWAY):
                    matrix = self.ai.state.psionic_matrix
                    for point in self.solver.buildings3x3:
                        if not self.ai.structures.closer_than(1, point) and matrix.covers(point):
                            if worker.build(UnitTypeId.GATEWAY, point):
                                break  # success

            if self.cache.own(UnitTypeId.STARGATE) or self.cache.own(UnitTypeId.SHIELDBATTERY):
                sgs = self.cache.own(UnitTypeId.STARGATE).ready
                sbs = self.cache.own(UnitTypeId.SHIELDBATTERY).ready
                buildings = sgs + sbs
                for b in buildings:
                    point = b.position
                    matrix = self.ai.state.psionic_matrix
                    if not matrix.covers(point):
                        if worker.build(UnitTypeId.PYLON, point + Point2((3, 3))):
                            break  # success
            """
            Fix to defend proxy only as long as its up
            if worker.tag not in self.ai.unit_tags_received_action and not self.has_build_order(worker):
                target = self.pather.find_weak_influence_ground(self.proxy_location, 15)
                self.pather.find_influence_ground_path(worker.position, target)
                worker.move(self.proxy_location)"""

    async def execute(self) -> bool:
        self.gather_point_solver.set_gather_point(self.gather_point)
        await self.build_order()
        return True

    def get_worker(self):
        if not self.ai.workers:
            return None
        worker = self.cache.by_tag(self.proxy_worker_tag)
        if worker:
            return worker

        worker = self.ai.workers.closest_to(self.proxy_location)
        self.proxy_worker_tag = worker.tag
        return worker

    def calc_proxy_location(self):
        STATIC = self.ai.game_info.map_center.distance_to(self.zone_manager.enemy_main_zone.center_location)

        # algo
        # check distance from main to natural
        # check distance from main to 3rd and 4th
        # if 3rd or 4th < natural build there
        # else default to map center algo
        base_to_use = None
        third = self.zone_manager.enemy_expansion_zones[2]
        fourth = self.zone_manager.enemy_expansion_zones[3]

        if third.center_location.distance_to(
                self.zone_manager.enemy_main_zone.center_location) < self.zone_manager.enemy_natural.center_location.distance_to(
            self.zone_manager.enemy_main_zone.center_location):
            base_to_use = third
        elif fourth.center_location.distance_to(
                self.zone_manager.enemy_main_zone.center_location) < self.zone_manager.enemy_natural.center_location.distance_to(
            self.zone_manager.enemy_main_zone.center_location):
            base_to_use = fourth

        if base_to_use:
            proxy_location = base_to_use.center_location
        else:
            """
            proxy_location = self.ai.game_info.map_center.towards(self.ai.enemy_start_locations[0], STATIC)
            rad = self.zone_manager.enemy_main_zone.radius
            distance = proxy_location.distance_to(self.zone_manager.enemy_main_zone.center_location)
            while distance <= rad+5 and not proxy_location in self.pather.map.map.get_borders():
                STATIC -= 1
                proxy_location = self.ai.game_info.map_center.towards(self.ai.enemy_start_locations[0], STATIC)
                distance = proxy_location.distance_to(self.zone_manager.enemy_main_zone.center_location)
            """
            proxy_location = self.zone_manager.enemy_main_zone.center_location.towards(self.ai.game_info.map_center, 5)
            rad = self.zone_manager.enemy_main_zone.radius + 10
            while proxy_location.distance_to(
                    self.zone_manager.enemy_main_zone.center_location) < rad and not proxy_location in self.pather.map.map.get_borders():
                proxy_location = proxy_location.towards(self.ai.game_info.map_center, 5)
        return proxy_location


class VoidRayRush(ActBase):
    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self):
        self.unit_type = UnitTypeId.VOIDRAY
        super().__init__()

    @property
    def attack_type(self):
        voids = self.cache.own(self.unit_type).ready
        if len(voids) < 3:
            return MoveType.Harass
        return MoveType.Assault

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.combat = knowledge.get_required_manager(ICombatManager)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    async def execute(self) -> bool:
        voids = self.cache.own(self.unit_type).ready

        # Begin the execution
        if voids:
            self.micro_units()
        return True

    def micro_units(self):
        voids = self.cache.own(self.unit_type).ready
        attackers = self.ai.units.of_type({UnitTypeId.STALKER, UnitTypeId.ZEALOT})
        zone = self.zone_manager.enemy_main_zone

        if self.zone_manager.enemy_main_zone.enemy_townhall:
            attack_zone = zone.center_location
            move_type = MoveType.Assault
        else:
            attack_zone = zone.center_location#self.cache.enemy_in_range(self.zone_manager.enemy_main_zone.center_location, 20).
            move_type = MoveType.SearchAndDestroy

        for unit in voids + attackers:
            if unit.shield_percentage > .25:
                if unit.is_ready:
                    self.combat.add_unit(unit)
        self.combat.execute(attack_zone, move_type)
        """
            self.ai.enemy_structures
        if len(self.cache.enemy_townhalls) < 2:
            attack_zone = self.cache.enemy_townhalls.random_group_of(1).center
            move_type = MoveType.SearchAndDestroy
        else:"""

        for a in attackers:
            self.shield_battery_micro(a)
        for v in voids:
            self.shield_battery_micro(v)

    def shield_battery_micro(self, unit):
        batteries = self.cache.own(UnitTypeId.SHIELDBATTERY).ready

        if isinstance(unit, Unit):
            if unit.shield_percentage <= .25 and 0 < len(batteries):
                self.roles.set_task(UnitTask.Reserved, unit)
                d = 100000
                retreat_to = batteries.random_group_of(1)[0]
                for b in batteries:
                    if unit.distance_to(b) < d:
                        d = unit.distance_to(b)
                        retreat_to = b
                if unit.is_flying:
                    p = self.pather.find_weak_influence_air(retreat_to.position, 5)
                else:
                    p = self.pather.find_weak_influence_ground(retreat_to.position, 5)
                unit.move(p)
