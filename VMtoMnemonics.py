#
#VMtoMnemonics.py
#
# Ryan Sowers
#
# CS2002   Project 8 Virtual Machine (part 2)
#
# Fall 2017
# last updated 28 Sept 2017
#

import sys  #for grading server
from pathlib import *

from VMParser import *
from VMCodeGenerator import *


class VMtoMnemonics(object):

##########################################
#Constructor

    #there are no changes to the constructor
    def __init__(self, targetPath):

        self.targetPath = Path(targetPath)

        if self.targetPath.is_dir():
            self.outputFilePath = self.targetPath / (self.targetPath.name + '.asm')

        else:
            if self.targetPath.suffix == '.vm':
                self.outputFilePath = Path(self.targetPath.parent / (self.targetPath.stem + '.asm'))

            else:
                raise RuntimeError( "error, cannot use the filename: " + targetPath )

            
          
##########################################
#public methods


    def process(self):
        ''' processes a directory or a single file, returning the translated  assembly code. '''
        

        #this is almost the same as your project 7 process() function
        #  you need to handle calling generateInit() exactly once per program translated
        #  and note that generateTermination() is replaced by functionality inside generateInit()
        
        assemblyCode = []

        assemblyCode.extend(VMCodeGenerator(self.targetPath).generateInit())    # generateInit at beginning of process

        if self.targetPath.is_dir():
            for file in self.targetPath.iterdir(): 
                if file.suffix == '.vm':            # process .vm files in a directory
                    assemblyCode.extend(self.__processFile__(file))
        else:
            if self.targetPath.suffix == '.vm':     # process .vm files in target path
                file = self.targetPath
                assemblyCode.extend(self.__processFile__(file))

        return self.__output__(assemblyCode)



##########################################
#private methods


    def __processFile__(self, filePath):
        ''' processes a single file, returning the translated assembler. '''

        assemblyCode = []

        parser = VMParser(filePath)
        codeGen = VMCodeGenerator(filePath)
        command = parser.advance()

        while (command):                            # for each command line, translate it
            Tline = codeGen.translateLine(command)
            assemblyCode.extend(Tline)
            command = parser.advance()
                
        return assemblyCode

        
        
    def __output__(self, codeList):
        ''' outpute the machine code codeList into a file and returns the filename'''
           
        file = open(str(self.outputFilePath),"w")
        file.write("\n".join(codeList))
        file.close()
        return str(self.outputFilePath)

    

 
#################################
#################################
#################################
#this kicks off the program and assigns the argument to a variable
#
if __name__=="__main__":

    target = sys.argv[1]     # use this one for final deliverable

    
##    target = 'ProgramFlow/BasicLoop'          # test 1  for internal IDLE testing only -- PASS
##    target = 'ProgramFlow/FibonacciSeries'    # test 2  for internal IDLE testing only -- PASS
##    target = 'FunctionCalls/SimpleFunction'   # test 3  for internal IDLE testing only -- PASS
##    target = 'FunctionCalls/NestedCall'       # test 4  for internal IDLE testing only -- PASS?
##    target = 'FunctionCalls/FibonacciElement' # test 5  for internal IDLE testing only
##    target = 'FunctionCalls/StaticsTest'      # test 6  for internal IDLE testing only

    translator = VMtoMnemonics(target)
    print('\n' + str( translator.process() ) + ' has been translated.')



