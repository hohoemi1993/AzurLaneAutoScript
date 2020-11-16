from module.base.utils import location2node
from module.logger import logger


class GridInfo:
    """
    Class that gather basic information of a grid in map_v1.

    Visit 碧蓝航线WIKI(Chinese Simplified) http://wiki.biligame.com/blhx, to get basic info of a map_v1.
    For example, visit http://wiki.biligame.com/blhx/7-2, to know more about campaign 7-2,
    which includes boss point, enemy spawn point.

    A grid contains these unchangeable properties which can known from WIKI.
    | print_name | property_name  | description             |
    |------------|----------------|-------------------------|
    | ++         | is_land        | fleet can't go to land  |
    | --         | is_sea         | sea                     |
    | __         |                | submarine spawn point   |
    | SP         | is_spawn_point | fleet may spawns here   |
    | ME         | may_enemy      | enemy may spawns here   |
    | MB         | may_boss       | boss may spawns here    |
    | MM         | may_mystery    | mystery may spawns here |
    | MA         | may_ammo       | fleet can get ammo here |
    | MS         | may_siren      | Siren/Elite enemy spawn |
    """

    # is_sea --
    is_land = False  # ++
    is_spawn_point = False  # SP

    may_enemy = False  # ME
    may_boss = False  # MB
    may_mystery = False  # MM
    may_ammo = False  # MA
    may_siren = False  # MS
    may_ambush = False
    may_mechanism_trigger = False
    may_mechanism_block = False
    mechanism_trigger = None  # SelectedGrids
    mechanism_block = None  # SelectedGrids
    mechanism_wait = 2  # Seconds to wait the mechanism unlock animation

    is_enemy = False  # example: 0L 1M 2C 3T 3E
    is_boss = False  # BO
    is_mystery = False  # MY
    is_ammo = False  # AM
    is_fleet = False  # FL
    is_current_fleet = False
    is_submarine = False  # ss
    is_siren = False  # SI
    is_portal = False
    portal_link = ()

    enemy_scale = 0
    enemy_genre = None  # Light, Main, Carrier, Treasure, Enemy(unknown)

    is_cleared = False
    is_caught_by_siren = False
    is_carrier = False  # Is carrier spawn in mystery
    is_movable = False  # Is movable enemy
    is_mechanism_trigger = False  # Mechanism has triggered
    is_mechanism_block = False  # Blocked by mechanism
    cost = 9999
    cost_1 = 9999
    cost_2 = 9999
    connection = None
    weight = 1

    location = None

    def decode(self, text):
        text = text.upper()
        dic = {
            '++': 'is_land',
            'SP': 'is_spawn_point',
            'ME': 'may_enemy',
            'MB': 'may_boss',
            'MM': 'may_mystery',
            'MA': 'may_ammo',
            'MS': 'may_siren',
        }
        valid = text in dic
        for k, v in dic.items():
            self.__setattr__(v, valid and bool(k == text))

        self.may_ambush = not (self.may_enemy or self.may_boss or self.may_mystery or self.may_mystery)
        # if self.may_siren:
        #     self.may_enemy = True
        # if self.may_boss:
        #     self.may_enemy = True

    def encode(self):
        dic = {
            '++': 'is_land',
            'BO': 'is_boss',
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        if self.is_siren:
            name = self.enemy_genre[6:8].upper() if self.enemy_genre else 'SU'
            return name if name else 'SU'

        if self.is_enemy:
            return '%s%s' % (
                self.enemy_scale if self.enemy_scale else 0,
                self.enemy_genre[0].upper() if self.enemy_genre else 'E')

        dic = {
            'FL': 'is_current_fleet',
            'Fc': 'is_caught_by_siren',
            'Fl': 'is_fleet',
            'ss': 'is_submarine',
            'MY': 'is_mystery',
            'AM': 'is_ammo',
            '==': 'is_cleared'
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        return '--'

    def __str__(self):
        return location2node(self.location)

    __repr__ = __str__

    def __hash__(self):
        return hash(self.location)

    def __eq__(self, other):
        return self.location == other.location

    @property
    def str(self):
        return self.encode()

    @property
    def is_sea(self):
        return False if self.is_land or self.is_enemy or self.is_boss else True

    @property
    def may_carrier(self):
        return self.is_sea and not self.may_enemy

    @property
    def is_accessible(self):
        return self.cost < 9999

    @property
    def is_accessible_1(self):
        return self.cost_1 < 9999

    @property
    def is_accessible_2(self):
        return self.cost_2 < 9999

    @property
    def is_nearby(self):
        return self.cost < 20

    def merge(self, info, mode='normal'):
        """
        Args:
            info (GridInfo):
            mode (str): Scan mode, such as 'normal', 'carrier', 'movable'

        Returns:
            bool: If success.
        """
        if info.is_caught_by_siren:
            if self.is_sea:
                self.is_fleet = True
                self.is_caught_by_siren = True
            else:
                return False
        if info.is_fleet:
            if self.is_sea:
                self.is_fleet = True
                if info.is_current_fleet:
                    self.is_current_fleet = True
                return True
            else:
                return False
        if info.is_boss:
            if not self.is_land and self.may_boss:
                self.is_boss = True
                return True
            else:
                return False
        if info.is_siren:
            if not self.is_land and self.may_siren:
                self.is_siren = True
                self.enemy_scale = 0
                self.enemy_genre = info.enemy_genre
                return True
            elif (mode == 'movable' or self.is_movable) and not self.is_land:
                self.is_siren = True
                self.enemy_scale = 0
                self.enemy_genre = info.enemy_genre
                return True
            else:
                return False
        if info.is_enemy:
            if not self.is_land and (self.may_enemy or self.is_carrier):
                self.is_enemy = True
                if info.enemy_scale:
                    self.enemy_scale = info.enemy_scale
                if info.enemy_genre:
                    self.enemy_genre = info.enemy_genre
                return True
            elif mode == 'carrier' and not self.is_land and self.may_carrier:
                self.is_enemy = True
                self.is_carrier = True
                if info.enemy_scale:
                    self.enemy_scale = info.enemy_scale
                if info.enemy_genre:
                    self.enemy_genre = info.enemy_genre
                return True
            else:
                return False
        if info.is_mystery:
            if self.may_mystery:
                self.is_mystery = info.is_mystery
                return True
            else:
                return False
        if info.is_ammo:
            if self.may_ammo:
                self.is_ammo = info.is_ammo
                return True
            else:
                return False

        return True

    def wipe_out(self):
        """
        Call this method when a fleet step on grid.
        """
        self.is_enemy = False
        self.enemy_scale = 0
        self.enemy_genre = None
        self.is_mystery = False
        self.is_boss = False
        self.is_ammo = False
        self.is_siren = False
        self.is_caught_by_siren = False
        self.is_carrier = False
        self.is_movable = False
        if self.is_mechanism_trigger:
            self.mechanism_trigger.set(is_mechanism_trigger=False)
            self.mechanism_block.set(is_mechanism_block=False)

    def reset(self):
        """
        Call this method after entering a map.
        """
        self.wipe_out()
        self.is_fleet = False
        self.is_current_fleet = False
        self.is_submarine = False
        self.is_cleared = False
        self.is_mechanism_trigger = self.may_mechanism_trigger
        self.is_mechanism_block = self.may_mechanism_block

    def covered_grid(self):
        """Relative coordinate of the covered grid.

        Returns:
            list[tuple]:
        """
        if self.is_current_fleet:
            return [(0, -1), (0, -2)]
        if self.is_fleet or self.is_siren or self.is_mystery:
            return [(0, -1)]

        return []
