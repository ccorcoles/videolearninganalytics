import csv
import time
from datetime import datetime
from itertools import groupby

def values_from_csv(file, timeDifference=5, outputFile='output.csv'):
    """
    A function that reads a CSV file, processes the data, and writes the output to another CSV file.
    
    Parameters:
    - file: The input CSV file to be read.
    - timeDifference: The time difference threshold to consider operations as one (default is 5).
    - outputFile: The output CSV file to write the processed data (default is 'output.csv').
    
    Returns:
    This function does not return anything, it writes the processed data to the specified output file.
    """
    # file is the file we read, outputFile is the file we write to
    # when two 'seek' operations are separated by less than timeDifference, we consider that they are one and the same
    with open(file, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        data = list(reader)    

    print('File '+file+' is read.')

    discarded_nonSequentialData = 0
    discarded_weirdPause = 0
    discarded_weirdSeek = 0
    csvOutput = ''

    verbose = False # for debugging purposes

    # we keep only the second, third, fourth, fifth and sixth columns
    data = [[row[1], row[2], row[3], row[4], row[5]] for row in data]

    # discard the first line
    data = data[1:]

    # data:
    # the first column contains a MYSQL datetime (the moment the page was accessed)
    # the second column contains a floating point number (a random number to avoid collisions)
    # (in the future, this may contain and ID of the user, which serves the same purpose: avoiding collisions)
    # the third column contains a second MYSQL datetime (the moment the verb happened)
    # the fourth column contains a string (the verb, mainly play, pause, seek, or stop)
    # the fifth column contains a floating point number (the parameter for the verb)

    # we now sort the list by the second column, and then the first one
    data.sort(key=lambda row: (row[1], row[0]))

    # we convert the fifth row from a string to a float for all the rows in data
    # for row in data:    
    #    row[4] = float(row[4].replace(',','.'))

    # we store the maximum of the fifth column in a variable
    videoLength = max(row[4] for row in data) # it's not really the video length until the video has been watched enough times, obviously

    # we loop on the list and we convert the first and third columns to datetime
    for row in data:
        row[0] = datetime.strptime(row[0], '%a, %d %b %Y %H:%M:%S %Z')
        row[2] = datetime.strptime(row[2], '%a, %d %b %Y %H:%M:%S %Z')
    # for each row, we calculate the difference in seconds between the third and first columns and store it in the third column
    # so that we have a relative time (from the moment the page was loaded)
        row[2] = (row[2] - row[0]).total_seconds()
    
    # we separate the list in a list of lists, differentiated by the first and second columns
    jumps = [list(g) for _, g in groupby(data, lambda row: (row[0], row[1]))]

    print('We have '+str(len(jumps))+' sequences in the original file.')

    # some basic error detection
    # for each sublist in jumps, we check that the values in the third column are in ascending order. 
    # if they are not, we drop the sublist
    for sublist in jumps:
        for i in range(1, len(sublist)):
            if sublist[i][2] < sublist[i-1][2]:
                jumps.remove(sublist)
                discarded_nonSequentialData += 1
                break
    if discarded_nonSequentialData > 0: print('We have discarded '+str(discarded_nonSequentialData)+' sequences because of out of sequence data.')

    # for each row in each sublist, we substract the first value of the third column from the value of the third column
    # so that it starts at zero
    for sublist in jumps:
        tmp = sublist[0][2]
        for row in sublist:
            row[2] = row[2] - tmp
    
    # now we should merge consecutive jumps (those less than timeDifference seconds apart)
    if verbose: print('Merging consecutive seeks...')
    for sublist in jumps:
        i = 0
        while i < len(sublist)-1:
            # first, we check wether we have a seek in our line. if it is the case, we must check whether the next action
            # is also a seek and whether it is less than timeDifference seconds apart. 
            # if it is, we merge the two lines. we keep the origin from the first row,
            # the end from the second one, we store that on the second row (so we don't break the loop) and drop the first one

            # This thing works, but doesn't fix timestamps for non-consecutive seeks 
            if sublist[i][3] == 'seek' and sublist[i+1][3] == 'seek' and sublist[i+1][2]-sublist[i][2] < timeDifference:
                difference = sublist[i+1][2]-sublist[i][2]
                sublist[i+1][2] = sublist[i][2]
                sublist[i] = sublist[i+1]
                sublist.remove(sublist[i+1])
                # now, we subtract the time difference between skips from all future events
                for j in range(i+1, len(sublist)):
                   sublist[j][2] = sublist[j][2] - difference
            else:
                i += 1 # we only jump to the next line if we have finished checking the one we are in

    # some more error detection can be done:
    #  in pauses, big discrepances between [2] and [4] should not happen. and [2] should not be lower than [4] (+- a second), in any case
    #  and we should never have the playhead beyond the end of the video 
    #  as Codeium says: "technological limitations make it impossible to capture all possible variations of this event"
    #  but we should discard such events, in any case (we suspect they are all due to slow connections)
    for sublist in jumps:
        # a pause on the last line is actually a stop
        if sublist[-1][3] == 'pause':
            sublist[-1][3] = 'stop'    
        if verbose:
            print('---')
            print('We are in sublist number '+str(jumps.index(sublist)))
            for row in sublist:
                print(row[2],row[3],row[4])

        # first, we'll check if we are at a pause
        for row in sublist:
            if verbose: print(row[3])
            if row[3] == 'pause':
                if row[2]+1 < row[4]: #this shouldn't happen. if it does, let's remove the sublist
                    jumps.remove(sublist)
                    if verbose: print('We have removed the sublist because of a pause we didn\'t like. Row 2 was '+str(row[2])+' and row 4 was '+str(row[4]))
                    discarded_weirdPause += 1
                    break
                else: # if everything looks OK, we should write the pause to the csv file (if it's at least one second long)
                      # TODO should the minimum length of the pause be a parameter?
                      # we don't wait thil the end of the list to store it. if something goes wrong later, this is still OK
                    if row[4]>1: 
                        csvOutput += str('PAUSE,') + str(round(row[4])) + ',' + str(round(sublist[sublist.index(row)+1][2]-row[2])) + '\n'
                    if verbose: print('We\'ve written a pause at '+str(row[4])+' with duration '+str(sublist[sublist.index(row)+1][2]-row[2]))
                # and in any case, we must adjust the following timestamps
                difference = sublist[sublist.index(row)+1][2]-row[4]
                for j in range(sublist.index(row)+1, len(sublist)):
                    sublist[j][2] = sublist[j][2] - difference
            else:
                # if it's not a pause, but it's a seek, we should write the jump to the csv file
                if row[3] == 'seek':
                    # some more error detection:
                    #  if row 2 is bigger than 1.1 times the our detected videoLenghth, we should abort...
                    # TODO Should that 1.1 be a parameter?
                    if row[2] > 1.1*videoLength:
                        jumps.remove(sublist)
                        if verbose: print('We have removed the sublist because of a seek we didn\'t like. Row 2 was '+str(row[2])+' and videoLength was '+str(videoLength))
                        discarded_weirdSeek += 1
                        break
                    if abs(row[4]-row[2])>1: # again, we'll only consider jumps longer than a second
                                             # and, again, maybe that length should be a parameter TODO
                        csvOutput += str('JUMP,') + str(round(row[2])) + ',' + str(round(row[4])) + '\n'
                        if verbose: print('We\'ve written a jump from '+str(row[2])+' to '+str(row[4]))
                        plus = row[4]
                        minus = row[2]
                        if sublist.index(row)+1 < len(sublist): # and, if we are not at the last line, we should fix the timestamps
                            if verbose: print('Fixing the timestamps...')
                            for j in range(sublist.index(row)+1, len(sublist)):
                                if verbose: print(sublist[j][2], plus, minus)
                                sublist[j][2] = sublist[j][2] + plus - minus
        if verbose: 
            print('...and the processed list is...')
            for row in sublist:
                print(row[2],row[3],row[4])
    if discarded_weirdPause > 0 : print('We have dropped ' + str(discarded_weirdPause) + ' sequences because of pauses that were not as expected.')
    if discarded_weirdPause > 0 : print('We have dropped ' + str(discarded_weirdSeek) + ' sequences because of seeks that were not as expected.')

    # and now, the stops...
    for sublist in jumps:
        if sublist[-1][3] == 'stop': csvOutput += str('STOP,' + str(round(sublist[-1][4]))) + '\n'

    # we write the contents of the csv to the flie specified in outputFile
    with open(outputFile, 'w') as f:
        f.write(csvOutput)

'''    
values_from_csv('telec1ca_raw.csv',5,'telec1ca_processed.csv')
values_from_csv('telec1es_raw.csv',5,'telec1es_processed.csv')
values_from_csv('telec2ca_raw.csv',5,'telec2ca_processed.csv')
values_from_csv('telec2es_raw.csv',5,'telec2es_processed.csv')
values_from_csv('telec3ca_raw.csv',5,'telec3ca_processed.csv')
values_from_csv('telec3es_raw.csv',5,'telec3es_processed.csv')
values_from_csv('telec4ca_raw.csv',5,'telec4ca_processed.csv')
values_from_csv('telec4es_raw.csv',5,'telec4es_processed.csv')
'''

values_from_csv('distracid_raw.csv',5,'distracid_processed.csv')
values_from_csv('distrarq_raw.csv',5,'distrarq_processed.csv')
values_from_csv('distrCAPBASE_raw.csv',5,'distrCAPBASE_processed.csv')
values_from_csv('distrdiseno_raw.csv',5,'distrdiseno_processed.csv')
values_from_csc('distrintro_raw.csv',5,'distrintro_processed.csv')
values_from_csv('InstNeo4j_raw.csv',5,'InstNeo4j_processed.csv')
values_from_csv('intronosqles_raw.csv',5,'intronosqles_processed.csv')
values_from_csv('magregatip_raw.csv',5,'magregatip_processed.csv')
values_from_csv('mapreduce_raw.csv',5,'mapreduce_processed.csv')
values_from_csv('mgrafo_raw.csv',5,'mgrafos_processed.csv')
values_from_csv('mongoACT_raw.csv',5,'mongoACT_processed.csv')
values_from_csv('mongoCONS_raw.csv',5,'mongoCONS_processed.csv')
values_from_csv('mongoCREA_raw.csv',5,'mongoCREA_processed.csv')
values_from_csv('mongodb_raw.csv',5,'mongodb_processed.csv')
values_from_csv('neo4j_raw.csv',5,'neo4j_processed.csv')
values_from_csv('nosqlintro_raw.csv',5,'nosqlintro_processed.csv')
values_from_csv('nosqlmagregacar_raw.csv',5,'nosqlmagregacar_processed.csv')
values_from_csv('nosqlmagregamot_raw.csv',5,'nosqlmagregamot_processed.csv')
values_from_csv('nosqlpersistencia_raw.csv',5,'nosqlpersistencia_processed.csv')
values_from_csv('restNeo4j_raw.csv',5,'restNeo4j_processed.csv')
values_from_csv('riak_raw.csv',5,'riak_processed.csv')