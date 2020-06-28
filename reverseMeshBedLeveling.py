# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 17:09:10 2020

@author: stefa

TODO:
    - what happens at z hop?
    - more slicer compatibility
    

"""
import re
from collections import namedtuple
from typing import Tuple

Point2D = namedtuple('Point2D', 'x y')
GCodeLine = namedtuple('GCodeLine', 'x y z e f')


INPUT_FILE_NAME = "256W7520-1W09_001_lable_neu.gcode"
OUTPUT_FILE_NAME = "RML_" + INPUT_FILE_NAME 

CORNER_LOWER_LEFT = Point2D(30, 30+40)
CORNER_UPPER_RIGHT = Point2D(500-30, 400-30+40)
GRID_POINTS = 3
EXTRAPOLATE = 1 #Extrapolate beyond the measured points (e.g. corners)
DISCRETIZATION_LENGTH = 10 # [mm] Subdivision Length
FADE_LAYERS = 10 # Number of layers in which the leveling is used and slowly faded to zero

LEVELING_OFFSET = 0.1 #offset used during leveling e.g. what was the z-height when you measured the HEIGHT_VALUES
HEIGHT_VALUES = [.23, .11, .16,   .11, .11, .17,  .38, .42, .44] #measured distances from the nozzle at the leveling points

RANGE_X = CORNER_UPPER_RIGHT.x - CORNER_LOWER_LEFT.x
RANGE_Y = CORNER_UPPER_RIGHT.y - CORNER_LOWER_LEFT.y
GRID_SEGMENT_LENGTH_X = RANGE_X / (GRID_POINTS - 1)
GRID_SEGMENT_LENGTH_Y = RANGE_Y / (GRID_POINTS - 1)


def bilinear_interpolation(Q11: Point2D, Q22: Point2D, h_Q11, h_Q21, h_Q12, h_Q22, targetPoint: Point2D) -> float:
    return 1 / ((Q22.x-Q11.x) * (Q22.y-Q11.y)) * (\
                 h_Q11 * (Q22.x - targetPoint.x) * (Q22.y - targetPoint.y) + \
                 h_Q21 * (targetPoint.x - Q11.x) * (Q22.y - targetPoint.y) + \
                 h_Q12 * (Q22.x - targetPoint.x) * (targetPoint.y - Q11.y) + \
                 h_Q22 * (targetPoint.x - Q11.x) * (targetPoint.y - Q11.y))
    
def getXY(currentLine: str) -> Point2D:
    searchX = re.search(r"X(\d*\.?\d*)", currentLine)
    searchY = re.search(r"Y(\d*\.?\d*)", currentLine)
    elementX = searchX.group(1)
    elementY = searchY.group(1)
    return Point2D(float(elementX), float(elementY))

def parseGCode(currentLine: str) -> GCodeLine:
    thisLine = re.compile('(?i)^[gG][0-3](?:\s+x-?(?P<x>[0-9.]{1,15})|\s+y-?(?P<y>[0-9.]{1,15})|\s+z-?(?P<z>[0-9.]{1,15})|\s+e-?(?P<e>[0-9.]{1,15})|\s+f-?(?P<f>[0-9.]{1,15}))*')
    lineEntries = thisLine.match(currentLine)
    if lineEntries:
        return GCodeLine(lineEntries.group('x'), lineEntries.group('y'), lineEntries.group('z'), lineEntries.group('e'), lineEntries.group('f'))
    

def getDistance(p1: Point2D, p2: Point2D) -> float:
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2) ** 0.5

def getMeshSquare(pos: Point2D):
    #column
    col = (pos.x - CORNER_LOWER_LEFT.x) // GRID_SEGMENT_LENGTH_X
    if EXTRAPOLATE == 1:
        if col < 0:
            col = 0
        if col > GRID_POINTS - 2:
            col = GRID_POINTS - 2
        
    # row
    row = (pos.y - CORNER_LOWER_LEFT.y) // GRID_SEGMENT_LENGTH_Y
    if EXTRAPOLATE == 1:
        if row < 0:
            row = 0
        if row > GRID_POINTS - 2:
            row = GRID_POINTS - 2
    
    return [int(col),int(row)]

def getZOffset(currentPosition: Point2D, currentLayer: int) -> float:
    meshSquare = getMeshSquare(currentPosition)
    if EXTRAPOLATE == 0:
        if meshSquare[0] < 0:
            currentPosition = currentPosition._replace(x = CORNER_LOWER_LEFT.x)
            meshSquare[0] = 0
        if meshSquare[0] > (GRID_POINTS - 2):
            currentPosition = currentPosition._replace(x = CORNER_UPPER_RIGHT.x)
            meshSquare[0] = (GRID_POINTS - 2)
        if meshSquare[1] < 0:
            currentPosition = currentPosition._replace(y = CORNER_LOWER_LEFT.y)
            meshSquare[1] = 0
        if meshSquare[1] > (GRID_POINTS - 2):
            currentPosition = currentPosition._replace(y = CORNER_UPPER_RIGHT.y)
            meshSquare[1] = (GRID_POINTS - 2)
            
    return (bilinear_interpolation(Point2D(CORNER_LOWER_LEFT.x + meshSquare[0] * GRID_SEGMENT_LENGTH_X , CORNER_LOWER_LEFT.y + meshSquare[1] * GRID_SEGMENT_LENGTH_Y), \
                                     Point2D(CORNER_LOWER_LEFT.x + (meshSquare[0] + 1) * GRID_SEGMENT_LENGTH_X , CORNER_LOWER_LEFT.y + (meshSquare[1] + 1) * GRID_SEGMENT_LENGTH_Y), \
                                     HEIGHT_VALUES[meshSquare[0] + GRID_POINTS * meshSquare[1]], \
                                     HEIGHT_VALUES[meshSquare[0] + GRID_POINTS * meshSquare[1] + 1] , \
                                     HEIGHT_VALUES[meshSquare[0] + GRID_POINTS * meshSquare[1] + GRID_POINTS], \
                                     HEIGHT_VALUES[meshSquare[0] + GRID_POINTS * meshSquare[1] + GRID_POINTS + 1], \
                                     currentPosition) - LEVELING_OFFSET) * \
                                     ((FADE_LAYERS - currentLayer + 1) / FADE_LAYERS) 
    

def mapRange(a: Tuple[float, float], b: Tuple[float, float], s: float) -> float:
    (a1, a2), (b1, b2) = a, b
    return b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

def writeLine(G, X, Y, Z, F = None, E = None):
    outputSting = "G" + str(int(G)) + " X" + str(round(X,5)) + " Y" + str(round(Y,5)) + " Z" + str(round(Z,3))
    if E is not None:
        outputSting = outputSting + " E" + str(round(float(E),5))
    if F is not None:
        outputSting = outputSting + " F" + str(int(float(F)))
    outputFile.write(outputSting + "\n")


lastPosition = Point2D(0, 0)
currentZ = 0
currentLayer = 0

with open(INPUT_FILE_NAME, "r") as gcodeFile, open(OUTPUT_FILE_NAME, "w+") as outputFile:
        for currentLine in gcodeFile:
            if "; layer " in currentLine and " Z " in currentLine:
                currentZ = float(re.search(r"Z = (\d*\.?\d*)", currentLine).group(1))
                currentLayer = int(re.search(r"layer (\d*)", currentLine).group(1))
            if currentLine[0] == ";":
                outputFile.write(currentLine)
                continue
            currentLineCommands = parseGCode(currentLine)
            #if " X" in currentLine and " Y" in currentLine and ("G1" in currentLine or "G0" in currentLine) and currentLayer <= FADE_LAYERS:
            if currentLineCommands is not None and currentLayer <= FADE_LAYERS:
                if currentLineCommands[0] is None or currentLineCommands[1] is None:
                    outputFile.write(currentLine)
                    continue
                currentPosition = Point2D(float(currentLineCommands[0]), float(currentLineCommands[1]))
                #if " E" in currentLine:
                #if currentLineCommands[3]:
                #   extrusionLength = float(re.search(r"E(\d*\.?\d*)", currentLine).group(1))
                #else:
                #    extrusionLength = None
                    
                if currentLineCommands[4]:
                    outputFile.write("G1 F" + currentLineCommands[4] + "\n")
                segmentLength = getDistance(currentPosition, lastPosition)
                if (segmentLength > DISCRETIZATION_LENGTH):
                    discretizationSteps = segmentLength / DISCRETIZATION_LENGTH
                    segementDirection = Point2D((currentPosition.x - lastPosition.x) / segmentLength * DISCRETIZATION_LENGTH, \
                                                (currentPosition.y - lastPosition.y) / segmentLength * DISCRETIZATION_LENGTH)
                    #if extrusionLength is not None:
                    if currentLineCommands[3]:
                        segmentExtrusion = float(currentLineCommands[3]) * DISCRETIZATION_LENGTH / segmentLength
                    else:
                        segmentExtrusion = None
                    for step in range(int(discretizationSteps)):
                        segmentEnd = Point2D(lastPosition.x + segementDirection.x, lastPosition.y + segementDirection.y)                    
                        zOffset = getZOffset(segmentEnd, currentLayer)
                        
                        writeLine(1,segmentEnd.x, segmentEnd.y, currentZ - zOffset,None,segmentExtrusion)
                        lastPosition = segmentEnd
                    zOffset = getZOffset(currentPosition, currentLayer)
   
                    #if extrusionLength is not None:
                    if currentLineCommands[3]:
                        #segmentExtrusion = extrusionLength * (DISCRETIZATION_LENGTH % segmentLength) / segmentLength
                        segmentExtrusion = float(currentLineCommands[3]) / discretizationSteps * (discretizationSteps % 1)
                    else:
                        segmentExtrusion = None
                    writeLine(1,currentPosition.x, currentPosition.y, currentZ - zOffset,None,segmentExtrusion)
                    lastPosition = currentPosition
                    continue
                
                zOffset = getZOffset(currentPosition, currentLayer)    
            
                writeLine(1,currentPosition.x, currentPosition.y, currentZ - zOffset,None,currentLineCommands[3])
                lastPosition = currentPosition
                    
            else:
                outputFile.write(currentLine)