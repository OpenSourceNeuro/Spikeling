/**
 * SerialCommand - A Wiring/Arduino library to tokenize and parse commands
 * received over a serial port.
 *
 * Copyright (C) 2022 Dennis Schuett <https://github.com/shyd/Arduino-SerialCommand>
 * Copyright (C) 2018 Mingyu Kim <mingyu@mingyu.co.kr>
 * Copyright (C) 2012 Stefan Rado <https://github.com/kroimon/Arduino-SerialCommand>
 * Copyright (C) 2011 Steven Cogswell <steven.cogswell@gmail.com>
 *                    http://husks.wordpress.com
 * 
 * Version 20221212
 * 
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this library.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "SerialCommand.h"

/**
 * Constructor makes sure some things are set.
 */
SerialCommand::SerialCommand(Stream &print, Stream &debugPrint, char terminator)
  : commandList(NULL),
    commandCount(0),
    defaultHandler(NULL),
    term(terminator),           // default terminator for commands, newline character
    last(NULL)
{
  debugPrinter = &debugPrint; //operate on the address of custom debug serial
  printer = &print; //operate on the address of custom serial
  strcpy(delim, " "); // strtok_r needs a null-terminated string
  clearBuffer();
}

SerialCommand::SerialCommand(Stream &print, char terminator)
  : commandList(NULL),
    commandCount(0),
    defaultHandler(NULL),
    term(terminator),           // default terminator for commands, newline character
    last(NULL)
{
  printer = &print; //operate on the address of custom Serial
  debugPrinter = &print; //operate on the address of custom Serial
  strcpy(delim, " "); // strtok_r needs a null-terminated string
  clearBuffer();
}

SerialCommand::SerialCommand(char terminator)
  : commandList(NULL),
    commandCount(0),
    defaultHandler(NULL),
    term(terminator),           // default terminator for commands, newline character
    last(NULL)
{
  debugPrinter = &Serial; //operate on the address of default Serial
  printer = &Serial; //operate on the address of default Serial
  strcpy(delim, " "); // strtok_r needs a null-terminated string
  clearBuffer();
}


/**
 * Adds a "command" and a handler function to the list of available commands.
 * This is used for matching a found token in the buffer, and gives the pointer
 * to the handler function to deal with it.
 */
void SerialCommand::addCommand(const char *command, void (*function)()) {
  #ifdef SERIALCOMMAND_DEBUG
    debugPrinter->print("Adding command (");
    debugPrinter->print(commandCount);
    debugPrinter->print("): ");
    debugPrinter->println(command);
  #endif

  commandList = (SerialCommandCallback *) realloc(commandList, (commandCount + 1) * sizeof(SerialCommandCallback));
  strncpy(commandList[commandCount].command, command, SERIALCOMMAND_MAXCOMMANDLENGTH);
  commandList[commandCount].function = function;
  commandCount++;
}

/**
 * This sets up a handler to be called in the event that the receveived command string
 * isn't in the list of commands.
 */
void SerialCommand::setDefaultHandler(void (*function)(const char *)) {
  defaultHandler = function;
}


/**
 * This checks the Serial stream for characters, and assembles them into a buffer.
 * When the terminator character (default '\n') is seen, it starts parsing the
 * buffer for a prefix command, and calls handlers setup by addCommand() member
 */
void SerialCommand::readSerial() {
  while (printer->available() > 0) {
    char inChar = printer->read();   // Read single available character, there may be more waiting
    #ifdef SERIALCOMMAND_DEBUG
      debugPrinter->print(inChar);   // Echo back to serial stream
    #endif

    if (inChar == term) {     // Check for the terminator (default '\r') meaning end of command
      #ifdef SERIALCOMMAND_DEBUG
        debugPrinter->print("Received: ");
        debugPrinter->println(buffer);
      #endif

      char *command = strtok_r(buffer, delim, &last);   // Search for command at start of buffer
      if (command != NULL) {
        boolean matched = false;
        for (int i = 0; i < commandCount; i++) {
          #ifdef SERIALCOMMAND_DEBUG
            debugPrinter->print("Comparing [");
            debugPrinter->print(command);
            debugPrinter->print("] to [");
            debugPrinter->print(commandList[i].command);
            debugPrinter->println("]");
          #endif

          // Compare the found command against the list of known commands for a match
          if (strncmp(command, commandList[i].command, SERIALCOMMAND_MAXCOMMANDLENGTH) == 0) {
            #ifdef SERIALCOMMAND_DEBUG
              debugPrinter->print("Matched Command: ");
              debugPrinter->println(command);
            #endif

            // Execute the stored handler function for the command
            (*commandList[i].function)();
            matched = true;
            break;
          }
        }
        if (!matched && (defaultHandler != NULL)) {
          (*defaultHandler)(command);
        }
      }
      clearBuffer();
    }
    else if (isprint(inChar)) {     // Only printable characters into the buffer
      if (bufPos < SERIALCOMMAND_BUFFER) {
        buffer[bufPos++] = inChar;  // Put character into buffer
        buffer[bufPos] = '\0';      // Null terminate
      } else {
        #ifdef SERIALCOMMAND_DEBUG
          debugPrinter->println("Line buffer is full - increase SERIALCOMMAND_BUFFER");
        #endif
      }
    }
  }
}

/*
 * Clear the input buffer.
 */
void SerialCommand::clearBuffer() {
  buffer[0] = '\0';
  bufPos = 0;
}

/**
 * Retrieve the next token ("word" or "argument") from the command buffer.
 * Returns NULL if no more tokens exist.
 */
char *SerialCommand::next() {
  return strtok_r(NULL, delim, &last);
}
