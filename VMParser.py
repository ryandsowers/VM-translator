#
#VMParser.py
#
# CS2002   Project 7 & 8 Virtual Machine (part 1 & 2)
#
#  Ryan Sowers
#
# Fall 2017
# last updated 28 Sept 2017
#

class VMParser(object):

    # No MAGIC Numbers!!!
    #  refer to these like this example:  VMParser.CMD
    CMD = 0
    ARG1 = 1
    ARG2 = 2

############################################
# Constructor

    def __init__(self, filePath):
        loadedList = self.__loadFile__(str(filePath))
        
        self.toParse = self.__filterFile__(loadedList)        

        
############################################
# static methods
#    these methods are owned by the Class not one instance
#    note they do not have self as the first argument and they have the @staticmethod tag

    @staticmethod
    def command(line):
        ''' returns the line's command as a string'''
        
        splitLine = line.split()
        correctArgNum = (len(splitLine) == 1 or len(splitLine) == 3)    # check for correct number of arguments to process

        if len(splitLine) < VMParser.ARG1:
            result = None
        elif correctArgNum:
            result = splitLine[VMParser.CMD]
        else:
            raise RuntimeError("Invalid number of arguments.")
        
        return result

   
    @staticmethod
    def arg1(line):
        ''' returns the line's first argument as a string'''
        
        splitLine = line.split()
        correctArgNum = (len(splitLine) == 3)       # check for correct number of arguments to process

        if len(splitLine) == VMParser.ARG1:
            result = None
        elif correctArgNum:       
            result = splitLine[VMParser.ARG1]
        else:
            raise RuntimeError("Invalid number of arguments.")
        
        return result


    @staticmethod
    def arg2(line):
        ''' returns the line's second argument as a string '''
        
        splitLine = line.split()
        correctArgNum = (len(splitLine) == 3)       # check for correct number of arguments to process

        if len(splitLine) < 3:
            result = None
        elif correctArgNum:      
            result = splitLine[VMParser.ARG2]
        else:
            raise RuntimeError("Invalid number of arguments.")
        
        return result




############################################
# instance methods



    def advance(self):
        '''reads and returns the next command in the input,
           returns false if there are no more commands.  '''
        if self.toParse:
            return self.toParse.pop(0)
        else:
            return False




############################################
# private/utility methods (unchanged from project 6)

    def __toTestDotTxt__(self):
        '''this is just for outputting our stripped file as a test
           this function will not be active in the final program'''

        file = open("test.txt","w")
        file.write("\n".join(self.toParse))
        file.close() 


    def __loadFile__(self, fileName):
        '''Loads the file into memory.

           -fileName is a String representation of a file name,
           returns contents as a simple List'''
        
        fileList = []
        file = open(fileName,"r")
        
        for line in file:
            fileList.append(line)
            
        file.close()
        
        return fileList   


    def __filterFile__(self, fileList):
        '''Comments, blank lines and unnecessary leading/trailing whitespace are removed from the list.

           -fileList is a List representation of a file, one line per element
           returns the fully filtered List'''
        
        filteredList = []
        
        for line in fileList:
            line = line.strip()                       #leading and trailing whitespace removal
            line = self.__filterOutEOLComments__(line)
            
            if len(line) > 0:                          #empty line removal
                filteredList.append(line)
        
        return filteredList   



    def __filterOutEOLComments__(self, line):
        '''Removes end-of-line comments and and resulting whitespace.

           -line is a string representing single line, line endings already stripped
           returns the filtered line, which may be empty '''

        index = line.find('//')
        if (index >= 0):
            line = line[0:index]

        line = line.strip()

        return line
