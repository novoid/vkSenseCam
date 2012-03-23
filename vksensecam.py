#!/usr/bin/env python
# -*- coding: utf-8 -*-
## auto last change for vim and Emacs: (whatever comes last)
## Latest change: Mon Mar 08 11:49:34 CET 2010
## Time-stamp: <2012-03-23 21:51:55 vk>
"""
vksensecam.py
~~~~~~~~~~~~~

FIXXME:
   * add exception handling to all file system operation calls
   * handle misc FIXXMEs in the code :-)

"""

COPYRIGHT = "  :copyright:  (c) 2012 by Karl Voit <tools@Karl-Voit.at>\n\
  :license:    GPL v2 or any later version\n\
  :bugreports: <tools@Karl-Voit.at>\n"


import datetime
import logging, os, re, sys
import shutil ## for file copy
from optparse import OptionParser

## debugging:   for setting a breakpoint:  pdb.set_trace()
#import pdb

now = datetime.datetime.now()

## ======================================================================= ##
##                                                                         ##
##         Configure following lines to meet your requirements             ##
##                                                                         ##
## ======================================================================= ##

## NOTE: This script was developed using an Vicon Revue v1 device which
##       seems to be identical to Microsoft SenseCam. I am unsure to what
##       distinct the newer Vicon Revue devices differ. Send me one over
##       and I'll check :-)                              tools@Karl-Voit.at

## the absolute path to your SENSOR.CSV when SenseCam device is mounted in system:
## (I guess this is different on every system)
CSV_FILE_FOLDER = "/media/A295-005B/DATA"  

## the new name of the original SENSOR.CSV file which is kept as backup:
## (can be arbitrary as long as it differs from existing files)
BACKUP_CSV_FILE_NAME = "SENSOR_original.CSV"

## where should the SenseCam data be downloaded to
## (choose your archive folder name)
DESTINATION_CONTAINING_FOLDER = "/home/vk/archive/events_memories/" + str(now.year)

## which folder name should I use?
## (will be created for each distinct download process)
DESTINATION_FOLDERNAME = now.strftime("%Y-%m-%dT%H.%M_SenseCam_data")

## ======================================================================= ##
##                                                                         ##
##         You should NOT need to modify anything below this line!         ##
##                                                                         ##
## ======================================================================= ##

## manual version number
PROG_VERSION = "0.1"

## file name of SenseCam data - defined by the firmware of device
CSV_FILE_NAME = "SENSOR.CSV"

## temporary name for newly written sensor data file
TEMP_CSV_FILE_NAME = "SENSOR_NEW.CSV"

## combine destination folder:
DESTINATION_FOLDER_WITH_PATH = os.path.join(DESTINATION_CONTAINING_FOLDER, DESTINATION_FOLDERNAME)

## defines index positions in CSV file of various information:
## more details: http://www.clarity-centre.org/claritywiki/images/7/72/SenseCam_User_Guide_v1.4.pdf
TYPEIDX = 0  ## one of: CAM ACC CLR PIR TMP BAT RTC FIL VER SYS
TIMEIDX = 1  ## for CAM: 2012/03/20 19:13:40
FILEIDX = 2  ## for CAM: 00001807.JPG
METAIDX = 3  ## for CAM: one of: P L T M -> see CAM_REASON

## reason, a photo was made:
## more details: http://www.clarity-centre.org/claritywiki/images/7/72/SenseCam_User_Guide_v1.4.pdf
CAM_REASON = { 'P':"IR", 'L':"light", 'T':"timer", 'M':"manual" }
             ## P = PIR activated 
             ## T = timer 
             ## M = manual capture 
             ## L = light-level change


## Vicon Revue Data (on HDD) format:   «2012-03-20 18:58:58»
IMPORTFILEFORMAT = "-"

## format of SENSOR.CSV on the Device: «2012/03/21 10:41:44»
DEVICEFILEFORMAT = "/"

## RegEx matching both formats:
TIME_PATTERN = re.compile('^(\d{4,4})[/-]([01]\d)[/-]([0123]\d)[ ]([012]\d):([012345]\d):([012345]\d)')


USAGE = "\n\
         %prog [options]\n\
\n\
This script does has *two* different modes of operation depending\n\
on the format of the given SENSOR.CSV:\n\
\n\
MODE 1:\n\
This script copies sensor data and photographs from a \"Microsoft\n\
SenseCam\" or \"Vicon Revue v1\" device to your hard disk and:\n\
   * creates a download folder on your hard disk\n\
     like e.g. \"/configuredpath/2012-03-23T21.18_SenseCam_data\"\n\
   * copies SENSOR.CSV and photographs to this download folder\n\
   * add meta-data such as ISO time-stamps to the file names of photos\n\
     like e.g. \"2012-03-21T10.41.48_SenseCam_IR_00001810.JPG\"\n\
   * re-writes the SENSOR.CSV according to the new file names\n\
   * stores original SENSOR.CSV as a backup\n\
   * Note: EXIF meta-data of the photos is kept unchanged in the \n\
           photographs. Usually they are fine (reflect their exposure\n\
           time-stamp and such).\n\
\n\
No data is changed on the device itself! You can use other software\n\
like Vicon Revue Desktop as well afterwards.\n\
\n\
Example invocations on GNU/Linux or Mac OS X:\n\
  vksensecam.py --simulate        ... please use this if unsure!\n\
  vksensecam.py --verbose         ... to get all the noise details\n\
                                      what is going on\n\
  vksensecam.py                   ... this is all you need when \n\
                                      everything is set up\n\
\n\
MODE 2:\n\
If the given SENSOR.CSV is recognized having the format of an already\n\
downloaded file (Vicon Revue Desktop changes date-stamp separator\n\
characters to slashes), the tool assumes an already downloaded\n\
data-set. In this case it does (in the same folder as the SENSOR.CSV):\n\
   * rename photo file names like described above\n\
   * changes entries in SENSOR.CSV according to the new file names\n\
   * saves original SENSOR.CSV as a backup\n\
   * Note: EXIF meta-data is already likely overwritten by Vicon \n\
           Revue Desktop before\n\
\n\
Example invocations on GNU/Linux or Mac OS X:\n\
  vksensecam.py -f /path/SENSOR.CSV --simulate\n\
             ... please use this if unsure!\n\
  vksensecam.py -f /path/SENSOR.CSV\n\
             ... this is all you need when everything is set up\n\
\n\
If unsure, please use the simulate option!\n\
Basic configuration is done in the first section of the script.\n\
\n" + COPYRIGHT

parser = OptionParser(usage=USAGE)

parser.add_option("-f", "--folder", dest="folder", 
                  help="(optional) override default folder for SENSOR.CSV which is \"" + \
                      CSV_FILE_FOLDER + "\"", metavar="PATH")

parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")

parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="do not output anything but just errors on console")

parser.add_option("-s", "--simulate", dest="simulate", action="store_true",
                  help="do not change any file on disk, just report what would happen")

parser.add_option("--version", dest="version", action="store_true",
                  help="display version and exit")
             

(options, args) = parser.parse_args()


class vk_FileNotFoundException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.CRITICAL, format=FORMAT)
    else:
        FORMAT = "%(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)



def copy_file(original, new):
    """copies a file from one location to another or simulates it"""

    if options.simulate:
        logging.info("SIMULATED: copying  " + original + " -->  " + new)
    else:
        shutil.copy2(original, new)


def rename_file(original, new):
    """renames a file from one name to another or simulates it"""

    if options.simulate:
        logging.info("SIMULATED: renaming  " + original + " -->  " + new)
    else:
        os.rename(original, new)


def make_folder(foldername):
    """creates a new folder or simulates it"""

    if options.simulate:
        logging.info("SIMULATED: creating folder  " + foldername)
    else:
        os.mkdir(foldername)



def write_line( filehandle, line ):
    """writes a line to a file or simulates it"""

    if options.simulate:
        ##logging.debug("SIMULATED: writing line: [" + line.strip() + "]")  ## is a bit noisy
        pass
    else:
        filehandle.write( line )


def close_file( filehandle):
    """closes file handle or simulates it"""

    if options.simulate:
        logging.info("SIMULATED: closing filehandle")
    else:
        filehandle.close()


def generate_new_basename(timestampstring, basename, metadata):
    """generates a new filename based on the timestamp and the old basename"""

    year, month, day, hour, minute, second = TIME_PATTERN.match( timestampstring ).groups()

    name, extension = os.path.splitext(basename)

    return year + '-' + month + '-' + day + 'T' + \
        hour + '.' + minute  + '.' + second + '_' + \
        'SenseCam_' + \
        CAM_REASON[metadata] + '_' + \
        name + extension



def handle_photograph_file(basename, timestampstring, metadata, filetype, issues):
    """Handles a single photo file"""

    logging.debug("handle_photo_file: " + basename + " with time " + \
                      timestampstring + " and reason " + CAM_REASON[metadata] )

    returnline = False  ## has to be set in any case!

    old_csv_line = "CAM," + timestampstring + ',' + basename + ',' + metadata + "\n"

    if filetype == DEVICEFILEFORMAT:
        ## in DEVICEFILEFORMAT; "00010297.JPG" is actually "H01/M0102/00010297.JPG"
        sensor_path = os.getcwd()  ## store for later re-switching to

        device_file_path = os.path.join(sensor_path, 'H'+basename[2:4], 'M'+basename[2:6] )
        logging.debug("device_file_path: [%s]" % device_file_path )
        os.chdir( device_file_path )

    if os.path.isfile(basename):
        if TIME_PATTERN.match( timestampstring ):

            new_basename = generate_new_basename(timestampstring, basename, metadata)

            if filetype == DEVICEFILEFORMAT:
                ## DEVICEFILEFORMAT: copy file to destination folder with new name
                ## IMPORTFILEFORMAT: rename file locally
                filedestination = os.path.join(DESTINATION_FOLDER_WITH_PATH, new_basename)
            else:
                filedestination = new_basename

            ## FIXXME: check if filedestination does not already exist

            logging.debug("will rename/move \"" + basename + "\" to \"" + filedestination + "\"")
            if filetype == DEVICEFILEFORMAT:
                copy_file(basename, filedestination)
            else:
                rename_file(basename, filedestination)

            issues['CAMfound'] += 1
    
            ## basically replacing the file name of the original CSV line with the new file name:
            returnline = "CAM," + timestampstring + ',' + new_basename + ',' + metadata + "\n"
    
        else:
            logging.warn("WARNING: time string \"" + timestampstring + \
                              "\" does not match RegEx for time strings! Omitting image \"" + \
                              basename + "\"")
            issues['timestampmismatch'] += 1
            returnline = old_csv_line

    else:  ## basename is not existing as file (any more?)
        logging.warn("WARNING: file \"" + basename + \
                         "\" does not exist (any more). Skipping and omitting in new CSV file.")
        issues['file_not_found'] += 1
        returnline = ""

    if filetype == DEVICEFILEFORMAT:
        os.chdir(sensor_path)

    return returnline, issues


def make_sure_destination_folder_exists():
    """checks if no DESTINATION_CONTAINING_FOLDER exists and creates it"""

    if not os.path.isdir(DESTINATION_CONTAINING_FOLDER):
        logging.error("\nERROR: the configured DESTINATION_CONTAINING_FOLDER [%s] is not an existing path. (re-configure this script or create folder)\n")
        sys.exit(4)

    if os.path.isdir(DESTINATION_FOLDER_WITH_PATH):
        logging.error("\nERROR: the desired destination folder [%s] already exists. (I stop here to prevent overwritten data.)\n" % DESTINATION_FOLDER_WITH_PATH )
        sys.exit(5)
    else:
        logging.debug("creating folder [%s]" % DESTINATION_FOLDER_WITH_PATH )
        make_folder(DESTINATION_FOLDER_WITH_PATH)


def guess_data_format(line):
    """checks the year/month/day separators and derives data format; quits if wrong characters were detected"""

    if line[8] == IMPORTFILEFORMAT and line[11] == IMPORTFILEFORMAT:
        logging.info("Detected already imported format (I assume: data was imported e.g. with Vicon Revue Desktop)")
        filetype = IMPORTFILEFORMAT

    elif line[8] == DEVICEFILEFORMAT and line[11] == DEVICEFILEFORMAT:
        logging.info("Detected device format (I assume: data is still in same format of the device)")
        filetype = DEVICEFILEFORMAT

    else:
        logging.error("\nERROR: I could not detect file format. Probably wrong SENSOR.CSV file format.\n")
        sys.exit(3)

    return filetype



def set_filetype_and_create_new_sensorfile(line):
    """sets filetype variable and creates sensor files accordingly"""

    filetype = guess_data_format(line)

    if filetype == DEVICEFILEFORMAT:
        make_sure_destination_folder_exists()
        newsensorcsvfilename = os.path.join(DESTINATION_FOLDER_WITH_PATH, CSV_FILE_NAME)
    else:
        newsensorcsvfilename = TEMP_CSV_FILE_NAME

    logging.debug("using new SENSOR filename: [%s]" % newsensorcsvfilename )

    tempcsvfile = False

    if options.simulate:
        logging.info("SIMULATED: creating " + newsensorcsvfilename)
    else:
        tempcsvfile = open(newsensorcsvfilename, 'w')

    return filetype, newsensorcsvfilename, tempcsvfile


def ParseSensorFile(csvfilename, issues):

    filetype = False  ## either IMPORTFILEFORMAT or DEVICEFILEFORMAT

    for line in open(csvfilename, 'r'):

        if not filetype:
            filetype, newsensorcsvfilename, tempcsvfile = set_filetype_and_create_new_sensorfile(line)

        elements = line.split(",")
        ## logging.debug("line: " + str(elements) )  ## is a bit noisy

        if elements[TYPEIDX] == 'CAM':
            logging.debug( "CAM found; file:[" + elements[FILEIDX] + "]  time:[" + elements[TIMEIDX] + "]" )
            newcsvline, issues = handle_photograph_file(elements[FILEIDX], elements[TIMEIDX], \
                                                           elements[METAIDX][0], filetype, issues)
        else:
            newcsvline = line

        write_line( tempcsvfile, newcsvline )

    close_file(tempcsvfile)

    if filetype == DEVICEFILEFORMAT:
        fromfile = os.path.join(CSV_FILE_FOLDER, CSV_FILE_NAME)
        tofile = os.path.join(DESTINATION_FOLDER_WITH_PATH, BACKUP_CSV_FILE_NAME)
        logging.debug("storing original \""+ fromfile + "\" to \"" + tofile + "\"")
        copy_file( fromfile, tofile )

    elif filetype == IMPORTFILEFORMAT:
        logging.debug("storing original \""+ CSV_FILE_NAME + "\" to \"" + BACKUP_CSV_FILE_NAME + "\"")
        rename_file( CSV_FILE_NAME, BACKUP_CSV_FILE_NAME )
        logging.debug("renaming newly created \"" + TEMP_CSV_FILE_NAME + "\" to \"" + \
                      CSV_FILE_NAME + "\"")
        rename_file( TEMP_CSV_FILE_NAME, CSV_FILE_NAME )

    return issues


def main():
    """Main function [make pylint happy :)]"""

    issues = { 'file_not_found':0, 'error':0, 'timestampmismatch':0, 'CAMfound':0 }

    print "     " + os.path.basename(sys.argv[0]) + " " + PROG_VERSION
    print COPYRIGHT

    handle_logging()

    if options.version:
        print os.path.basename(sys.argv[0]) + " " + PROG_VERSION
        sys.exit(0)

    ## old ## if ( not options.importformat and not options.deviceformat ) or \
    ## old ##         ( options.importformat and options.deviceformat ) :
    ## old ##     print USAGE
    ## old ##     logging.error("\nERROR: Please use one of \"--deviceformat\" or \"--importformat\"\n")
    ## old ##     sys.exit(1)

    ## filelist = args[0:]
    ## logging.debug("filelist: [%s]" % filelist)

    global DESTINATION_CONTAINING_FOLDER

    original_path = os.getcwd()

    if not options.folder:
        logging.debug("taking default folder [%s]" % CSV_FILE_FOLDER )
        csvfile = os.path.join(CSV_FILE_FOLDER, CSV_FILE_NAME)
    else:
        logging.debug("user has chosen his own folder [%s]" % options.folder )
        csvfile = os.path.join(options.folder, CSV_FILE_NAME)

    if os.path.isfile(csvfile):
        logging.info("found csvfile: " + csvfile )

        path = os.path.dirname(csvfile)
        logging.debug("has directory: " + path)
        basename = os.path.basename(csvfile)
        logging.debug("has basename:  " + basename)

        if path:
            os.chdir(path)
        logging.debug("changed cwd to: " + os.getcwd())
        issues = ParseSensorFile( basename, issues )
        os.chdir(original_path)

    else:
        logging.critical("\nERROR: \"%s\" is no existing file!" % csvfile)

    logging.info("\n")

    if issues['error'] != 0:
        ## FIXXME: actually since I assume, errors always exits, this is redundant and never reached!
        logging.info("Found " + str(issues['error']) + " errors!")

    if issues['file_not_found'] != 0:
        logging.warn("WARNING: Could not find " + str(issues['file_not_found']) + " file(s)! (a few are always missing)")

    if issues['timestampmismatch'] != 0:
        logging.info(str(issues['timestampmismatch']) + " time stamps could not be recognized!")

    logging.info(str(issues['CAMfound']) + " photos successfully processed.")

    logging.info("finished.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################
# vim:foldmethod=indent expandtab ai ft=python tw=120 fileencoding=utf-8 shiftwidth=4
