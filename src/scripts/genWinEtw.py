
## Licensed to the .NET Foundation under one or more agreements.
## The .NET Foundation licenses this file to you under the MIT license.
## See the LICENSE file in the project root for more information.
#

import os 
from genXplatEventing import * 

stdprolog="""
// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.
// See the LICENSE file in the project root for more information.

/******************************************************************

DO NOT MODIFY. AUTOGENERATED FILE.
This file is generated using the logic from <root>/src/scripts/genWinEtw.py

******************************************************************/

"""
import argparse
import sys
import xml.dom.minidom as DOM

def generateEtwMacroHeader(sClrEtwAllMan, sExcludeFile,macroHeader,inHeader):
    tree                      = DOM.parse(sClrEtwAllMan)
    numOfProviders            = len(tree.getElementsByTagName('provider'))
    nMaxEventBytesPerProvider = 64
    
    exclusionInfo = parseExclusionList(sExcludeFile)
    incDir = os.path.dirname(os.path.realpath(macroHeader))
    if not os.path.exists(incDir):
        os.makedirs(incDir)
    
    outHeader    = open(macroHeader,'w')
    outHeader.write(stdprolog + "\n")

    outHeader.write("#include \"" + os.path.basename(inHeader) + '"\n')
    outHeader.write("#define NO_OF_ETW_PROVIDERS " + str(numOfProviders) + "\n")
    outHeader.write("#define MAX_BYTES_PER_ETW_PROVIDER " + str(nMaxEventBytesPerProvider) + "\n")
    outHeader.write("EXTERN_C __declspec(selectany) const BYTE etwStackSupportedEvents[NO_OF_ETW_PROVIDERS][MAX_BYTES_PER_ETW_PROVIDER] = \n{\n")

    for providerNode in tree.getElementsByTagName('provider'):
        stackSupportedEvents = [0]*nMaxEventBytesPerProvider
        eventNodes = providerNode.getElementsByTagName('event')
        eventProvider    = providerNode.getAttribute('name')

        for eventNode in eventNodes:
            taskName                = eventNode.getAttribute('task')
            eventSymbol             = eventNode.getAttribute('symbol')
            eventTemplate           = eventNode.getAttribute('template')
            eventTemplate           = eventNode.getAttribute('template')
            eventValue              = int(eventNode.getAttribute('value'))
            eventIndex              = eventValue // 8
            eventBitPositionInIndex = eventValue % 8
            
            eventStackBitFromNoStackList       = int(getStackWalkBit(eventProvider, taskName, eventSymbol, exclusionInfo.nostack))
            eventStackBitFromExplicitStackList = int(getStackWalkBit(eventProvider, taskName, eventSymbol, exclusionInfo.explicitstack))

            # Shift those bits into position.  For the explicit stack list, swap 0 and 1, so the eventValue* variables
            # have 1 in the position iff we should issue a stack for the event.
            eventValueUsingNoStackListByPosition = (eventStackBitFromNoStackList << eventBitPositionInIndex)
            eventValueUsingExplicitStackListByPosition = ((1 - eventStackBitFromExplicitStackList) << eventBitPositionInIndex)

            # Commit the values to the in-memory array that we'll dump into the header file
            stackSupportedEvents[eventIndex] = stackSupportedEvents[eventIndex] | eventValueUsingNoStackListByPosition;
            if eventStackBitFromExplicitStackList == 0:
                stackSupportedEvents[eventIndex] = stackSupportedEvents[eventIndex] | eventValueUsingExplicitStackListByPosition
        
        # print the bit array
        line = []
        line.append("\t{")
        for elem in stackSupportedEvents:
            line.append(str(elem))
            line.append(", ")
        
        del line[-1]
        line.append("},")
        outHeader.write(''.join(line) + "\n")
    outHeader.write("};\n")
    
    outHeader.close()


def generateEtwFiles(sClrEtwAllMan, exclusionListFile, etmdummyHeader, macroHeader, inHeader):

    checkConsistency(sClrEtwAllMan, exclusionListFile)
    generateEtmDummyHeader(sClrEtwAllMan, etmdummyHeader)
    generateEtwMacroHeader(sClrEtwAllMan, exclusionListFile, macroHeader, inHeader)

def main(argv):

    #parse the command line
    parser = argparse.ArgumentParser(description="Generates the Code required to instrument LTTtng logging mechanism")

    required = parser.add_argument_group('required arguments')
    required.add_argument('--man',  type=str, required=True,
                                    help='full path to manifest containig the description of events')
    required.add_argument('--exc',  type=str, required=True,
                                    help='full path to exclusion list')
    required.add_argument('--eventheader',  type=str, required=True,
                                    help='full path to the header file')
    required.add_argument('--macroheader',  type=str, required=True,
                                    help='full path to the macro header file')
    required.add_argument('--dummy',  type=str, required=True,
                                    help='full path to  file that will have dummy definitions of FireEtw functions')

    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print('Unknown argument(s): ', ', '.join(unknown))
        return const.UnknownArguments

    sClrEtwAllMan     = args.man
    exclusionListFile = args.exc
    inHeader          = args.eventheader
    macroHeader       = args.macroheader
    etmdummyHeader    = args.dummy

    generateEtwFiles(sClrEtwAllMan, exclusionListFile, etmdummyHeader, macroHeader, inHeader)

if __name__ == '__main__':
    return_code = main(sys.argv[1:])
    sys.exit(return_code)
