
from sharpy.interfaces import ILostUnitsManager
from sharpy.managers.core.manager_base import ManagerBase
from sc2.constants import EQUIVALENTS_FOR_TECH_PROGRESS


class DynamicBuildLogic(ManagerBase):
    lost_units_manager: ILostUnitsManager

    def __init__(self):
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.lost_units_manager = knowledge.get_required_manager(ILostUnitsManager)

    def get_killed_units(self, unit_type):
        count = 0

        count += self.lost_units_manager.own_lost_type(unit_type, real_type=False)
        related = EQUIVALENTS_FOR_TECH_PROGRESS.get(unit_type, None)
        if related:
            for related_type in related:
                count += self.lost_units_manager.own_lost_type(related_type, real_type=False)

        return count

    async def update(self):
        # This is being run each frame
        pass

    async def post_update(self):
        # This manager doesn't need to do anything at the end of the frame.
        pass
