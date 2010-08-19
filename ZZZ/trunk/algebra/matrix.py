"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from copy import deepcopy

class Matrix(list):
    def __str__(self):
        """
        string representation
        """
        ret = ""
        for row in self:
            for col in row:
                ret += str(col) + " "
            ret += "\n"
        return ret
    
    def __add__ (self, other):
        """
        add operator
        @param other: another Matrix instance.
        """
        assert(issubclass(type(other), Matrix))
        
        newMatrix = deepcopy(self)
        for i in range(len(self)):
            for j in range(len(self[i])):
                newMatrix[i][j] += other[i][j]
        return Matrix(newMatrix)
    
    def __sub__ (self, other):
        """
        subtraction operator
        @param other: another Matrix instance.
        """
        assert(issubclass(type(other), Matrix))
        
        newMatrix = deepcopy(self)
        for i in range(len(self)):
            for j in range(len(self[i])):
                newMatrix[i][j] -= other[i][j]
        return Matrix(newMatrix)
    
    def __mul__ (self, other):
        """
        multiplication operator
        @param other: another Matrix instance.
        """
        assert(issubclass(type(other), Matrix))
        
        newMatrix = []
        for i in range(len(self)):
            newMatrix.append([])
        for k in range(len(self)):
            for i in range(len(self)):
                item = 0
                for j in range(len(self[i])):
                    item += self[k][j]*other[j][i]
                newMatrix[k].append(item)
        return Matrix(newMatrix)
    
    def transpose(self):
        """
        returns the transpose matrix.
        """
        newMatrix = []
        for i in range(len(self)):
            newMatrix.append([])
        for i in range(len(self)):
            for j in range(len(self)):
                newMatrix[j].append(self[i][j])
        return Matrix(newMatrix)
    
    def determinant(self):
        """
        Returns the matrix determinant.
        """
        if len(self) == 2:
            return self[0][0]*self[1][1] - self[1][0]*self[0][1]
        elif len(self) > 2:
            value=None
            for i in range(len(self)):
                newMatrix = []
                for j in range(len(self)):
                    if i == j: continue
                    newMatrix.append(self[j][1:])
                newMatrix = Matrix(newMatrix)
                if value == None:
                    value=self[i][0]*newMatrix.determinant()
                elif i%2 == 0:
                    value+=self[i][0]*newMatrix.determinant()
                else:
                    value-=self[i][0]*newMatrix.determinant()
            return value
        else:
            return None
    
    def isQuadratic (self):
        """
        returns wether this is a quadratic matrix.
        """
        rows = len(self)
        for i in range(rows):
            if len(self[i]) != rows:
                return False
        return True
        
    def isUnitMatrix (self):
        """
        returns wether this is a unit matrix.
        """
        if not self.isQuadratic():
            return False
        
        currentCol = 0
        for i in range(len(self)):
            for j in range(len(self[i])):
                if currentCol == j and currentCol == i:
                    if self[i][j] != 1:
                        return False
                else:
                    if self[i][j] != 0:
                        return False
            currentCol+=1
        return True
    
    def toUnitForm (self, matrixes=[], pictures=[]):
        """
        tries to form matrix to unit form, also applying all transformations
        to matrixes and pictures.
        @param matrix: The matrix to transform to unit form.
        @param matrixes: Other matrixes to apply the transformations on,
                        for example usefull for the inverted matrix of @matrix.
        @param pictures: List of vectors that may can be created by @matrix.
        """
        def switchRows (matrixes, pictures, aRowIndex, bRowIndex):
            """
            switches two rows.
            @param matrixes: Matrixes to switch the rows on.
            @paran pictures: Pictures to switch the row on.
            @param aRowIndex: index of a row (should be valid)
            @param bRowIndex: index of another row (should be valid)
            """
            for m in matrixes+pictures:
                buf = m[aRowIndex]
                m[aRowIndex] = m[bRowIndex]
                m[bRowIndex] = buf
        def devideRow (matrixes, pictures, rowIndex, factor):
            """
            multiplicates row with a factor.
            @param matrixes: The matrixes to devide the rows on.
            @param pictures: The pictures to switch the rows on.
            @param rowIndex: Index of the row.
            @param factor: devision factor.
            """
            for p in pictures:
                p[rowIndex] /= factor
            
            for m in matrixes:
                for i in range(len(m[rowIndex])):
                    m[rowIndex][i] /= factor
        def addRow (matrixes, pictures, fromIndex, toIndex, factor):
            """
            adds two rows.
            @param matrixes: List of matrixes to add the rows on.
            @param pictures: List of pictures to add the rows on.
            @param fromIndex: Index of the row wich sould be added to another row.
            @param toIndex: Index of the row to add.
            @param factor: The factor for addition.
            """
            for p in pictures:
                p[toIndex] += factor*p[fromIndex]
            
            for m in matrixes:
                for i in range(len(m[toIndex])):
                    m[toIndex][i] += factor*m[fromIndex][i]
        def toUnitFormReal (matrixes, pictures, currentRow=0, currentCol=0):
            """
            tries to form matrixes[0] to unit form, also applying all transformations
            to matrixes[1:] and pictures.
            @param matrixes: Matrixes to apply the transformations on,
                            matrixes[0] is the actual matrix we want the unit form for.
                            for example usefull for the inverted matrix of @matrix.
            @param pictures: List of vectors that may can be created by @matrixes[0].
            """
            # the matrix we actually wanna get the unit form for
            matrix = matrixes[0]
            
            rows = len(matrix)
            cols = len(matrix[0])
            
            # we are out of the matrix
            if currentRow >= rows or currentCol >= cols:
                return matrix
            
            if matrix[currentRow][currentCol] == 0:
                """
                try to find a row with currentCol != 0.
                otherwise we cannot calculate the coefficient for this col!
                """
                for i in range(currentRow+1, len(matrix)):
                    if i == currentRow:
                        continue
                    if matrix[i][currentCol] != 0:
                        switchRows(matrixes, pictures, currentRow, i)
                        return toUnitFormReal(matrixes, pictures, currentRow, currentCol)
                # skip the current col, because its zero only
                return toUnitFormReal(matrixes, pictures, currentRow, currentCol+1)
            else:
                devideRow(matrixes, pictures, currentRow, matrix[currentRow][currentCol])
                for i in range(len(matrix)):
                    if i == currentRow:
                        continue
                    factor = matrix[i][currentCol]
                    if factor != 0:
                        addRow(matrixes, pictures, currentRow, i, -factor)
                return toUnitFormReal(matrixes, pictures, currentRow+1, currentCol+1)
        matrix = deepcopy(self)
        # do some validation checks
        for pic in pictures:
            assert(len(pic) == len(matrix))
        for m in matrixes:
            assert(len(m) == len(matrix))
            assert(len(m[0]) == len(matrix[0]))
        return toUnitFormReal([matrix]+matrixes, pictures)
    
    def invert(self):
        """
        Returns the inverted matrix,
        or None if the matrix is not invertable.
        """
        # none quadratic matrixes are not invertable
        if not self.isQuadratic():
            return None
        
        rows = len(self)
        unitMatrix = Matrix([])
        currentCol = 0
        for i in range(rows):
            unitMatrix.append([])
            for j in range(rows):
                if currentCol == j:
                    unitMatrix[i].append(1)
                else:
                    unitMatrix[i].append(0)
            currentCol+=1
        
        solvedMatrix = self.toUnitForm([unitMatrix])
        
        if solvedMatrix.isUnitMatrix():
            return unitMatrix
        else:
            return None
    
    def rank(self):
        """
        Returns the matrix rank.
        """
        solvedMatrix = self.toUnitForm()
        rank = 0
        # count rows != 0
        for i in range(len(solvedMatrix)):
            for j in range(len(solvedMatrix[i])):
                if solvedMatrix[i][j] != 0:
                    rank += 1
                    break
        return rank
    
    
    
    def solveWithGauss(self, b):
        # TODO
        pass
    
    def solveWithCramer(self, b):
        """
        Returns coefficients for the given picture b.
        If the matrix is not solvable, None is returned.
        @param b: the picture.
        """
        det = self.determinant()
        # matrix is not solvable
        if det == 0: return None
        coefficients=[]
        for i in range(len(self)):
            m = deepcopy(self)
            for j in range(len(self)):
                m[j][i] = b[j]
            coefficients.append(Matrix(m).determinant()/det)
        return coefficients
    
    def solve(self, b):
        """
        Returns coefficients for the given picture b.
        If the matrix is not solvable, None is returned.
        @param b: the picture.
        """
        return self.solveWithCramer(b)

""" stdin parsing """

from expression.expression import Expression

def matrixFromString():
    from sys import stdin
    
    string = stdin.read()
    matrix = []
    lastRow = []
    lastItem = ""
    picture = []
    for character in string:
        # next row
        if character == "\n":
            if lastItem != "":
                picture.append(Expression(lastItem))
                lastItem = ""
            else:
                picture.append(lastRow[-1])
                lastRow.remove(lastRow[-1])
            matrix.append(lastRow)
            lastRow =[]
            continue
        # next item
        if character == " " or character == "\t":
            if lastItem != "":
                lastRow.append(Expression(lastItem))
                lastItem = ""
            continue
        lastItem += character
    return (Matrix(matrix), picture)

if __name__ == "__main__":
    (matrix, picture) = matrixFromString()
    coefficients = matrix.solve(picture)
    print str(coefficients)

