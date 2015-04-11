import point
import worldmodel
import actions
BLOB_RATE_SCALE = 4
BLOB_ANIMATION_RATE_SCALE = 50
BLOB_ANIMATION_MIN = 1
BLOB_ANIMATION_MAX = 3

ORE_CORRUPT_MIN = 20000
ORE_CORRUPT_MAX = 30000

QUAKE_STEPS = 10
QUAKE_DURATION = 1100
QUAKE_ANIMATION_RATE = 100

VEIN_SPAWN_DELAY = 500
VEIN_RATE_MIN = 8000
VEIN_RATE_MAX = 17000
class Background:
   def __init__(self, name, imgs):
      self.name = name
      self.imgs = imgs
      self.current_img = 0


class MinerNotFull:
   def __init__(self, name, resource_limit, position, rate, imgs,
      animation_rate):
      self.name = name
      self.position = position
      self.rate = rate
      self.imgs = imgs
      self.current_img = 0
      self.resource_limit = resource_limit
      self.resource_count = 0
      self.animation_rate = animation_rate
      self.pending_actions = []

   def miner_to_ore(world, entity, ore):
     entity_pt = get_position(entity)
     if not ore:
          return ([entity_pt], False)
     ore_pt = get_position(ore)
     if actions.adjacent(entity_pt, ore_pt):
          set_resource_count(entity,
            1 + get_resource_count(entity))
          actions.remove_entity(world, ore)
          return ([ore_pt], True)
     else:
          new_pt = actions.next_position(world, entity_pt, ore_pt)
          return (worldmodel.move_entity(world, entity, new_pt), False)

   def entity_string(entity):
        return ' '.join(['miner', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.resource_limit),
         str(entity.rate), str(entity.animation_rate)])

class MinerFull:
   def __init__(self, name, resource_limit, position, rate, imgs,
      animation_rate):
      self.name = name
      self.position = position
      self.rate = rate
      self.imgs = imgs
      self.current_img = 0
      self.resource_limit = resource_limit
      self.resource_count = resource_limit
      self.animation_rate = animation_rate
      self.pending_actions = []

   def miner_to_smith(world, entity, smith):
        entity_pt = get_position(entity)
        if not smith:
            return ([entity_pt], False)
        smith_pt = get_position(smith)
        if actions.adjacent(entity_pt, smith_pt):
            set_resource_count(smith,
            get_resource_count(smith) +
            get_resource_count(entity))
            set_resource_count(entity, 0)
            return ([], True)
        else:
            new_pt = actions.next_position(world, entity_pt, smith_pt)
            return (worldmodel.move_entity(world, entity, new_pt), False)

class Vein:
   def __init__(self, name, rate, position, imgs, resource_distance=1):
      self.name = name
      self.position = position
      self.rate = rate
      self.imgs = imgs
      self.current_img = 0
      self.resource_distance = resource_distance
      self.pending_actions = []

   def entity_string(entity):
        return ' '.join(['vein', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.rate),
         str(entity.resource_distance)])

class Ore:
   def __init__(self, name, position, imgs, rate=5000):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0
      self.rate = rate
      self.pending_actions = []

   def entity_string(entity):
         return ' '.join(['ore', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.rate)])

class Blacksmith:
   def __init__(self, name, position, imgs, resource_limit, rate,
      resource_distance=1):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0
      self.resource_limit = resource_limit
      self.resource_count = 0
      self.rate = rate
      self.resource_distance = resource_distance
      self.pending_actions = []

   def entity_string(entity):
        return ' '.join(['blacksmith', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.resource_limit),
         str(entity.rate), str(entity.resource_distance)])

class Obstacle:
   def __init__(self, name, position, imgs):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0

   def entity_string(entity):
        return ' '.join(['obstacle', entity.name, str(entity.position.x),
         str(entity.position.y)])

class OreBlob:
   def __init__(self, name, position, rate, imgs, animation_rate):
      self.name = name
      self.position = position
      self.rate = rate
      self.imgs = imgs
      self.current_img = 0
      self.animation_rate = animation_rate
      self.pending_actions = []

   def blob_to_vein(world, entity, vein):
       entity_pt = get_position(entity)
       if not vein:
          return ([entity_pt], False)
       vein_pt = get_position(vein)
       if actions.adjacent(entity_pt, vein_pt):
          actions.remove_entity(world, vein)
          return ([vein_pt], True)
       else:
          new_pt = entity.blob_next_position(world, entity_pt, vein_pt)
          old_entity = worldmodel.get_tile_occupant(world, new_pt)
          if isinstance(old_entity, Ore):
             actions.remove_entity(world, old_entity)
          return (worldmodel.move_entity(world, entity, new_pt), False)

   def blob_next_position(world, entity_pt, dest_pt):
       horiz = sign(dest_pt.x - entity_pt.x)
       new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

       if horiz == 0 or (worldmodel.is_occupied(world, new_pt) and
          not isinstance(worldmodel.get_tile_occupant(world, new_pt),
          Ore)):
          vert = sign(dest_pt.y - entity_pt.y)
          new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

          if vert == 0 or (worldmodel.is_occupied(world, new_pt) and
             not isinstance(worldmodel.get_tile_occupant(world, new_pt),
             Ore)):
             new_pt = point.Point(entity_pt.x, entity_pt.y)

       return new_pt




class Quake:
   def __init__(self, name, position, imgs, animation_rate):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0
      self.animation_rate = animation_rate
      self.pending_actions = []


def set_position(entity, point):
   entity.position = point

def get_position(entity):
   return entity.position


def get_images(entity):
   return entity.imgs

def get_image(entity):
   return entity.imgs[entity.current_img]


def get_rate(entity):
   return entity.rate


def set_resource_count(entity, n):
   entity.resource_count = n

def get_resource_count(entity):
   return entity.resource_count


def get_resource_limit(entity):
   return entity.resource_limit


def get_resource_distance(entity):
   return entity.resource_distance


def get_name(entity):
   return entity.name


def get_animation_rate(entity):
   return entity.animation_rate


def remove_pending_action(entity, action):
   if hasattr(entity, "pending_actions"):
      entity.pending_actions.remove(action)

def add_pending_action(entity, action):
   if hasattr(entity, "pending_actions"):
      entity.pending_actions.append(action)


def get_pending_actions(entity):
   if hasattr(entity, "pending_actions"):
      return entity.pending_actions
   else:
      return []

def clear_pending_actions(entity):
   if hasattr(entity, "pending_actions"):
      entity.pending_actions = []


def next_image(entity):
   entity.current_img = (entity.current_img + 1) % len(entity.imgs)


# This is a less than pleasant file format, but structured based on
# material covered in course.  Something like JSON would be a
# significant improvement.
def entity_string(entity):
    return 'unknown'

def sign(x):
   if x < 0:
      return -1
   elif x > 0:
      return 1
   else:
      return 0