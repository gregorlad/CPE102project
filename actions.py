import entities
import worldmodel
import pygame
import math
import random
import point
import image_store




def sign(x):
   if x < 0:
      return -1
   elif x > 0:
      return 1
   else:
      return 0

def adjacent(pt1, pt2):
   return ((pt1.x == pt2.x and abs(pt1.y - pt2.y) == 1) or
      (pt1.y == pt2.y and abs(pt1.x - pt2.x) == 1))

def find_open_around(world, pt, distance):
   for dy in range(-distance, distance + 1):
      for dx in range(-distance, distance + 1):
         new_pt = point.Point(pt.x + dx, pt.y + dy)

         if (worldmodel.within_bounds(world, new_pt) and
            (not worldmodel.is_occupied(world, new_pt))):
            return new_pt

   return None





