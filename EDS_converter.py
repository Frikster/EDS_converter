#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Converts EDS files to csv. Best approximation

author: Cornelis Dirk Haupt
website: https://www.linkedin.com/in/dirk-haupt-a1296316
last edited: July 2016
"""

import sys, os
import atexit
from PyQt4 import QtGui
from PyQt4.QtGui import *
import csv
import textwrap
import numpy as np

absDirPath = os.path.dirname(__file__)

def hasNumbers(inputString):
    if inputString == []:
        return True
    else:
        return any(char.isdigit() for char in inputString)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        self.setWindowIcon(QtGui.QIcon(os.path.join(absDirPath, "icons", "ICORDlogo.png")))
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Convert EDS File')
        openFile.triggered.connect(self.eds_conversion)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('EDS Converter')
        self.show()

    def is_center_pt_number(self, elem):
        if '-' in elem:
            elem_split = elem.split('-')
            if len(elem_split[0]) != 6:
                return False
            try:
                center = int(elem_split[0])
            except ValueError:
                return False
            try:
                pt_number = int(elem_split[1])
            except ValueError:
                if len(elem_split[1]) > 0:
                    return True
        return False

    def find_boundaries(self, my_data):
        #assume my_data has been stripped
        date_replacements = ['CON', 'U', 'CONT', 'UNK', 'NAV', 'C', 'CONT.', 'CONTINUE', 'CONTINUED', 'CONTINUES',
                             'N/A']
        not_date_identification = ['ABCDE', 'ABCD', 'BCDE']

        date_counts = []
        dosage_reason_boundaries = [] # all boundaries in the form [(index, boundary),()...]
        end_dates = [] #all end_dates in the form [(index,end_date),()...]
        candidate_end_date_for_set = ''
        ind_plusone_flag = False
        for ind in range(len(my_data)):
            if ind_plusone_flag:
                ind_plusone_flag = False
                continue

            # First find a candidate end_date since you'll hit it first
            elem = my_data[ind]
            elem_6_split = [elem[i:i + 6] for i in range(0, len(elem), 6)]
            elem_6_split_isdigit = [i.isdigit() for i in elem_6_split] # True False for each one
            elem_6_split_digits = [i for i in elem_6_split if i.isdigit()]
            n_spaces = elem.count(' ')

            ##########################################################################
            #### Weak case, if the following is minimally true we have an end_date ###
            if len(elem) >= 6 and\
                True in elem_6_split_isdigit and\
                max(map(len, elem_6_split_digits)) >= 6 and\
                not self.is_center_pt_number(elem) and\
                '-' not in elem and \
                candidate_end_date_for_set == '' and \
                n_spaces < 2 and \
                all([i not in elem for i in not_date_identification]):
                # The obvious hard-ass case:
                if elem.isdigit() and all(i == 6 for i in map(len, elem_6_split)):
                    candidate_end_date_for_set = elem
                else:
                    # Splitting of end_date needed
                    # when here we know one of elem_6_split is not a digit
                    candidate = ''
                    if elem_6_split_isdigit[-1]:
                        the_wrong_start = ''
                        for i in range(len(elem_6_split)):
                            if elem_6_split[i].isdigit():
                                candidate = candidate + elem_6_split[i]
                            else:
                                the_wrong_start = the_wrong_start + elem_6_split[i]
                        # correct my_data's end_date
                        my_data = my_data[:ind - 1] + [the_wrong_start, candidate] + my_data[ind:]
                        # note candidate is **NOT** still at ind: WILL NEED TO SKIP NEXT LOOP ITERATION
                        candidate_end_date_for_set = candidate
                        ind_plusone_flag = True
                    else:
                        unsolvable_problem = False
                        if elem_6_split_isdigit[0]:
                            # Could have a date_replacement attatched to it... sighs
                            for i in range(len(elem_6_split)):
                                if elem_6_split[i].isdigit():
                                    candidate = candidate + elem_6_split[i]
                                else:
                                    # correct my_data's end_date
                                    the_rest = elem_6_split[i:][0]
                                    if the_rest in date_replacements:
                                        my_data = my_data[:ind-1] + [candidate, the_rest] + my_data[ind:]
                                    else:
                                        print(my_data[ind - 5:ind + 5])
                                        unsolvable_problem =  True
                                    break
                                    # note candidate is still at ind, so okay to split in a loop
                            if not unsolvable_problem:
                                candidate_end_date_for_set = candidate
                            else:
                                candidate_end_date_for_set = "UNSOLVABLE PROBLEM IDENTIFYING DATES FOR THIS SECTION"
                        else:
                            # This would mean this element has both values tacked on the front and back
                            # and should be looked into seperately...
                            print(my_data[ind - 5:ind + 5])
                            assert(False)
                if ind_plusone_flag:
                    end_dates = end_dates + [(ind+1, candidate_end_date_for_set)]
                    print(str(ind)+'/'+str(len(my_data)))
                else:
                    end_dates = end_dates + [(ind, candidate_end_date_for_set)]
                    print(str(ind) + '/' + str(len(my_data)))

                ##########################################
                ### Count number of dates for this set ###
                if ind_plusone_flag:
                    date_count_ind = ind + 1
                else:
                    date_count_ind = ind
                count = 0
                while True:
                    elem_6_split = [my_data[date_count_ind][i:i + 6] for i in range(0, len(my_data[date_count_ind]), 6)]
                    elem_6_split_dates = [i for i in elem_6_split if i.isdigit() and len(i) >= 6]
                    if (len(elem_6_split_dates) > 0 and len(my_data[date_count_ind]) >= 6) or\
                                    my_data[date_count_ind] in date_replacements:
                        count = count + 1
                        date_count_ind = date_count_ind + 1
                    else:
                        break
                date_counts = date_counts + [(ind, count, my_data[date_count_ind-count:date_count_ind])]
                date_count_ind, date_count = date_counts[-1][0], date_counts[-1][1]

            ##############################
            ### Check for the boundary ###
            if candidate_end_date_for_set != '':
                n_spaces = elem.count(' ')
                not_boundary_identifiers = ['1 1/2 CONS', '2 GMS-6', '5 DOSES (8)']
                boundary_list = elem.split()
                boundary_digits_list = [s for s in boundary_list if s.isdigit()]
                boundary_strings_list = [s for s in boundary_list if not s.isdigit()]
                boundary_has_digit_list = [s for s in boundary_list if hasNumbers(s)]
                boundary_has_digit_strings_list = [s for s in boundary_has_digit_list if not s.isdigit()]

                remove_spaces_elem = elem.replace(' ', '')
                digits_before_not_digit = 0
                for char in remove_spaces_elem:
                    if char.isdigit():
                        digits_before_not_digit = digits_before_not_digit + 1
                    else:
                        break

                # CRITERIA are DEBATEABLE!!!
                number_parts_with_digits_threshold = len(boundary_has_digit_strings_list) > 0 \
                                                     and hasNumbers(boundary_has_digit_strings_list[0])
                alone_numbers_1to8 = all(0 < int(i) < 9 for i in boundary_digits_list) \
                                     and len(boundary_digits_list) > 0
                only_numbers_and6_and1to8 = (len(remove_spaces_elem) < 6 and remove_spaces_elem.isdigit()) \
                                            and alone_numbers_1to8  # gets obvious case
                alone_strings_len = all((len(i) > 3 or hasNumbers(i)) for i in boundary_strings_list)  # must contain a number else be a word
                first_first_char_is_digit = boundary_list[0][0].isdigit()
                space_threshold_met = (n_spaces >= 1)
                no_not_boundaries = all([i not in elem for i in not_boundary_identifiers])
                one_digit_special_condition = True
                second_first_char_is_digit = True
                if len(boundary_list) > 1:
                    second_first_char_is_digit = boundary_list[1][0].isdigit()


                # fails (seperated by ;): 6 MCG/K8/MIN ; 1 1/2 CONS ; 0.25% 1 SPRAY ; 2 MG-4MG ; N-100 2 ; 1:1 DRIP 5 MG/HR ; PRN: 8 DOSES (2 MGS) ; LR09664 1 UNIT ; 1 (5ML) ; 7 (0.15) DOSES 2 (0.3) DOSES ; 1 UNIT, LG46490 ; 3 (25) DOSES ; 5 DOSES (8)
                # more: Q4H 1 ; Q2-4H 7 ; Q2H 3 ; Q4H 3 ; Q6H 5 ; 3 GM/1 LITER ; Q4H 1 DOSE ; Q4-6' 7 ; #3 2 TABS ; 1 ML/HR .2 MEQ/ML
                # if '50 MG/250 D5W' in elem: #second has
                #     print('h')
                # try:
                #     if len(boundary_has_digit_list) == 1 or (first_first_char_is_digit and
                #                                                  not second_first_char_is_digit):
                #         one_digit_special_condition = (date_count <= 2) and len(boundary_has_digit_list[0]) == 1
                # except:
                #     print('dfg')

                if digits_before_not_digit == 1:
                    one_digit_special_condition = (date_count <= 2)

                    # len(boundary_has_digit_list) == 1 or (first_first_char_is_digit and
                    #                                          not second_first_char_is_digit):
                    # one_digit_special_condition = (date_count <= 2) and len(boundary_has_digit_list[0]) == 1
                    # Additionally check if there is only one "standalone" string... this is not a boundary if there is
                    # if one_digit_special_condition:
                    #     one_digit_special_condition = len(boundary_strings_list) != 1

                # if all(i > 1 for i in map(len, boundary_strings_list)) and \
                #         (any(hasNumbers(i) for i in boundary_strings_list) or boundary_strings_list == []) and \
                #                 (ind - date_count_ind) >= ((date_count * 2) - 1) and \
                #         ((all(i == 1 for i in map(len, boundary_digits_list)) and
                #                   boundary_digits_list != [] and
                #                   n_spaces >= 1) or (len(remove_spaces_elem) < 6 and
                #                                          remove_spaces_elem.isdigit())) and \
                #         all([i not in elem for i in not_boundary_identifiers]):

                # Other cases not identified (removed directly from file since they are few)
                # (ind - date_count_ind) >= ((date_count * 2)-1) and \
                #  There are cases where you might have 3 dates and only 1 dose and 0 dosage...
                # (len(boundary_list) - len(boundary_digits_list) < 2 and
                # There are numerous cases like '3 2 3 7 2 7 1 2 1 1ANTIBIOTIC PROPHYLAXIS' or even more words stuck
                # on

                # Check if boundary is a reasonable distance away from associated end_date
                # CRITERIA DEBATEABLE: MADE IT DOUBLE (3 items to boundary * 2) WHAT IT SHOULD BE
                # (don't forget dates aren't properly split yet)

                # todo:
                # only the digits 1,2,3,4,5,6,7,8 can be on the boundary <- happens a lot where dosage numbers are picked up
                # 1. More than one space between numbers in boundary. Incorrect split messing up whole set <<<< HAPPENS THE MOST AND A LOT
                # 2. Attatched Letters at end
                # 3. 4 number dates
                # 4. multi-digit standalone numbers things being identified as boundaries
                # 5. single standalone digit numbers being misidentified as boundaries
                # 6. Cases like "1/2 TAB BID L TAB AM" actually make it through and are identified as boundaries...
                # another e.g. 1 DOSE MD 7/21/93, TOTAL 3 DOSES HR >40 BP >110
                # 7. 01194: end_date should be 'U'
                # 8. Sometimes there is a combo problem 1 3 3 1U  1 1 <- two spaces + letter in middle

                if  (only_numbers_and6_and1to8 and one_digit_special_condition) or \
                        (alone_numbers_1to8 and alone_strings_len and
                             space_threshold_met and no_not_boundaries and
                             number_parts_with_digits_threshold and first_first_char_is_digit and
                             one_digit_special_condition):

                    if ind - date_count_ind > date_count * 6:
                        dosage_reason_boundaries = dosage_reason_boundaries + [(ind, my_data[ind]
                        + " SKIPPING WHOLE SECTION")]

                        # Patterns identified:
                        # 1. Right after end_date often the next date only has 5 characters
                        # 2. Sometimes UNK is a date... other times not...?
                        # 3. Sometimes - '3 7 4 3 3 3 7 7 3 3INCREASED H + H' -
                        # boundary has more than one solid attatched. Not accounted for.
                        # 4. cant discersn whether UNK is for missing date or missing dose
                        #
                        print(date_counts[-1])
                        print(my_data[date_counts[-1][0]:ind+1])
                        candidate_end_date_for_set = ''
                    else:
                        dosage_reason_boundaries = dosage_reason_boundaries + [(ind, my_data[ind])]
                        assert (len(end_dates) == len(dosage_reason_boundaries))
                        candidate_end_date_for_set = ''

        print(len(date_counts))
        print(len(dosage_reason_boundaries))
        assert(len(date_counts) == len(dosage_reason_boundaries))
        return [date_counts, dosage_reason_boundaries, my_data]


    def get_patient_ids(self, my_data):
        #todo: delete this once you're sure it really is unneeded

        # Split all the end_dates correctly
        # date_replacements = ['CON', 'U', 'CONT', 'UNK', 'NAV', 'C', 'CONT.',
        #                      'CONTINUE', 'CONTINUED', 'CONTINUES','N/A']
        # ind = 0
        # dates_counts = []
        # end_date_inds = []
        # end_date_found = False
        # dates_count = 0
        # # dates_counts counts up the number of dates (end and start dates together) and starting at each end_date_ind
        # for ind in range(len(my_data)):
        #     elem = my_data[ind]
        #     elem = elem.replace(' ', '')
        #     try:
        #         int(elem)
        #     except:
        #         if elem not in date_replacements:
        #             end_date_found = False
        #             if dates_count > 0:
        #                 dates_counts = dates_counts + [dates_count]
        #                 assert (len(dates_counts) == len(end_date_inds))
        #                 dates_count = 0
        #             continue
        #     # Logically if you are here elem is an integer or in date_replacements
        #     if not end_date_found and len(elem) >= 6:
        #         end_date_inds = end_date_inds + [ind]
        #         try:
        #             int(elem)
        #         except:
        #             assert(False)
        #         end_date_found = True
        #         dates_count = 1
        #     else:
        #         if end_date_found and (len(elem) >= 6 or elem in date_replacements):
        #             dates_count = dates_count + 1

        # problem_inds = []
        # # Concatenate end_dates properly
        # for ind in range(len(end_date_inds)):
        #     date_elem = my_data[end_date_inds[ind]]
        #     date_elem = date_elem.replace(' ', '')
        #     date_count = dates_counts[ind]
        #     if date_count > 1:
        #         if (len(date_elem) / (date_count - 1)) < 6:
        #             possible_date_concat = True
        #             date_ind = end_date_inds[ind] + 1
        #             add_on = ''
        #             modifier = 2
        #             while possible_date_concat:
        #                 add_on = add_on + my_data[date_ind]
        #                 if (date_count - modifier) <= 0:
        #                     print(
        #                     "Unsolvable problem at end_date " + date_elem + " at index " + str(end_date_inds[ind]) +
        #                     " skipping...")
        #                     problem_inds = problem_inds + [end_date_inds[ind]]
        #                     break
        #                 assert ((date_count - modifier) > 0)
        #                 if ((len(date_elem) + len(add_on)) / (date_count - modifier) == 6):
        #                     possible_date_concat = False
        #                     my_data[end_date_inds[ind]] = date_elem + add_on
        #                     for i in range(end_date_inds[ind] + 1, date_ind + 1):
        #                         my_data[i] = ''
        #                 date_ind = date_ind + 1
        #                 modifier = modifier + 1
        #                 if (ind + 1) < len(end_date_inds):
        #                     assert (
        #                     date_ind < end_date_inds[ind + 1])  # Otherwise you're overlapping with another date!
        #
        # my_data = [val for val in my_data if val != '']

        # Recompute date count but for start_dates
        # Recompute indices for end dates since you changed the array one line up
        # Find where the dates end in each case
        # also find pt_number_center_inds
        end_date_inds = []
        end_of_dates_inds = []
        start_dates_counts = []
        end_date_found = False
        start_dates_count = 0
        pt_number_center_inds = []
        for ind in range(len(my_data)):
            elem = my_data[ind]
            elem = elem.replace(' ', '')
            # add pt_number_center
            if self.is_center_pt_number(elem):
                pt_number_center_inds = pt_number_center_inds + [ind]
            try:
                int(elem)
            except:
                if elem not in date_replacements:
                    end_date_found = False
                    if start_dates_count > 0:
                        # Problem here when looking at index 1527. start_dates_count is wrong
                        start_dates_counts = start_dates_counts + [start_dates_count - 1]
                        end_of_dates_inds = end_of_dates_inds + [ind]
                        assert(len(start_dates_counts) == len(end_date_inds) == len(end_of_dates_inds))
                        start_dates_count = 0
                    continue
            # Logically if you are here elem is an integer or in date_replacements
            if not end_date_found and len(elem) >= 6:
                end_date_inds = end_date_inds + [ind]
                end_date_found = True
                start_dates_count = 1
            else:
                if end_date_found and (len(elem) >= 6 or elem in date_replacements):
                    start_dates_count = start_dates_count + 1

        # Check to make sure that your start_date_count accounts for missing dates
        # 1. times where end_date ends up with more dates than available start_dates
        # 2. times where both start and end dates are just flat missing - check in the boundary dict #todo: still need to implement
        start_dates_counts_actual = start_dates_counts[:]
        for ind in range(len(end_date_inds)):
            if (len(my_data[end_date_inds[ind]]) / 6) > start_dates_counts[ind]:
                start_dates_counts_actual[ind] = (len(my_data[end_date_inds[ind]]) / 6)
            assert ((len(my_data[end_date_inds[ind]]) / 6) <= start_dates_counts_actual[ind])

        col_names = ['pt_number_center', 'drug', 'start_date', 'end_date', 'dose', 'dosing', 'reason', 'conclusion']
        rows = [col_names]
        problem_rows = []
        pt_number_center_inds_ind = 0
        # add drug, end_date, start_dates, doses, reasons and conclusion columns first
        for ind in range(len(end_date_inds)):
            problem_row = False
            start_ind = end_date_inds[ind]
            end_date_ind = end_date_inds[ind]
            if pt_number_center_inds_ind < len(pt_number_center_inds)-1:
                if end_date_ind > pt_number_center_inds[pt_number_center_inds_ind]\
                        and end_date_ind < pt_number_center_inds[pt_number_center_inds_ind+1]:
                    pt_number_center = my_data[pt_number_center_inds[pt_number_center_inds_ind]]
                else:
                    pt_number_center_inds_ind = pt_number_center_inds_ind + 1
                    if pt_number_center_inds_ind < len(pt_number_center_inds) - 1:
                        if(end_date_ind > pt_number_center_inds[pt_number_center_inds_ind]\
                            and end_date_ind < pt_number_center_inds[pt_number_center_inds_ind+1]):
                            pt_number_center = my_data[pt_number_center_inds[pt_number_center_inds_ind]]
                    else:
                        assert (pt_number_center_inds_ind == len(pt_number_center_inds) - 1)
            else:
                assert(pt_number_center_inds_ind == len(pt_number_center_inds)-1)

            # Note we count missing start_dates as well
            # todo: which one
            start_date_count = start_dates_counts[ind]
            #start_date_count = start_dates_counts_actual[ind]
            # Find the first drug for this set
            end_date = my_data[start_ind]
            if start_ind in problem_inds:
                problem_row = True
            for i in range(1, start_date_count + 1):
                drug_ref_inds = list(reversed(range(1, start_date_count + 1)))
                drug_ref_ind = drug_ref_inds[i-1]
                drug = my_data[end_date_ind - drug_ref_ind]
                # start_ind is where the end_date for this row is
                start_ind = end_date_ind + i
                row = []
                #entered_reason = False  or entered_reason
                # start_ind_reason gives us the ind just before where we start after the boundary for this row,
                # NOT the actual boundary though it of course will be the boundary in the first row for this set

                # 2. times where both start and end dates are just flat missing
                # - more elements than needed to get to boundary #todo: still need to implement
                start_ind_reason = start_ind + (start_date_count * 3)
                missing_end_and_start_date = False
                if i == 1 and my_data[start_ind_reason] != '__Dosage_Reason__' and \
                                '__Dosage_Reason__' not in my_data[start_ind:start_ind_reason]:
                    missing_end_and_start_date = True
                    inds_to_boundary = 0
                    flag = start_ind_reason + 1
                    while flag < len(my_data):
                        if my_data[flag] == '__Dosage_Reason__':
                            inds_to_boundary = flag - start_ind_reason
                            break
                        else:
                            flag = flag + 1

                assert(len(range(start_ind, start_ind + (start_date_count * 3), start_date_count)) == 3)
                for j in range(start_ind, start_ind + (start_date_count * 3), start_date_count):
                    if my_data[j] == '__Dosage_Reason__' or '__Dosage_Reason__' in my_data[j-start_date_count:j]:
                        if my_data[j] == '__Dosage_Reason__':
                            start_ind_reason = j
                        else:
                            # Find out if you passed the boundary
                            itemindex = my_data[j-start_date_count:j].index('__Dosage_Reason__')
                            start_ind_reason = j-start_date_count+itemindex
                            assert(my_data[start_ind_reason] == '__Dosage_Reason__')
                        #entered_reason = True
                        row = row + ['Missing']
                        problem_row = True
                    else:
                        row = row + [my_data[j]]

                if missing_end_and_start_date:
                    start_ind_reason = start_ind_reason + inds_to_boundary
                # i ranges from 0 to the number of start_dates (incl. missing)
                # todo: fgure out if start_ind_reason - i + 1 or start_ind_reason + i - 1 makes more sense
                if my_data[start_ind_reason - i + 1] != '__Dosage_Reason__':
                    # the boundary has to be behind us in this case
                    if '__Dosage_Reason__' not in my_data[start_ind_reason + i - (start_date_count * 3):start_ind_reason + i]:
                        problem_rows = problem_rows + [[(len(rows) - 1)]]
                        problem_row = False
                        row = row + ['Too difficult to parse', 'Too difficult to parse']
                        continue
                    assert('__Dosage_Reason__' in my_data[start_ind_reason + i - (start_date_count*3):start_ind_reason + i])
                    itemindex = my_data[start_ind_reason + i - (start_date_count*3):start_ind_reason + i].index('__Dosage_Reason__')
                    start_ind_reason = start_ind_reason + i - (start_date_count*3) + itemindex
                assert(len(range(start_ind_reason + i, (start_ind_reason + i) + (start_date_count * 2), start_date_count)) == 2)
                for j in range(start_ind_reason + i, (start_ind_reason + i) + (start_date_count * 2), start_date_count):
                    if j == start_ind_reason + 1:
                        assert(my_data[j - 1] == '__Dosage_Reason__')
                    row = row + [my_data[j]]
                assert(len([pt_number_center, drug, end_date] + row) == len(col_names))
                if '__Dosage_Reason__' in row:
                    print('')
                #assert('__Dosage_Reason__' not in row)
                rows = rows + [[pt_number_center, drug, end_date] + row]
                if problem_row:
                    problem_rows = problem_rows + [[(len(rows)-1)]]
                    problem_row = False


        # Split the end_dates and add e
        for ind in range(len(rows)):
            if rows[ind][2] == 'start_date':
                continue
            end_dates = textwrap.wrap(rows[ind][2], 6)
            assert([len(x) == 6 for x in end_dates])
            rows[ind].insert(2, end_dates)
            del rows[ind][3]

        # Add only one of split dates to each row
        row_ind = 0
        while row_ind < len(rows):
            if row_ind < 1 or row_ind >= len(rows)-1:
                row_ind = row_ind + 1
                continue
            end_date_total = len(rows[row_ind][2])
            for end_date_no in range(len(rows[row_ind][2])):
                try:
                    rows[row_ind + end_date_no][2] = rows[row_ind + end_date_no][2][end_date_no]
                except:
                    print("WARNING: Unexpected End_Date length on row " + str(row_ind + end_date_no) +
                          " Using first available date here")
                    rows[row_ind + end_date_no][2] = rows[row_ind + end_date_no][2][0]
                    problem_rows = problem_rows + [[row_ind + end_date_no]]
            row_ind = row_ind + end_date_total

        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_csv.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        problems_file_name = fname[:-4]
        problems_file_name = problems_file_name + '_problem_rows.csv'
        with open(problems_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(problem_rows)

        # Display output
        out_f = open(output_file_name, 'r')
        with out_f:
            data = out_f.read()
            self.textEdit.setText(data)
        w = QWidget()
        QMessageBox.information(w, "Conversion Complete", "csv saved to " + output_file_name)
        w = QWidget()
        QMessageBox.information(w, "Conversion Complete", "Problem rows saved to " + problems_file_name)



    def eds_conversion(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                  '/home')
        with open(fname, 'rt') as csvfile:
            lol = list(csv.reader(csvfile, delimiter='\t'))
        lol = [item for sublist in lol for item in sublist]
        # Choose splitting criteria carefully... 2 spaces? 4 spaces?
        my_data = [x.split("  ") for x in lol]
        my_data = [item for sublist in my_data for item in sublist]
        my_data = list(filter(None, my_data))
        # get rid of trailing whitespaces
        for ind in range(len(my_data)):
            my_data[ind] = my_data[ind].strip()

        # Delete all empty elements
        my_data = [val for val in my_data if val != '']

        [end_date_counts, dosage_reason_boundaries, my_data] = self.find_boundaries(my_data)

        header = ['end_date indices in EDS',
                  'end_date counts',
                  'dates identified for this section',
                  'dosage_reason_boundary indices in EDS',
                  'dosage_reason_boundaries']

        [end_date_indices, end_date_count, dates_section] = [list(t) for t in zip(*end_date_counts)]
        [dosage_reason_boundaries_indices, dosage_reason_boundaries] = [list(t) for t in zip(*dosage_reason_boundaries)]
        rows = [header] + list(zip(end_date_indices, end_date_count, dates_section, dosage_reason_boundaries_indices, dosage_reason_boundaries))
        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_foundations.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        eds_mod_file_name = fname[:-4]
        eds_mod_file_name = eds_mod_file_name + '_modified.csv'
        with open(eds_mod_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows([[i] for i in my_data])

        # Display output
        out_f = open(output_file_name, 'r')
        with out_f:
            data = out_f.read()
            self.textEdit.setText(data)
        w = QWidget()
        QMessageBox.information(w, "Foundations saved",
                                "foundations csv saved to "
                                + output_file_name)
        w = QWidget()
        QMessageBox.information(w, "EDS converted to preliminary csv",
                                "Modifed EDS generated. EDS csv saved to "
                                + eds_mod_file_name)

        # clean the boundary and get something to compare dates against
        [dosage_reason_boundaries_cleaned, tacked_on] = zip(*self.clean_dosage_reason_boundary(dosage_reason_boundaries))
        dosage_reason_boundaries_cleaned = list(dosage_reason_boundaries_cleaned)
        tacked_on = list(tacked_on)
        assert(len(dosage_reason_boundaries_cleaned) == len(dates_section))

        date_replacements = ['CON', 'U', 'CONT', 'UNK', 'NAV', 'C', 'CONT.',
                              'CONTINUE', 'CONTINUED', 'CONTINUES','N/A']

        # split dates retrieved and update date counts:
        # [end_date_indices, end_date_count, dates_section]
        # [dosage_reason_boundaries_indices, dosage_reason_boundaries]
        dates_converted = []
        for j in range(len(dates_section)):
            date_converted_row = []
            for i in range(len(dates_section[j])):
                # print(str(i*j) + '/' + str(len(dates_section)*len(dates_section[j])))
                if dates_section[j][i] not in date_replacements and len(dates_section[j][i]) > 6:
                    date_converted = textwrap.wrap(dates_section[j][i], 6)
                    date_converted_row = date_converted_row + date_converted
                else:
                    date_converted = [dates_section[j][i]]
                    date_converted_row = date_converted_row + date_converted
            dates_converted = dates_converted + [date_converted_row]
        new_date_count = [len(x) for x in dates_converted]
        print('Dates retrieved.')
        print('Checking that date count matches boundary lengths')

        #boundary_lengths = [len(x) for x in dosage_reason_boundaries_cleaned]
        # check date lengths and boundary lengths match
        ####
        # for i in range(len(dates_section)):
        #     if((len(dates_converted[i])/2) != boundary_lengths[i] and
        #     not (len(dates_converted[i]) == 1 and boundary_lengths[i] == 1)):
        #         if(tacked_on[i] == []):
        #             assert(False)
        # print('check complete')
        # print('all rows with values in tacked on are suspicious')
        #####
        print('Retrieving drugs and checking for patient IDs...')
        # retrieve the drugs
        drugs_rows = []
        patient_IDs = [[my_data[0]]]
        for segment in zip(end_date_indices, dates_converted):
            if (len(segment[1]) % 2 == 0):
                segment_count = (len(segment[1])/2)
            else:
                # assume one value missing
                segment_count = ((len(segment[1])+1) / 2)
            end_date_ind = segment[0]
            drugs_rows = drugs_rows + my_data[end_date_ind-segment_count:end_date_ind]
            if self.is_center_pt_number(my_data[end_date_ind-segment_count-1]):
                print(my_data[end_date_ind - segment_count - 1])
                patient_IDs = patient_IDs + [my_data[end_date_ind-segment_count-1]]
            else:
                patient_IDs = patient_IDs + [patient_IDs[-1]]
            # drug_row = []
            # for drug in my_data[end_date_ind-segment_count:end_date_ind]:
            #     drug_row = drug_row + [drug]
            # drugs_rows = drugs_rows + [drug_row]
        print('Drugs retrieved')
        assert(len(drugs_rows)==len(dates_converted))
        print('Retrieving Dose and Dosage...')
        # retrieve dose and dosage
        dose_dosage_rows = []
        for segment in zip(end_date_indices, end_date_count, dosage_reason_boundaries_indices):
            # segment_count = (len(segment[1])/2)
            segment_start = segment[0] + segment[1]
            segment_end = segment[2]
            dose_dosage_rows = dose_dosage_rows + [my_data[segment_start:segment_end]]
            # dose_dosage_row = []
            # for dose_dosage in my_data[segment_start:segment_end]:
            #     dose_dosage_row = dose_dosage_row + [dose_dosage]
            # dose_dosage_rows = dose_dosage_rows + [dose_dosage_row]
        print('Dose and Dosage retrieved')
        assert (len(dose_dosage_rows) == len(dates_converted))
        print('Retrieving Reason and Conslusion...')
        # retrieve reason and conclusion
        reason_conclusion_rows = []
        for segment in zip(dosage_reason_boundaries_indices, dates_converted):
            if (len(segment[1]) % 2 == 0):
                segment_count = (len(segment[1])/2)
            else:
                # assume one value missing
                segment_count = ((len(segment[1])+1) / 2)
            segment_start = segment[0]
            # sometimes the boundary is split e.g '3 1', '1' at the start.
            # Offset to get everything to the end of the conclusions
            offset = 0
            flag = True
            i = segment_start
            while(flag):
                candidate = my_data[i].replace(" ", "")
                if not candidate.isdigit():
                 flag = False
                else:
                 offset = offset + 1
                 i = i + 1
            reason_conclusion_rows = reason_conclusion_rows + [my_data[segment_start:segment_start +
                                                                                     (segment_count*2) +
                                                               offset]]
            # reason_conclusion_row = []
            # for reason_conclusion in my_data[segment_start:segment_start + (segment_count*2)]:
            #     reason_conclusion_row = reason_conclusion_row + [reason_conclusion]
            # reason_conclusion_rows = reason_conclusion_rows + [reason_conclusion_row]
        print('Dose and Dosage retrieved')
        print('Collecting data... saving to csv...')
        # save to csv
        header = ['patient IDs',
                  'drugs',
                  'dates',
                  'dose_dosage',
                  'reason_conclusion']
        rows = [header] + zip(patient_IDs, drugs_rows, dates_converted, dose_dosage_rows, reason_conclusion_rows)

        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_preliminary.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # Display output
        out_f = open(output_file_name, 'r')
        with out_f:
            data = out_f.read()
            self.textEdit.setText(data)
        w = QWidget()
        QMessageBox.information(w, "ALMOST THERE",
                                "If this file has everything right then we are very close."
                                + output_file_name)

        # offset = -1
        # flag = True
        # i = segment_start
        # while (flag):
        #     candidate = my_data[i].replace(" ", "")
        #     if not candidate.isdigit():
        #         flag = False
        #     else:
        #         offset = offset + 1
        #         i = i + 1
        reason_conclusion_rows_cleaned = []
        offsets = []
        reason_conclusion_boundaries = []
        for rc_segment in reason_conclusion_rows:
            offset = 0
            for elem in rc_segment:
                if elem.replace(" ", "").isdigit():
                    offset = offset + 1
                else:
                    offsets = offsets + [offset]
                    break
            reason_conclusion_boundary = rc_segment[0:offset]
            reason_conclusion_rows_cleaned = reason_conclusion_rows_cleaned + [rc_segment[offset:]]
            reason_conclusion_boundary = [x.replace(' ', '') for x in reason_conclusion_boundary]
            reason_conclusion_boundary = ''.join(reason_conclusion_boundary)
            reason_conclusion_boundaries = reason_conclusion_boundaries + [reason_conclusion_boundary]

        #reason_conclusion_boundaries = [x[0:offsets[i]] for i, x in enumerate(reason_conclusion_rows)]
        #reason_conclusion_boundaries = [str.split(x) for x in reason_conclusion_boundaries]
        rows = zip(patient_IDs, drugs_rows, dates_converted, dose_dosage_rows, reason_conclusion_rows_cleaned)
        #self.reshape_for_kip(rows_mod, reason_conclusion_boundaries, fname)


        header = ['patient_IDs', 'drug', 'end_date', 'start_date', 'dose', 'dosage', 'reason', 'conclusion', 'problem']
        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_FINAL.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for row_no, row in enumerate(rows):
                for i, drug in enumerate(row[0]):
                    problem = ''
                    patient_ID = row[0]
                    try:
                        end_date = row[2][i]
                    except:
                        problem = problem + ' problem in end date'
                        end_date = 'MISSING'
                    try:
                        start_date = row[2][i+len(row[1])]
                    except:
                        problem = problem + ' problem in start date'
                        start_date = 'MISSING'
                    try:
                        dose = row[3][i]
                    except:
                        problem = problem + ' problem in dose'
                        dose = 'MISSING'
                    try:
                        dosage = row[3][i+len(row[1])]
                    except:
                        problem = problem + ' problem in dosage'
                        dosage = 'MISSING'
                    try:
                        reason = row[4][i]
                    except:
                        problem = problem + ' problem in reason'
                        reason = 'MISSING'
                    try:
                        conclusion = row[4][i+len(row[1])]
                    except:
                        problem = problem + ' problem in conclusion'
                        conclusion = 'MISSING'
                    writer.writerow([patient_ID, drug, end_date, start_date, dose, dosage, reason, conclusion, problem])

        # Display output
        out_f = open(output_file_name, 'r')
        with out_f:
            data = out_f.read()
            self.textEdit.setText(data)
        w = QWidget()
        QMessageBox.information(w, "Conversion Complete",
                                "Final csv saved to "
                                + output_file_name)



    def reshape_for_kip(self, rows, reason_conclusion_boundaries, fname):
        # format recieved by function
        # header = ['drugs',
        #           'dates',
        #           'dose_dosage',
        #           'reason_conclusion'] reason_conclusion has the boundary at the front

        header = ['drug', 'end_date', 'start_date', 'dose', 'dosage', 'reason', 'conclusion', 'problem']
        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_FINAL.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for row_no, row in enumerate(rows):
                for i, drug in enumerate(row[0]):
                    problem = ''
                    try:
                        end_date = row[1][i]
                    except:
                        problem = problem + 'problem in end date'
                        end_date = 'MISSING'
                    try:
                        start_date = row[1][i+len(row[0])]
                    except:
                        problem = problem + 'problem in start date'
                        start_date = 'MISSING'
                    try:
                        dose = row[2][i]
                    except:
                        problem = problem + 'problem in dose'
                        dose = 'MISSING'
                    try:
                        dosage = row[2][i+len(row[0])]
                    except:
                        problem = problem + 'problem in dosage'
                        dosage = 'MISSING'
                    try:
                        reason = row[3]
                    except:
                        problem = problem + 'problem in reason'
                        reason = 'MISSING'
                    try:
                        conclusion = row[3][i+len(row[0])]
                    except:
                        problem = problem + 'problem in conclusion'
                        conclusion = 'MISSING'
                    writer.writerow([drug, end_date, start_date, dose, dosage, reason, conclusion, problem])


        # end_dates = []
        # start_dates = []
        # problem_section = []
        # for row_no, row in enumerate(rows):
        #     date_segment = row[1]
        #     if (len(date_segment) % 2 == 0):
        #         # let's be hyper sure about these dates:
        #         if (len(reason_conclusion_boundaries[row_no]) * 2 != len(date_segment)):
        #             problem_section + problem_section + [(row_no, 'boundary and number of dates do not match')]
        #         end_dates = end_dates + date_segment[0:(len(date_segment)/2)]
        #         start_dates = start_dates + date_segment[(len(date_segment)/2):]
        #     else:
        #         problem_section = problem_section + [(row_no, 'Odd number of dates')]
        #         end_dates = end_dates + date_segment[0:(len(date_segment)/2)]
        #         start_dates = start_dates + date_segment[(len(date_segment)/2):] + ['Missing']
        #
        # drugs = []
        # for row_no, row in enumerate(rows):
        #     drug_segment = row[0]
        #     drugs = drugs + [drug_segment]
        # assert(len(drugs) == len(end_dates))
        #
        # doses = []
        # dosages = []
        # problem_section = []
        # for row_no, row in enumerate(rows):
        #     dd_segment = row[2]
        #     if (len(dd_segment) % 2 == 0):
        #         # let's be hyper sure about these dates:
        #         assert (len(reason_conclusion_boundaries[row_no]) * 2 == len(dd_segment))
        #         doses = doses + dd_segment[0:(len(dd_segment)/2)]
        #         dosages = dosages + dd_segment[(len(dd_segment)/2):]
        #     else:
        #         problem_section = problem_section + [(row_no, 'Missing value(s) in dose or dosage')]
        #         doses = doses + dd_segment[0:(len(dd_segment)/2)]
        #         dosages = dosages + dd_segment[(len(dd_segment)/2):] + ['Missing']
        # assert(len(doses) == len(end_dates))
        # assert(len(dosages) == len(end_dates))
        #
        # reasons = []
        # conclusions = []
        # problem_section = []
        # for row_no, row in enumerate(rows):
        #     rc_segment = row[3]
        #     if (len(rc_segment) % 2 == 0):
        #         # let's be hyper sure about these dates:
        #         assert (len(reason_conclusion_boundaries[row_no]) * 2 == len(rc_segment))
        #         reasons = reasons + rc_segment[0:(len(rc_segment)/2)]
        #         conclusions = conclusions + rc_segment[(len(rc_segment)/2):]
        #     else:
        #         problem_section = problem_section + [(row_no, 'Missing value(s) in reason or conclusion')]
        #         reasons = reasons + rc_segment[0:(len(rc_segment)/2)]
        #         conclusions = conclusions + rc_segment[(len(rc_segment)/2):] + ['Missing']
        # assert(len(reasons) == len(end_dates))
        # assert(len(conclusions) == len(end_dates))
        #
        # return rows

    def clean_dosage_reason_boundary(self, dosage_reason_boundary):
        split_boundary_raw = [str.split(x) for x in dosage_reason_boundary]
        dosage_reason_boundary_cleaned = []
        for raw_boundary in split_boundary_raw:
            single_boundary_cleaned = []
            tacked_on = []
            end_of_boundary_found = False
            for elem in raw_boundary:
                if elem.isdigit() and not end_of_boundary_found:
                    single_boundary_cleaned = single_boundary_cleaned + [elem]
                else:
                    end_of_boundary_found = True
                    tacked_on = tacked_on + [elem]
            dosage_reason_boundary_cleaned = dosage_reason_boundary_cleaned + [(single_boundary_cleaned, tacked_on)]
        return dosage_reason_boundary_cleaned



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
    #closeInput = raw_input("Press ENTER to exit")
    print("Closing...")
    sys.exit(app.exec_())
