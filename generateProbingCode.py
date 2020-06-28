# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 09:18:05 2020

@author: llihes4
"""
from collections import namedtuple

Point2D = namedtuple('Point2D', 'x y')

CORNER_LOWER_LEFT = Point2D(30, 30+40)
CORNER_UPPER_RIGHT = Point2D(500-30, 400-30+40)
GRID_POINTS = 3

RANGE_X = CORNER_UPPER_RIGHT.x - CORNER_LOWER_LEFT.x
RANGE_Y = CORNER_UPPER_RIGHT.y - CORNER_LOWER_LEFT.y
GRID_SEGMENT_LENGTH_X = RANGE_X / (GRID_POINTS - 1)
GRID_SEGMENT_LENGTH_Y = RANGE_Y / (GRID_POINTS - 1)

PAUSE_TIME = 40 # [s] paus etime between moves

outputFile = open("probingCode.gcode", "w+")

outputFile.write("G28\n")
outputFile.write("G1 F5000\n")

for i in range(0, GRID_POINTS):
    for j in range(0, GRID_POINTS):
        outputFile.write("G1 X" + str(CORNER_LOWER_LEFT.x + GRID_SEGMENT_LENGTH_X * j) + " Y" +  str(CORNER_LOWER_LEFT.y + GRID_SEGMENT_LENGTH_Y * i) + "\n")
        outputFile.write("G1 Z0.1 \n")
        outputFile.write("G4 P" + str(PAUSE_TIME * 1000)  + "\n")
        outputFile.write("G1 Z5 \n")

outputFile.close()