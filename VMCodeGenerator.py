#
#VMCodeGenerator.py
#
#
# Ryan Sowers
#
# CS2002   Project 8 Virtual Machine (part 2)
#
# Fall 2017
# last updated 28 Sept 2017
#

from VMParser import *

#constants only used in this file, so I located them outside the class boundary
T_STATIC = 'static'
T_CONSTANT = 'constant'
T_POINTER = 'pointer'
T_TEMP = 'temp'

SEGMENT_MAP = {  'argument' : 'ARG',
                    'local' : 'LCL',
                     'this' : 'THIS',
                     'that' : 'THAT',
                  T_POINTER : 3,
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
    NO_INIT_FOR_TESTS = ['BasicLoop', 'FibonacciSeries', 'SimpleFunction']

############################################
# Constructor    
    def __init__(self, filePath):       

        #fileName is used for static partition name creation
        self.fileName = filePath.name
                                
        self.currentFunction = None

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


              'label' : self.__generateLabel__,
               'goto' : self.__generateGoto__,
            'if-goto' : self.__generateIf__,

           'function' : self.__generateFunction__,
               'call' : self.__generateCall__,
             'return' : self.__generateReturn__
        }

        

############################################
# static class methods
#    these methods are owned by the Class not one instance
#    note they do not have self as the first argument and they have the @staticmethod tag


    @staticmethod
    def __getSimpleLabel__():
        ''' A static utility method useful for creating arbitrary unique labels when the required label
            was not provided by the VM code. '''

        result = 'L' + str(VMCodeGenerator.labelID)
        VMCodeGenerator.labelID += 1
        
        return result




############################################
# instance methods

    def translateLine(self, line):
        ''' this is how we prevent VMtoMnemonics from having to twiddle,
            we do the translation task here and return the result'''

        command = VMParser.command(line)            
        return self.tokenToCommandDict[command](line)
         

    def generateInit(self): 
        ''' Generation Hack assembler code for program initialization:
                SP = 256.
                pointers = true (LCL, ARG, THIS, THAT to -1)
                Call Sys.Init()
                place Termination loop'''

        lines = []
        lines.append('//generateInit')

        if self.fileName not in VMCodeGenerator.NO_INIT_FOR_TESTS:
            ##bootstrap section from book

            ##### not invoked for first 3 examples
            
            lines.extend(['@256', 'D=A', '@SP', 'M=D'])             # SP = 256
            lines.extend(self.__generatePointerInitializer__())     # initialize LCL, ARG, THIS, THAT to -1

            lines.extend(self.__generateCall__('call Sys.init 0'))  # call Sys.init

            lines.append('(TERMINAL_LOOP)')                         # terminal loop protection
            lines.append('@TERMINAL_LOOP')
            lines.append('0;JMP')

            ##### end not invoked for first 3 examples

        return lines 




############################################
# private/utility methods

    def __arithmetic__(self, line):
                             
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

        lines = []        

        tempLabel = VMCodeGenerator.__getSimpleLabel__()    # generate a unique label for this call of __conditional__()
        labelJumpToEnd = 'END' + tempLabel
        labelJumpIfTrue = 'IF_TRUE' + tempLabel

        lines.extend(self.__popStacktoD__())
        lines.extend(['A=A-1', 'D=M-D', '@' + labelJumpIfTrue, 'D;J' + VMParser.command(line).upper(), 'D=0', \
            '@' + labelJumpToEnd, '0;JMP', '(' + labelJumpIfTrue + ')', 'D=-1', '(' + labelJumpToEnd + ')', '@SP', 'A=M-1', 'M=D'])
         
        return lines



    def __push__(self, line):
        
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



    ##############################################
    # New stuff for project 8
    #
    # \/  \/  \/  \/  \/  \/
    #

    

    def __mangleLabelText__(self, label):
        ''' Creates globally unique label text and returns it.

            -label is a string which requires mangling to ensure uniqueness
              per fig 8.6 standard (pg. 164)'''

        label = str(self.currentFunction) + '$' + label        # create label for labels inside functions

        return label



    def __generateLabel__(self, line):
        ''' Translate a label command. 
            
            -line is the whole command, arg1 of the line is the label we need
              to mangle to ensure uniqueness

            returns a list of assembler instructions that contains a proper and unique label command'''
        
        lines = []

        result = "(" + self.__mangleLabelText__(VMParser.arg1(line)) + ")"
        lines.append(result)

        return lines



    def __generateGoto__(self, line):
        ''' Translate a goto command.

            -line is the whole command, arg1 of the line is the label of the destination
              which requires proper mangling to match its assembly (label)

            returns a list of assembler instructions '''

        lines = []

        result = self.__mangleLabelText__(VMParser.arg1(line))
        lines.extend(['@' + result])
        lines.extend(["0;JMP"])

        return lines


    def __generateIf__(self, line):
        ''' Translate an if-goto command.

            -line is the whole command, arg1 of the line is the the label of the destination
              which requires proper mangling to match its assembly (label)

            returns a list of assembler instructions '''

        lines = []

        result = self.__mangleLabelText__(VMParser.arg1(line))
        lines.extend(self.__popStacktoD__())
        lines.extend(['@' + result])
        lines.extend(["D;JNE"])

        return lines



    def __generateCall__(self, line):
        ''' Translate a call command.

            -line is the whole command, arg1 of the line is the name of the called function
              arg2 of the line is the number of arguments to the called function

            returns a list of assembler instructions '''

        lines = []

        nArgs = VMParser.arg2(line)
        funcName = VMParser.arg1(line)
        returnAddress = 'returnAddress' + self.__getSimpleLabel__()

        lines.extend(['@' + returnAddress, 'D=A'])       # push returnAddress
        lines.extend(self.__pushDtoStack__())
        lines.extend(self.__generatePointerSaver__())    # helper function
        lines.extend(['@SP', 'D=M', '@5', 'D=D-A', '@' + nArgs, 'D=D-A', '@ARG', 'M=D'])    # ARG = SP - 5 - nArgs
        lines.extend(['@SP', 'D=M', '@LCL', 'M=D'])      # LCL = SP
        lines.extend(['@' + funcName, '0;JMP'])          # goto funcName
        lines.extend(['(' + returnAddress + ')'])        # returnAddress label

        return lines



    def __generateFunction__(self, line):
        ''' Translate a function command.

            -line is the whole command, arg1 of the line is the name of the defined function
              arg2 of the line is the number of local variables in the defined function

            returns a list of assembler instructions '''

        lines = []

        self.currentFunction = VMParser.arg1(line)
        funcName = ['(' + VMParser.arg1(line) + ')']
        localVars = int(VMParser.arg2(line))

        lines.extend(funcName)
        while localVars:
            lines.extend(['@0', 'D=A'])
            lines.extend(self.__pushDtoStack__())
            localVars -= 1
        
        return lines



    def __generateReturn__(self, unused):
        ''' Translate a return command.

            -unused is exactly what it says, it is required only for consistency in dynamic function
              calling.

            returns a list of assembler instructions '''
        
        lines = []

        lines.extend(['@LCL', 'D=M', '@R13', 'M=D'])                            # endFrame = LCL
        lines.extend(['@R13', 'D=M', '@5', 'A=D-A', 'D=M', '@R14', 'M=D'])      # retAddress = *(endFrame - 5)
        lines.extend(self.__popStacktoD__())
        lines.extend(['@ARG', 'A=M', 'M=D'])                                    # *ARG = pop()
        lines.extend(['@ARG', 'D=M+1', '@SP', 'M=D'])                           # *SP  = *ARG + 1
        lines.extend(self.__generateFrameSlider__())                            # helper function
        lines.extend(['@R14', 'A=M', '0;JMP'])                                  # goto retAddress

        return lines




    #TODO helper function(s) as required
    #
    # Don't
    # Repeat
    # Yourself
    #
    #there is at least one required

    def __generateFrameSlider__(self):
        lines = []
        pointerList = ['THAT', 'THIS', 'ARG', 'LCL']

        for i in range(1,5):
            lines.extend(['@R13', 'D=M', '@' + str(i), 'A=D-A', 'D=M', '@' + pointerList[i-1], 'M=D'])

        return lines


    def __generatePointerSaver__(self):
        lines = []
        pointerList = ['LCL', 'ARG', 'THIS', 'THAT']

        for i in range(0,4):
            lines.extend(['@' + pointerList[i], 'D=M'])            
            lines.extend(self.__pushDtoStack__())

        return lines


    def __generatePointerInitializer__(self):
        lines = []
        pointerList = ['LCL', 'ARG', 'THIS', 'THAT']

        for i in range(0,4):
            lines.extend(['D=-1', '@' + pointerList[i], 'M=D'])

        return lines           
            
       



























