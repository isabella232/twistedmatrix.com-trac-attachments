"""CDDB protocol implementation.

Future Plans:
 - add server protocol
 - add not readonly client commands
"""

from twisted.internet import reactor, protocol
from twisted.protocols import basic

TERMINATING_MARKER = "."
MAX_PROTO = "6"

# response codes
OK                        = 200
EXACT_MATCH               = OK
CURRENT_PROTO_LEVEL       = OK
OK_READ_ONLY              = 201
OK_PROTO_LEVEL_CHANGED    = 201
NO_MATCH_FOUND            = 202
OK_FURTHER_DATA_FOLLOWS   = 210
MULTIPLE_INEXACT_MATCHES  = 211
OK_VERSION_INFO_FOLLOWS   = 211
QUIT_OK_CLOSING           = 230
NOT_AVAILABLE             = 401
UNLINK_PERMISSION_DENIED  = 401
FILE_ACCESS_FAILED        = 402
SERVER_ERROR              = 402
HANDSHAKE_ALREADY_DONE    = 402
DB_ENTRY_CORRUPTED        = 403
CGI_ENV_ERROR             = 408
HANDSHAKE_NOT_DONE        = 409
HANDSHAKE_FAILED          = 431
CONNECT_PERMISSION_DENIED = 432
USER_LIMIT_EXCEED         = 433
SYSTEM_LOAD_TOO_HIGH      = 434
SYNTAX_ERROR              = 500
UNKOWN_COMMAND            = SYNTAX_ERROR
UNIMPLEMENTED_COMMAND     = SYNTAX_ERROR
INVALID_DATA              = 501
SAME_PROTO_LEVEL          = 502
QUIT_ERROR_CLOSING        = 530
SERVER_TIMEOUT            = 530

# proper codes for each supported command
login_codes = [OK, OK_READ_ONLY, CONNECT_PERMISSION_DENIED, USER_LIMIT_EXCEED,
                SYSTEM_LOAD_TOO_HIGH]
hello_codes = [OK, HANDSHAKE_FAILED, HANDSHAKE_ALREADY_DONE]
lscat_codes = [OK_FURTHER_DATA_FOLLOWS]
query_codes = [EXACT_MATCH, MULTIPLE_INEXACT_MATCHES, NO_MATCH_FOUND,
               DB_ENTRY_CORRUPTED, HANDSHAKE_NOT_DONE]
read_codes = [OK_FURTHER_DATA_FOLLOWS, NOT_AVAILABLE, SERVER_ERROR,
              DB_ENTRY_CORRUPTED, HANDSHAKE_NOT_DONE]
discid_codes = [OK, SYNTAX_ERROR]
help_codes = [OK_FURTHER_DATA_FOLLOWS, NOT_AVAILABLE]
motd_codes = [OK_FURTHER_DATA_FOLLOWS, NOT_AVAILABLE]
proto_codes = [CURRENT_PROTO_LEVEL, OK_PROTO_LEVEL_CHANGED,
               INVALID_DATA, SAME_PROTO_LEVEL]
quit_codes = [QUIT_OK_CLOSING, QUIT_ERROR_CLOSING]
sites_codes = [OK_FURTHER_DATA_FOLLOWS, NOT_AVAILABLE]
stat_codes = [OK_FURTHER_DATA_FOLLOWS]
ver_codes = [OK, OK_FURTHER_DATA_FOLLOWS]
misc_codes = [SERVER_ERROR, CGI_ENV_ERROR, SYNTAX_ERROR,
              UNKOWN_COMMAND, UNIMPLEMENTED_COMMAND, SERVER_TIMEOUT]
unlink_codes = [OK, UNLINK_PERMISSION_DENIED, FILE_ACCESS_FAILED, INVALID_DATA]

# helper codes list
successful_codes = [200, 201, 230]
multi_line_codes = [210, 211]
failure_error_codes = [431, 432, 433, 434]

# dictionary to map codes
RESPONSE_CODES = {
    "login": login_codes,
    "hello": hello_codes,
    "lscat": lscat_codes,
    "query": query_codes,
    "read": read_codes,
    "discid": discid_codes,
    "help": help_codes,
    "motd": motd_codes,
    "proto": proto_codes,
    "quit": quit_codes,
    "sites": sites_codes,
    "stat": stat_codes,
    "ver": ver_codes,
    "unlink": unlink_codes,
    "general_errors": misc_codes
    }

class CDDBPClient(basic.LineReceiver):
    """ CDDB Protocol client implementation.
    
    @cvar buffer: Holds multi line reponse data.
    @cvar command: The current executing command.
    @cvar multi_line: Set it to true in L{self.handleStatus} when you expect
    further incoming data.
    """
    buffer = []
    command = ""
    multi_line = False
    
    def connectionMade(self):
        self.buffer = []
        self.command = "login"
        self.multi_line = False
    
    def lineReceived(self, line):
        """ Called when a line is received from the server.
        
        This method checks if the current running command expects a multi
        line response or not and calls the right method to handle the incoming
        data.
        """
        if not self.multi_line:
            code = int(line.split(" ", 1)[0])
            self.handleStatus(code, line)
        else:
            if line == TERMINATING_MARKER:
                self.parseResponse(self.buffer[:])
                self.buffer = []
                self.multi_line = False
            else:
                self.buffer.append(line)

    def sendCommand(self, command, args=[]):
        """ Create string commands to send to the server. """
        str = "%s %s" % (command, " ".join(args))
        self.sendLine(str)

    def hello(self, username, hostname, app_name, app_version):
        """ Send 'hello' command to initiate the session (handshake).
        
        sample command:
            - C{cddb hello foo localhost app 1.0}
        """
        self.command = "hello"
        self.sendCommand("cddb", [self.command, username, hostname,
                                  app_name, app_version])
    
    def lscat(self):
        """ Send 'lscat' command to get the list of available categories.
        
        sample command:
            - C{cddb lscat}
        """
        self.command = "lscat"
        self.sendCommand("cddb", [self.command])
    
    def query(self, full_discid):
        """ Send 'query' command to query freedb for matching entries.
            
        full_discid has to be in the form explained in the
        U{CDDB-protocol documentation<http://
        freedb.org/modules.php?name=Sections&sop=viewarticle&artid=28>}        
        
        sample command:
            - C{cddb query f2123610 16 150 29977 46577 68970 85297 104922 131622
            150317 157300 181212 208612 231910 253045 273352 295987 326627 4664}
            
        @type full_discid: string
        @param full_discid: The discid (in hexadecimal lower case
        representation), followed by the number of tracks, the frame offset for
        each track and finally the length of the cd in seconds, for example:
            
        C{f2123610 16 150 29977 46577 68970 85297 104922 131622 150317 157300
        181212 208612 231910 253045 273352 295987 326627 4664}
        """
        self.command = "query"
        self.sendCommand("cddb", [self.command, full_discid])

    def read(self, category, discid):
        """ Send 'read' command to read entries from a freedb server.
        L{query} must B{always} be called before this method.
        
        sample command:
            - C{cddb read misc f2123610}
            
        @type category: string
        @param category: Category has to be one of the available categories,
        call L{self.lscat} to know them.
        """
        self.command = "read"
        self.sendCommand("cddb", [self.command, category, discid])

    def discid(self, cd_data):
        """ Send 'discid' command to let the server compute discid from cd data.
        
        sample command:
            - C{discid 16 150 29977 46577 68970 85297 104922 131622 150317
            157300 181212 208612 231910 253045 273352 295987 326627 4664}
        
        @type cd_data: string
        @param cd_data: The number of tracks followed by the frame offset
        of each cd track and the length of the cd in seconds, for example:
            
        C{16 150 29977 46577 68970 85297 104922 131622 150317 157300
        181212 208612 231910 253045 273352 295987 326627 4664}
        """
        self.command = "discid"
        self.sendCommand(self.command, [cd_data])

    def proto(self, level=""):
        """ Send 'proto' command to get/set the server's current cddbp
        protocol level.
        
        The protocol level is a number between 1 and L{MAX_PROTO}. The protocol
        level number is optional (if you let it blank you get the current
        level).
        
        sample commands:
            - C{proto}
            
            or
            - C{proto 6}
        @type level: int
        @param level: The protocol level to set.
        """
        self.command = "proto"
        self.sendCommand(self.command, [level])
        
    def help(self, help_cmd="", help_subcmd=""):
        """ Send 'help' command to get help about supported commands.
        
        Sending only I{help} returns a brief explanation of available commands.
        You can gain more help adding a specific command to help_cmd argument
        and help_subcmd argument.
        
        sample commands:
            - C{help}
            
            or 
            - C{help quit}
            
            or
            - C{help cddb hello}
            
        @type help_cmd: string
        @param help_cmd: Represents the command to get help for
        @type help_subcmd: string
        @param help_subcmd: Represents the sub command to get help for
        """
        self.command = "help"
        self.sendCommand(self.command, [help_cmd, help_subcmd])
    
    def motd(self):
        """ Send 'motd' command to get the message of the day.
        
        sample command:
            - C{motd}
        """
        self.command = "motd"
        self.sendCommand(self.command)

    def quit(self):
        """ Send 'quit' command to close the connection.
        
        sample command:
            - C{quit}
        """
        self.command = "quit"
        self.sendCommand(self.command)

    def sites(self):
        """ Send 'sites' command to get the whole list of known freedb mirrors.
        
        sample command:
            - C{sites}
        """
        self.command = "sites"
        self.sendCommand(self.command)

    def stat(self):
        """ Send 'stat' command to get the server's status.
        
        sample command:
            - C{stat}
        """
        self.command = "stat"
        self.sendCommand(self.command)
    
    def ver(self):
        """ Send 'ver' command to get the server's version.
        
        sample command:
            - C{ver}
        """
        self.command = "ver"
        self.sendCommand(self.command)
    
    def unlink(self, category, discid):
        """ Send 'unlink' command to delete an entry from database.
        
        Only administrative users could succeed issuing this command.
        
        sample command:
            - C{cddb unlink misc f2123610}
            
        @type category: string
        @param category: Category has to be one of the available categories,
        call L{self.lscat} to know them.
        """
        self.command = "unlink"
        self.sendCommand("cddb", [self.command, category, discid])
    
    def handleStatus(self, code, line):
        """ Handle status response strings.
        
        Called from L{self.lineReceived} when it encounters the first line of a
        a response received from the server.
        
        Use I{code} parameter and L{self.command} variable to check if the current
        command response will have subsequents response lines setting
        L{self.multi_line} to True. Due to oddities in the protocol you have
        to remember to set it manually.
        
        @type code: int
        @param code: The response code
        @type line: string
        @param line: The first line of incoming data.
        """
        raise NotImplementedError
    
    def parseResponse(self, response):
        """ Parse multi line response data.
        
        Called from L{self.lineReceived} when multi line response data has
        ended, so you could extract needed information from the data.
        
        @type response: list
        @param response: Holds the full response data, each item of the list
        corresponds to a new line in the response.
        """
        raise NotImplementedError
  
class CDDBPClientFactory(protocol.ClientFactory):
    protocol = CDDBPClient

    def clientLostConnection(self, connector, reason):
        print reason

    clientConnectionFailed = clientLostConnection