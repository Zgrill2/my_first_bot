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


class GenericWarpPrismDrop(ActBase):
    """
    Very old code, you probably don't want to use this for anything
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self, unit_to_use: UnitTypeId, quantity_desired: int):
        # initializing parameters of the drop (what unit are we dropping, how many. i.e. 2 archons, 2 DT, 4 zealot, etc)
        self.drop_quantity = quantity_desired
        self.unit_type = unit_to_use

        # tracks what phase of the push we are in
        self.phase = 0

        # tags to reference specific units being used in the drop
        self.ninja_dt_tags: List[Optional[int]] = []
        self.attack_dt_tags: List[Optional[int]] = []
        self.wp_tag: Optional[int] = None

        super().__init__()

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

        # Start dark templar attack
        dts = self.cache.own(self.unit_type).ready
        wps = self.cache.own(UnitTypeId.WARPPRISM).ready

        # at some point this should be able to drop in other expands too
        zone = self.zone_manager.enemy_main_zone

        # Begin the execution
        if dts.amount >= self.drop_quantity and wps.amount >= 1 and self.phase == 0:
            self.phase = 1

        if self.phase == 1:
            logger.info("Phase 1: Load Units into Dropship")

            # select units
            dts = dts.random_group_of(self.drop_quantity)
            wp = wps.random_group_of(1)[0]

            # assign tags to track units
            if self.wp_tag is None:
                for i in range(len(dts)):
                    if i % 2 == 0:
                        if dts[i].tag not in self.ninja_dt_tags + self.attack_dt_tags:
                            self.ninja_dt_tags.append(dts[i].tag)
                    else:
                        if dts[i].tag not in self.ninja_dt_tags + self.attack_dt_tags:
                            self.attack_dt_tags.append(dts[i].tag)
                self.wp_tag = wp.tag

            # assign reserved role
            self.assign_reserved_helper()

            # load DTs into prism
            for tag in self.ninja_dt_tags + self.attack_dt_tags:
                dt = self.cache.by_tag(tag)
                if dt:
                    dt(AbilityId.SMART, wp)

            if wp.cargo_left <= 1:
                self.phase = 2

        elif self.phase == 2:
            logger.info("Phase 2: Send prism to drop location")
            self.assign_reserved_helper()
            wp = self.cache.by_tag(self.wp_tag)
            if not wp is None:
                # path prism follows a safe path to the enemy base

                # Custom implement:
                #   Locate what corner we are in
                #   Locate what corner enemy is in
                #   Calculate path that stays close to edge of map
                p = self.pather.find_low_inside_ground(wp.position,
                    self.zone_manager.enemy_start_location.position.towards(wp, 5), 8)
                wp.move(p)
                logger.info(f'{wp.distance_to(self.zone_manager.enemy_start_location.position)}')
                if wp.distance_to(self.zone_manager.enemy_start_location.position) <= 11:
                    self.phase = 3
            else:
                # if prism isn't found drop must have failed
                self.reset_drop()
        elif self.phase == 3:
            logger.info("Phase 3: Find open ground and drop")
            self.assign_reserved_helper()
            wp = self.cache.by_tag(self.wp_tag)
            if wp:
                p = self.pather.find_weak_influence_ground(
                    self.zone_manager.enemy_start_location.position.towards(wp, 5), 10)
                wp.move(p)
                wp(AbilityId.UNLOADALLAT_WARPPRISM, wp)
                if wp.cargo_used <= 0:
                    self.phase = 4
            else:
                self.reset_drop()
        elif self.phase == 4:
            logger.info("Phase 4: Units dropped, attack commencing")
            self.assign_reserved_helper()
            wp = self.cache.by_tag(self.wp_tag)

            # set wp to micro/auto ai control
            self.combat.add_unit(wp)

        return True

