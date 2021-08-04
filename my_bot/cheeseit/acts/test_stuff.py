from typing import Optional

from sc2.position import Point2
from sharpy.interfaces import ICombatManager, IZoneManager
from sharpy.knowledges import Knowledge
from sharpy.plans.acts import ActBase
from sc2.unit import Unit
from sc2.units import Units
from sc2 import UnitTypeId, AbilityId
from sharpy.managers.core.roles import UnitTask
from sharpy.combat import MoveType

from loguru import logger


class ProbeAttack(ActBase):
    """
    If I wanted to go along the edge of the map, I would draw a line from the center of the map to my base and one
    from the center to the drop location. That tells you which quadrant you're in and which you need to get to so you
    can use the edges that would get you there. For instance, on Blackburn, you'd be going from lower left to lower
    right (or vice versa) so you only need the bottom edge of the map. On one of the maps with diagonal spawns,
    you'd need one vertical edge and one horizontal edge and you could use the target location for which edge to
    traverse first.
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self):
        # initializing parameters of the drop (what unit are we dropping, how many. i.e. 2 archons, 2 DT, 4 zealot, etc)
        super().__init__()

    async def execute(self) -> bool:
        units = self.ai.units
        for u in units:
            self.combat.add_unit(u)
        self.combat.execute(self.zone_manager.enemy_main_zone.enemy_townhall.position, MoveType.SearchAndDestroy)
        return True


class TestStuff(ActBase):
    """
    If I wanted to go along the edge of the map, I would draw a line from the center of the map to my base and one
    from the center to the drop location. That tells you which quadrant you're in and which you need to get to so you
    can use the edges that would get you there. For instance, on Blackburn, you'd be going from lower left to lower
    right (or vice versa) so you only need the bottom edge of the map. On one of the maps with diagonal spawns,
    you'd need one vertical edge and one horizontal edge and you could use the target location for which edge to
    traverse first.
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self):
        # initializing parameters of the drop (what unit are we dropping, how many. i.e. 2 archons, 2 DT, 4 zealot, etc)
        self.index = 0
        self.wp_tag: Optional[int] = None
        super().__init__()
        self.points = None#

    def locate_our_corner(self):
        logger.info(f'{self.pather.map.map}')

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.combat = knowledge.get_required_manager(ICombatManager)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    def load_points(self):
        #points_tuple = self.pather.map.map.get_borders()
        width = self.pather.ai.game_info.playable_area.width
        height = self.pather.ai.game_info.playable_area.height
        x_zero = self.pather.ai.game_info.playable_area.x
        y_zero = self.pather.ai.game_info.playable_area.y

        points_tuple = [(x_zero, y_zero),(x_zero, y_zero+height), (x_zero+width, y_zero+height), (x_zero+width, y_zero)]
        points = []
        for p in points_tuple:
            points.append(Point2(p))
        self.points = points[:]

    async def execute(self) -> bool:
        wps = self.cache.own(UnitTypeId.WARPPRISM).ready

        if self.points is None:
            self.load_points()
        # Begin the execution
        if wps.amount >= 1:
            if self.wp_tag is None:
                wp = wps.random_group_of(1)[0]
                self.wp_tag = wp.tag
            else:
                wp = self.cache.by_tag(self.wp_tag)
            self.roles.set_task(UnitTask.Reserved, wp)
            p = self.pather.find_path(wp.position, self.points[self.index], 1)
            wp.move(p)
            if wp.distance_to(self.points[self.index]) <= 3:
                self.index += 1
                if self.index >= len(self.points):
                    self.index = 0

        return True
