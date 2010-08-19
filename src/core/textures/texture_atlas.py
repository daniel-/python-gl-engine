# -*- coding: UTF-8 -*-
'''
Created on 06.08.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''


def calculateDynamicTextureAtlas(textures,
                                 numTextures,
                                 atlasSize):
    """
    creates viewports for all specified textures.
    the viewports will fit the atlas entirely, no empty space but stretched textures.
    the viewport size is calculated by this algorithm,
    so the textures do not have influence on their actual size within the atlas.
    
    the slicing is done in favor for the first elements of the textures list.
    if there are viewports with different sizes, the one more at the beginning
    of the input list will have the bigger viewport.
    
    Some example slices are:
    INPUT     -> ROWS IN ATLAS
    -------------------------- 
    [0]       -> [ [0] ]
    [0,1]     -> [ [0], [1] ]
    [0,1,2]   -> [ [0], [1,2] ]
    [0,1,2,3] -> [ [0,1], [2,3] ]
    and so forth ...
    
    @return: one dimensional list of viewports.
    """
    numTextures = len(textures)
    numRows = 1
    mapRows = [[textures[0]]]
    counter = 1
    
    while counter<numTextures:
        shadowMap = textures[counter]
        counter += 1
        
        if counter>numRows**2:
            numRows += 1
            # new row at the top for the first map
            lastRow = []
            mapRows = [ lastRow ] + mapRows
            for i in range( 1, len(mapRows) ):
                newRow = []
                # move the first map one row up
                lastRow.append( mapRows[i][0] )
                # the others move one column left
                for j in range( 1, len(mapRows[i]) ):
                    newRow.append( mapRows[i][j] )
                mapRows[i] = newRow
                lastRow = newRow
        else:
            remainingMaps = counter-1
            for i in range(numRows):
                i = numRows-i-1
                rowMaps = len( mapRows[i] )
                remainingMaps -= rowMaps
                
                # check if there is space left in this row
                if rowMaps<=remainingMaps or remainingMaps==0:
                    for j in range(numRows):
                        j = numRows-j-1
                        # if this is the row with empty space, we are sone
                        if i==j: break
                        # else we move the first element of this row
                        # into the previous row
                        mapRows[j-1].append(mapRows[j][0])
                        mapRows[j] = mapRows[j][1:]
                    break
        
        # append this map to the end of rows
        mapRows[numRows-1].append( shadowMap )
    
    numRowsF = float(numRows)
    # stepsize in vertical direction
    stepH = atlasSize/numRowsF
    # percentage of one step on the texture
    stepHPercent = stepH/atlasSize
    stepH = int(stepH)
    # offset produced by processed rows
    offH = 0.0
    
    viewports = []
    
    for i in range(numRows):
        rowI = mapRows[i]
        numCols = len(rowI)
        numColsF = float( numCols )
        # stepsize in horizontal direction
        stepW = atlasSize/numColsF
        # percentage of one step on the texture
        stepWPercent = stepW/atlasSize
        stepW = int(stepW)
        # offset produced by processed colums of this row
        offW = 0.0
        
        for j in range(numCols):
            viewport = (j*stepW, # x coordinate in atlas
                        i*stepH, # y coordinate in atlas
                        stepW,   # width of this texture
                        stepH,   # height of this texture
                        stepWPercent, # how much percent of the atlas size is the step in x direction 
                        stepHPercent, # how much percent of the atlas size is the step in y direction 
                        float(offW)/atlasSize, # offset percent in x direction
                        float(offH)/atlasSize) # offset percent in y direction
            viewports.append( viewport )
            shadowMap = rowI[j]
            
            offW += stepW
        offH += stepH
    
    return viewports

