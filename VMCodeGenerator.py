#
#VMCodeGenerator.py
#
# CS2002   Project 7 Virtual Machine (part 1)
#
#  Ryan Sowers
#
# Fall 2017
# last updated 28 Sept 2017
#

from VMParser import *

#constants only used in this file
T_STATIC = 'static'
T_CONSTANT = 'constant'
T_POINTER = 'pointer'
T_TEMP = 'temp'

SEGMENT_MAP = {  'argument' : 'ARG',
                    'local' : 'LCL',        # used to drastically collapse the if then else
                     'this' : 'THIS',
                     'that' : 'THAT',
                  T_POINTER : 3,            # pointer is used in multiple places, so delared here again
                     T_TEMP : 5  }

OPERAND_MAP = { 'add' : 'M=M+D',         
                'sub' : 'M=M-D',        
                'neg' : 'M=-M',    
                'and' : 'M=D&M',
                 'or' : 'M=D|M',
                'not' : 'M=!M'   }

  
class VMCodeGenerator(object):
    
############################################
#static class variables
#   these will be shared across multiple instances

    labelID = 0     
    
############################################
# Constructor    
    def __init__(self, filePath):

        #fileName is used for static partition name creation
        self.fileName = filePath.stem       

        #a little functional programming avoids well over 100 lines of code just
        # managing the two-stage lookups
        
        self.tokenToCommandDict = {
    
                'add' : self.__arithmetic__,
                'sub' : self.__arithmetic__,        
                'neg' : self.__arithmetic__,
                'and' : self.__arithmetic__,
                 'or' : self.__arithmetic__,
                'not' : self.__arithmetic__,
            
                 'eq' : self.__conditional__,
                 'gt' : self.__conditional__,
                 'lt' : self.__conditional__,
    
               'push' : self.__push__,
                'pop' : self.__pop__,
        }




############################################
# static class methods
#    these methods are owned by the Class not one instance
#    note they do not have self as the first argument and they have the @staticmethod tag

    @staticmethod
    def generateTermination():
        ''' I am paranoid about running off the edge of the earth and into arbirtary malicious code.
            put a jump to the termination loop at the very bottom of the program
            to prevent any possibility of leaking off the bottom (the edge)'''
        lines = []

        lines.append('(TERMINAL_LOOP)')
        lines.append('@TERMINAL_LOOP')
        lines.append('0;JMP')

        return lines 



    @staticmethod
    def __getSimpleLabel__():
        ''' a static utility method to access the class variable '''
        
        result = 'L' + str(VMCodeGenerator.labelID)
        VMCodeGenerator.labelID += 1
        
        return result



############################################
# instance methods

    def translateLine(self, line):
        ''' this is how we prevent VMtoMnemonics from having to twiddle,
            we do the translation task here and return the result'''

        result = self.tokenToCommandDict[VMParser.command(line)](line)
        
        return result




############################################
# private/utility methods


    def __arithmetic__(self, line):
        ''' Handle generation of Hack assembler code for the basic arithmetic commands
            -line will only contain the arithmetic operation

            returns a list of assembler instructions'''
        
        lines = []

        VMPcommandLine = VMParser.command(line)

        if VMPcommandLine in ('and', 'or', 'add', 'sub'):       # check for binary arithmetic
            lines.extend(self.__popStacktoD__())
            lines.extend(['A=A-1', OPERAND_MAP[VMPcommandLine]])
        elif VMPcommandLine in ('not', 'neg'):                  # check for unary arithmetic
            lines.extend(['@SP', 'A=M-1', OPERAND_MAP[VMPcommandLine]])
        else:
            raise RuntimeError('Error! called VMCodeGenerator.arithmetic() with bad command')
            lines = None

        return lines 




    def __conditional__(self, line):
        ''' Translate basic conditional (lt, gt, eq) commands.

            -command is the boolean comparison operator, Hack VM lang provides it in lowercase,
            
            returns a list of assembler instructions'''
        
        lines = []        

        tempLabel = VMCodeGenerator.__getSimpleLabel__()    # generate a unique label for this call of __conditional__()

        lines.extend(self.__popStacktoD__())
        lines.extend(['A=A-1', 'D=M-D', '@IF_TRUE' + tempLabel, 'D;J' + VMParser.command(line).upper(), 'D=0', \
            '@END' + tempLabel, '0;JMP', '(IF_TRUE' + tempLabel + ')', 'D=-1', '(END' + tempLabel + ')', '@SP', 'A=M-1', 'M=D'])
         
        return lines        




    def __push__(self, line):
        ''' Translate a push command.

            -line is the whole command, arg1 of the line is the segment, arg 2 is the index,

            returns a list of assembler instructions'''
        
        lines = []
        segment = VMParser.arg1(line)
        index = VMParser.arg2(line)

        if segment == T_CONSTANT:                   # check for push constant
            lines.extend(['@' + index, 'D=A'])
            lines.extend(self.__pushDtoStack__())
        elif segment == T_STATIC:                   # check for push static
            lines.extend(['@' + self.fileName + '.' + index, 'D=M'])
            lines.extend(self.__pushDtoStack__())
        elif segment in (T_TEMP, T_POINTER):        # check for push from pointer
            pushLines = self.__pushFromPointer__(SEGMENT_MAP[segment], index)
            lines.extend(pushLines)
        elif segment in SEGMENT_MAP:                # check for other segments
            lines.extend(['@' + index, 'D=A', '@' + SEGMENT_MAP[segment], 'D=M+D', 'A=D', 'D=M'])
            lines.extend(self.__pushDtoStack__())
        else:
            raise RuntimeError('Error! Illegal segment for pushing:', segment)

        return lines


    def __pop__(self, line):
        ''' Translate a pop command.

            -line is the whole command, arg1 of the line is the segment, arg 2 is the index,

            returns a list of assembler instructions'''
        
        lines = []
        segment = VMParser.arg1(line)
        index = VMParser.arg2(line)

        if segment == T_STATIC:                     # check for pop static
            lines.extend(self.__popStacktoD__())
            lines.extend(['@' + self.fileName + '.' + index, 'M=D'])
        elif segment in (T_TEMP, T_POINTER):        # check for pop to pointer
            popLines = self.__popToPointer__(SEGMENT_MAP[segment], index)
            lines.extend(popLines)
        elif segment in SEGMENT_MAP:                # check for other segments
            lines.extend(['@' + SEGMENT_MAP[segment], 'D=M', '@' + index, 'D=D+A', '@R15', 'M=D'])
            lines.extend(self.__popStacktoD__())
            lines.extend(['@R15', 'A=M', 'M=D'])
        else:
            raise RuntimeError('Error! Illegal segment for popping')

        return lines




    def __pushDtoStack__(self):
        lines = []

        lines.extend(['@SP', 'A=M', 'M=D', '@SP', 'M=M+1'])
        
        return lines

        
    def __popStacktoD__(self):
        lines = []

        lines.extend(['@SP', 'AM=M-1', 'D=M'])
        
        return lines


 
    def __popToPointer__(self, pointer, index):
        lines = []

        lines.extend(self.__popStacktoD__())
        lines.extend(['@' + str(pointer + int(index)), 'M=D'])
        
        return lines
        
                
    def __pushFromPointer__(self, pointer, index):
        lines = []

        lines.extend(['@' + str(pointer + int(index)), 'D=M'])
        lines.extend(self.__pushDtoStack__())

        return lines


        



