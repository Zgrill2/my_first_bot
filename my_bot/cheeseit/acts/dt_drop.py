from typing import Optional

from sharpy.interfaces import ICombatManager, IZoneManager
from sharpy.knowledges import Knowledge
from sc2.unit import Unit
from sc2.units import Units
from sc2 import UnitTypeId
from sharpy.managers.core.roles import UnitTask

from typing import List
from loguru import logger


from generic_drop import GenericWarpPrismDrop


class DarkTemplarDrop(GenericWarpPrismDrop):
    """
    Very old code, you probably don't want to use this for anything
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self, quantity_desired: int):
        # initializing parameters of the drop (what unit are we dropping, how many. i.e. 2 archons, 2 DT, 4 zealot, etc)
        self.drop_quantity = quantity_desired

        # tracks what phase of the push we are in
        self.phase = 0

        # tags to reference specific units being used in the drop
        self.ninja_dt_tags: List[Optional[int]] = []
        self.attack_dt_tags: List[Optional[int]] = []
        self.wp_tag: Optional[int] = None

        super().__init__(UnitTypeId.DARKTEMPLAR, quantity_desired)

    @property
    def dt_tags(self):
        return self.ninja_dt_tags + self.attack_dt_tags

    def assign_reserved_helper(self):
        for tag in self.dt_tags + [self.wp_tag]:
            logger.info(f'{tag}')
            if not self.cache.by_tag(tag):
                print(f'nonetype tag: {tag}: continuing on')
                continue
            self.roles.set_task(UnitTask.Reserved, self.cache.by_tag(tag))

    def reset_drop(self):
        """
        Called if drop has failed or completed
        Sets all tags to None
        Sets phase to 0
        """
        self.wp_tag = None
        self.phase = 0
        self.ninja_dt_tags = []
        self.attack_dt_tags = []

    def locate_our_corner(self):
        logger.info(f'{self.pather.map.map}')

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.combat = knowledge.get_required_manager(ICombatManager)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    async def execute(self) -> bool:
        """
        Phase based execution of a drop
        Phase 1. Load dropship
        Phase 2. Send dropship to drop location
        Phase 3: Drop units off
        Phase 4: Micro units with prism
        """
        zone = self.zone_manager.enemy_main_zone

        if self.phase == 4:
            logger.info("Phase 4: Units dropped, attack commencing")
            self.assign_reserved_helper()
            wp = self.cache.by_tag(self.wp_tag)

            # set wp to micro/auto ai control
            self.roles.set_task(UnitTask.Attacking, wp)

            # set dropped units to attack
            for tag in self.ninja_dt_tags:
                if self.cache.by_tag(tag):
                    dt = self.cache.by_tag(tag)
                    dt.move(zone.center_location)
            for tag in self.attack_dt_tags:
                if self.cache.by_tag(tag):
                    dt = self.cache.by_tag(tag)
                    dt.attack(zone.center_location)
            await self.harash_with_dt()
            await self.attack_with_dt()

        await super().execute()
        return True

    async def attack_with_dt(self):
        for tag in self.attack_dt_tags:
            attack_dt: Unit = self.cache.by_tag(tag)
            if attack_dt is not None:
                self.roles.set_task(UnitTask.Reserved, attack_dt)
                await self.attack_command(attack_dt)

    async def attack_command(self, unit: Unit):
        self.combat.add_unit(unit)
        target = self.zone_manager.enemy_start_location

        units: Units = self.ai.all_enemy_units
        units = units.not_flying
        if units:
            target = units.closest_to(unit).position

        self.combat.execute(target)

    async def harash_with_dt(self):
        for tag in self.ninja_dt_tags:
            harash_dt: Unit = self.cache.by_tag(tag)
            if harash_dt is not None:
                self.roles.set_task(UnitTask.Reserved, harash_dt)
                enemy_workers = self.cache.enemy_in_range(harash_dt.position, 15).of_type(
                    [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE]
                )
                if enemy_workers.exists:
                    target = enemy_workers.closest_to(harash_dt)
                    harash_dt.attack(target)
                elif harash_dt.shield_health_percentage < 1:
                    await self.attack_command(harash_dt)
                elif harash_dt.distance_to(self.zone_manager.enemy_start_location) < 5:
                    self.roles.clear_task(harash_dt)

                    # need to fix below line due to now we use a list of harassers
                    # unsure the importance of this behavior
                    # self.ninja_dt_tag = 0
                else:
                    harash_dt.move(self.zone_manager.enemy_start_location)
