import entities
import pygame
import ordered_list
import actions
import occ_grid
import point
import image_store

class WorldModel:
   def __init__(self, num_rows, num_cols, background):
      self.background = occ_grid.Grid(num_cols, num_rows, background)
      self.num_rows = num_rows
      self.num_cols = num_cols
      self.occupancy = occ_grid.Grid(num_cols, num_rows, None)
      self.entities = []
      self.action_queue = ordered_list.OrderedList()

   def schedule_blob(world, blob, ticks, i_store):
        schedule_action(world, blob, world.create_ore_blob_action(world, blob, i_store),
        ticks + entities.get_rate(blob))
        blob.schedule_animation(world, blob)


   def schedule_miner(world, miner, ticks, i_store):
        schedule_action(world, miner, world.create_miner_action(world, miner, i_store),
        ticks + entities.get_rate(miner))
        miner.schedule_animation(world, miner)

   def schedule_animation(world, entity, repeat_count=0):
       schedule_action(world, entity,
          world.create_animation_action(world, entity, repeat_count),
          entities.get_animation_rate(entity))

   def create_miner_action(world, entity, image_store):
      if isinstance(entity, entities.MinerNotFull):
         return world.create_miner_not_full_action(world, entity, image_store)
      else:
         return world.create_miner_full_action(world, entity, image_store)

   def create_animation_action(world, entity, repeat_count):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)

         entities.next_image(entity)

         if repeat_count != 1:
            schedule_action(world, entity,
               entity.create_animation_action(world, entity, max(repeat_count - 1, 0)),
               current_ticks + entities.get_animation_rate(entity))

         return [entities.get_position(entity)]
      return action

   def create_miner_not_full_action(world, entity, i_store):
       def action(current_ticks):
          entities.remove_pending_action(entity, action)

          entity_pt = entities.get_position(entity)
          ore = find_nearest(world, entity_pt, entities.Ore)
          (tiles, found) = entity.miner_to_ore(world, entity, ore)

          new_entity = entity
          if found:
             new_entity = world.try_transform_miner(world, entity,
                world.try_transform_miner_not_full)

          schedule_action(world, new_entity,
             world.create_miner_action(world, new_entity, i_store),
             current_ticks + entities.get_rate(new_entity))
          return tiles
       return action

   def create_miner_full_action(world, entity, i_store):
       def action(current_ticks):
          entities.remove_pending_action(entity, action)

          entity_pt = entities.get_position(entity)
          smith = find_nearest(world, entity_pt, entities.Blacksmith)
          (tiles, found) = entity.miner_to_smith(world, entity, smith)

          new_entity = entity
          if found:
             new_entity = world.try_transform_miner(world, entity,
                world.try_transform_miner_full)

          schedule_action(world, new_entity,
             world.create_miner_action(world, new_entity, i_store),
             current_ticks + entities.get_rate(new_entity))
          return tiles
       return action

   def create_ore_blob_action(world, entity, i_store):
       def action(current_ticks):
          entities.remove_pending_action(entity, action)

          entity_pt = entities.get_position(entity)
          vein = find_nearest(world, entity_pt, entities.Vein)
          (tiles, found) = entity.blob_to_vein(world, entity, vein)

          next_time = current_ticks + entities.get_rate(entity)
          if found:
             quake = world.create_quake(world, tiles[0], current_ticks, i_store)
             add_entity(world, quake)
             next_time = current_ticks + entities.get_rate(entity) * 2

          schedule_action(world, entity,
             world.create_ore_blob_action(world, entity, i_store),
             next_time)

          return tiles
       return action



   def create_vein_action(world, entity, i_store):
       def action(current_ticks):
          entities.remove_pending_action(entity, action)

          open_pt = world.find_open_around(world, entities.get_position(entity),
             entities.get_resource_distance(entity))
          if open_pt:
             ore = world.create_ore(world,
                "ore - " + entities.get_name(entity) + " - " + str(current_ticks),
                open_pt, current_ticks, i_store)
             add_entity(world, ore)
             tiles = [open_pt]
          else:
             tiles = []

          schedule_action(world, entity,
             world.create_vein_action(world, entity, i_store),
             current_ticks + entities.get_rate(entity))
          return tiles
       return action


   def try_transform_miner_full(world, entity):
       new_entity = entities.MinerNotFull(
          entities.get_name(entity), entities.get_resource_limit(entity),
          entities.get_position(entity), entities.get_rate(entity),
          entities.get_images(entity), entities.get_animation_rate(entity))

       return new_entity


   def try_transform_miner_not_full(world, entity):
       if entity.resource_count < entity.resource_limit:
          return entity
       else:
          new_entity = entities.MinerFull(
             entities.get_name(entity), entities.get_resource_limit(entity),
             entities.get_position(entity), entities.get_rate(entity),
             entities.get_images(entity), entities.get_animation_rate(entity))
          return new_entity


   def try_transform_miner(world, entity, transform):
       new_entity = transform(world, entity)
       if entity != new_entity:
          world.clear_pending_actions(world, entity)
          remove_entity_at(world, entities.get_position(entity))
          add_entity(world, new_entity)
          world.schedule_animation(world, new_entity)

       return new_entity

   def create_entity_death_action(world, entity):
       def action(current_ticks):
          entities.remove_pending_action(entity, action)
          pt = entities.get_position(entity)
          remove_entity(world, entity)
          return [pt]
       return action


   def create_ore_transform_action(world, entity, i_store):
       def action(current_ticks):
          entities.remove_pending_action(entity, action)
          blob = world.create_blob(world, entities.get_name(entity) + " -- blob",
             entities.get_position(entity),
             entities.get_rate(entity),
             current_ticks, i_store)

          remove_entity(world, entity)
          add_entity(world, blob)

          return [entities.get_position(blob)]
       return action





   def create_blob(world, name, pt, rate, ticks, i_store):
       blob = entities.OreBlob(name, pt, rate,
          image_store.get_images(i_store, 'blob'),
          random.randint(BLOB_ANIMATION_MIN, BLOB_ANIMATION_MAX)
          * BLOB_ANIMATION_RATE_SCALE)
       schedule_blob(world, blob, ticks, i_store)
       return blob




   def create_ore(world, name, pt, ticks, i_store):
       ore = entities.Ore(name, pt, image_store.get_images(i_store, 'ore'),
          random.randint(world.ORE_CORRUPT_MIN, world.ORE_CORRUPT_MAX))
       world.schedule_ore(world, ore, ticks, i_store)

       return ore


   def schedule_ore(world, ore, ticks, i_store):
       schedule_action(world, ore,
          world.create_ore_transform_action(world, ore, i_store),
          ticks + entities.get_rate(ore))


   def create_quake(world, pt, ticks, i_store):
       quake = entities.Quake("quake", pt,
          image_store.get_images(i_store, 'quake'), QUAKE_ANIMATION_RATE)
       world.schedule_quake(world, quake, ticks)
       return quake


   def schedule_quake(world, quake, ticks):
       world.schedule_animation(world, quake, QUAKE_STEPS)
       schedule_action(world, quake, world.create_entity_death_action(world, quake),
          ticks + QUAKE_DURATION)


   def create_vein(world, name, pt, ticks, i_store):
       vein = entities.Vein("vein" + name,
          random.randint(VEIN_RATE_MIN, VEIN_RATE_MAX),
          pt, image_store.get_images(i_store, 'vein'))
       return vein


   def schedule_vein(world, vein, ticks, i_store):
       schedule_action(world, vein, world.create_vein_action(world, vein, i_store),
          ticks + entities.get_rate(vein))


   def schedule_action(world, entity, action, time):
       entities.add_pending_action(entity, action)
       schedule_action(world, action, time)





   def clear_pending_actions(world, entity):
       for action in entities.get_pending_actions(entity):
          unschedule_action(world, action)
       entities.clear_pending_actions(entity)

   def remove_entity(world, entity):
       for action in entities.get_pending_actions(entity):
          unschedule_action(world, action)
       entities.clear_pending_actions(entity)
       remove_entity(world, entity)


def within_bounds(world, pt):
   return (pt.x >= 0 and pt.x < world.num_cols and
      pt.y >= 0 and pt.y < world.num_rows)


def is_occupied(world, pt):
   return (within_bounds(world, pt) and
      occ_grid.get_cell(world.occupancy, pt) != None)


def nearest_entity(entity_dists):
   if len(entity_dists) > 0:
      pair = entity_dists[0]
      for other in entity_dists:
         if other[1] < pair[1]:
            pair = other
      nearest = pair[0]
   else:
      nearest = None

   return nearest


def distance_sq(p1, p2):
   return (p1.x - p2.x)**2 + (p1.y - p2.y)**2


def find_nearest(world, pt, type):
   oftype = [(e, distance_sq(pt, entities.get_position(e)))
      for e in world.entities if isinstance(e, type)]

   return nearest_entity(oftype)


def add_entity(world, entity):
   pt = entities.get_position(entity)
   if within_bounds(world, pt):
      old_entity = occ_grid.get_cell(world.occupancy, pt)
      if old_entity != None:
         entities.clear_pending_actions(old_entity)
      occ_grid.set_cell(world.occupancy, pt, entity)
      world.entities.append(entity)


def move_entity(world, entity, pt):
   tiles = []
   if within_bounds(world, pt):
      old_pt = entities.get_position(entity)
      occ_grid.set_cell(world.occupancy, old_pt, None)
      tiles.append(old_pt)
      occ_grid.set_cell(world.occupancy, pt, entity)
      tiles.append(pt)
      entities.set_position(entity, pt)

   return tiles


def remove_entity(world, entity):
   remove_entity_at(world, entities.get_position(entity))


def remove_entity_at(world, pt):
   if (within_bounds(world, pt) and
      occ_grid.get_cell(world.occupancy, pt) != None):
      entity = occ_grid.get_cell(world.occupancy, pt)
      entities.set_position(entity, point.Point(-1, -1))
      world.entities.remove(entity)
      occ_grid.set_cell(world.occupancy, pt, None)


def schedule_action(world, action, time):
   world.action_queue.insert(action, time)


def unschedule_action(world, action):
   world.action_queue.remove(action)


def update_on_time(world, ticks):
   tiles = []

   next = world.action_queue.head()
   while next and next.ord < ticks:
      world.action_queue.pop()
      tiles.extend(next.item(ticks))  # invoke action function
      next = world.action_queue.head()

   return tiles


def get_background_image(world, pt):
   if within_bounds(world, pt):
      return entities.get_image(occ_grid.get_cell(world.background, pt))


def get_background(world, pt):
   if within_bounds(world, pt):
      return occ_grid.get_cell(world.background, pt)


def set_background(world, pt, bgnd):
   if within_bounds(world, pt):
      occ_grid.set_cell(world.background, pt, bgnd)


def get_tile_occupant(world, pt):
   if within_bounds(world, pt):
      return occ_grid.get_cell(world.occupancy, pt)


def get_entities(world):
   return world.entities
